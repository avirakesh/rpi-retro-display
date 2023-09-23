###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import math
from sortedcontainers import SortedDict
import json
import re
import subprocess
import time

_OUTPUT_ROOT = "" # path where the output gifs should be placed. Should end with "/"
_OUTPUT_DIR = _OUTPUT_ROOT + "gifs"
_TIME_REGEX = r"(\d\d):(\d\d)" # pattern for hh:mm


class PixletWrapper:
    def __init__(self, json_path):
        self._json_path = json_path
        cmd_out = subprocess.run(["which", "pixlet"])
        if (cmd_out.returncode != 0):
            print("Command 'pixlet' not found.")
            print("Make sure 'pixlet' binary is in PATH.")
            exit(1)

        cmd_out = subprocess.run(["mkdir", "-p", _OUTPUT_DIR])
        if (cmd_out.returncode != 0):
            print("Failed to create output 'gifs' directory")
            exit(1)

        cmd_out = subprocess.run(["which", "md5sum"])
        if (cmd_out.returncode != 0):
            print("Command 'md5sum' not found.")
            print("Make sure 'md5sum' binary is in PATH.")
            exit(1)


    def __enter__(self):
        with open(self._json_path) as json_file:
            json_data = json.load(json_file)
            self._init_applets(json_data["applets"])
            self._raw_applets = json_data["applets"]

        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        rm = subprocess.run(["rm", "-rf", _OUTPUT_DIR])
        if (rm.returncode != 0):
            print("Failed to remove", _OUTPUT_DIR)
        else:
            print("Deleted dir:", _OUTPUT_DIR)


    # returns (path_to_gif, md5 checksum of gif)
    def create_gif_from_sketch(self, applet):
        applet_path = applet["path"]
        applet_name = applet_path.split("/")[-1]
        applet_name = applet_name.split(".")[0]

        output_name = applet_name + ".gif"
        output_path = _OUTPUT_DIR + "/" + output_name

        rm = subprocess.run(["rm", "-rf", output_path])
        if (rm.returncode != 0):
            print("Failed to remove previous gif:", output_path)
            return (None, None)

        cmd = ["pixlet", "render", "--gif", "--output", output_path, applet_path]
        cmd.extend(applet["cmd_args"])
        pixlet_out = subprocess.run(cmd)
        if (pixlet_out.returncode != 0):
            print("Failed to create gif from applet:", applet_path)
            return (None, None)

        md5_proc = subprocess.run(["md5sum", output_path], capture_output=True)
        if md5_proc.returncode != 0:
            print("Successfully created gif but failed to generate hash.")
            return (output_path, None)

        # expecting output of type: "<some_hash> <file_name>\n"
        md5_output = md5_proc.stdout.decode()
        md5_hash = md5_output.split(" ")[0]

        return (output_path, md5_hash)


    # returns (current_applet, next_applet_time)
    # returns (current_applet, None) if there is only one applet
    #
    # Called by main.py at the start and then again when get_day_time_secs() returns a
    # value >= the returned next_applet_time. For simplicity, this function doesn't make assumtions
    # based on previous calls.
    def get_current_applet(self):
        # Simple time base automation.
        # Can be updated for more complex automation.

        if len(self._applets) == 1:
            return (self._applets.peekitem(0)[1], None)

        curr_time = PixletWrapper.get_day_time_secs()
        curr_applet_idx = self._get_current_applet_idx(curr_time)
        next_applet_idx = (curr_applet_idx + 1) % len(self._applets)

        curr_applet = self._applets.peekitem(curr_applet_idx)[1]
        next_applet_time = self._applets.peekitem(next_applet_idx)[0]


        return (curr_applet, next_applet_time)


    def _get_current_applet_idx(self, curr_time):
        curr_idx = self._applets.bisect_key_left(curr_time)

        if curr_idx == len(self._applets):
            return -1


        if self._applets.peekitem(curr_idx)[0] == curr_time:
            return curr_idx

        return curr_idx - 1


    def _init_applets(self, applets):
        start_time_to_applet = {}
        for applet in applets:
            start_time = applet["start_time"]

            if start_time_to_applet.get(start_time) is not None:
                print("Error: Found two applets with the same start time.")
                print("Start Time:", start_time)
                print("Applets:", start_time_to_applet[start_time]["name"], "and", applet["name"])
                exit(1)

            start_time_to_applet[start_time] = applet

        self._setup_applets(start_time_to_applet)


    def _setup_applets(self, start_time_to_applet):
        self._applets = SortedDict(PixletWrapper.identity_fn)

        for start_time_str, applet in start_time_to_applet.items():
            applet["brightness"] = applet["brightness"] if "brightness" in applet else 1
            applet["brightness"] = max(applet["brightness"], 0.0)

            start_time = PixletWrapper._parse_and_assert_time(start_time_str)
            applet["start_time"] = start_time

            cmd_args = []
            if "schema_vals" in applet:
                for key, val in applet["schema_vals"].items():
                    if isinstance(val, dict):
                        cmd_args.append(f"{key}={json.dumps(val)}")
                    else:
                        cmd_args.append(f"{key}={val}")
            print(cmd_args)
            applet["cmd_args"] = cmd_args

            self._applets[start_time] = applet


    @staticmethod
    def _parse_and_assert_time(time_str):
        match = re.findall(_TIME_REGEX, time_str)
        assert len(match) == 1, \
               f"Invalid time: '{time_str}'. start_time should match the pattern hh:mm"

        hhmm = match[0]
        (hh, mm) = (int(hhmm[0]), int(hhmm[1]))
        assert 0 <= hh and 23 >= hh, \
               f"Invalid time: '{time_str}'. {hh} should be between 0 and 23 inclusive"
        assert 0 <= mm and 59 >= mm, \
               f"Invalid time: '{time_str}'. {mm} should be between 0 and 59 inclusive"

        return (60 * 60 * hh) + (mm * 60)



    # returns the time passed in seconds since 00:00:00 hrs (midnight)
    # Time resolution is of seconds
    # output range: [0, 86340)
    @staticmethod
    def get_day_time_secs():
        hh = int(time.strftime("%H"))
        mm = int(time.strftime("%M"))
        ss = int(time.strftime("%S"))
        return (hh * 60 * 60) + (mm * 60) + ss


    @staticmethod
    def identity_fn(x):
        return x
