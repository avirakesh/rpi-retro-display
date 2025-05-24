###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

from sortedcontainers import SortedDict
from os import path
from setup_exception import SetupException
import copy
import json
import re
import time

_TIME_REGEX = r"(\d\d):(\d\d)"  # pattern for hh:mm


class UserConfig:
    def __init__(self, json_path):
        self._json_path = json_path

    def __enter__(self):
        with open(self._json_path) as json_file:
            json_data = json.load(json_file)
            self._init_applets(json_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # No cleanup needed
        pass

    def _init_applets(self, json_data):
        applets = json_data["applets"]
        brightness = (
            json_data["brightness"]
            if "brightness" in json_data
            else {"source": "schedule", "schedule": []}
        )

        start_time_to_applet = {}
        for applet in applets:
            start_time = applet["start_time"]

            if start_time_to_applet.get(start_time) is not None:
                print("Error: Found two applets with the same start time.")
                print("Start Time:", start_time)
                print(
                    "Applets:",
                    start_time_to_applet[start_time]["name"],
                    "and",
                    applet["name"],
                )
                raise SetupException("Found duplicate applet start times")

            start_time_to_applet[start_time] = applet

        start_time_to_brightness = {}
        if brightness["source"] == "schedule":
            if "schedule" not in brightness:
                raise SetupException(
                    "Brightness source set to schedule but no schedule provided."
                )
            self._should_setup_brightness_api = False
            for entry in brightness["schedule"]:
                start_time = entry["start_time"]
                if start_time_to_brightness.get(start_time) is not None:
                    print(
                        "Error: Found two brightness entries with the same start time."
                    )
                    print("Start Time:", start_time)
                    print(
                        "Values:",
                        start_time_to_brightness[start_time]["value"],
                        "and",
                        entry["value"],
                    )
                    raise SetupException("Found duplicate brightness start times")
                start_time_to_brightness[start_time] = entry
        elif brightness["source"] == "api":
            self._should_setup_brightness_api = True
        else:
            raise SetupException(
                f"Invalid brightness source: {brightness['source']}. "
                f'Must be one of ["schedule", "api"]'
            )

        self._validate_applets(start_time_to_applet)
        self._process_config(start_time_to_applet, start_time_to_brightness)

    def _validate_applets(self, start_time_to_applet):
        # Check that all applets have a valid path.
        for applet in start_time_to_applet.values():
            applet_path = path.abspath(applet["path"])
            if not path.exists(applet_path):
                applet_name = applet["name"]
                raise SetupException(
                    f"Applet path '{applet_path}', for applet '{applet_name}', does not exist."
                )

    def _process_config(self, start_time_to_applet, start_time_to_brightness):
        applets = SortedDict(UserConfig.identity_fn)
        brightness = SortedDict(UserConfig.identity_fn)

        # Setup applet specific information required to render the applet
        for start_time_str, applet in start_time_to_applet.items():
            start_time = UserConfig._parse_and_assert_time(start_time_str)
            applet["start_time"] = start_time

            cmd_args = []
            if "schema_vals" in applet:
                for key, val in applet["schema_vals"].items():
                    if isinstance(val, dict):
                        cmd_args.append(f"{key}={json.dumps(val)}")
                    else:
                        cmd_args.append(f"{key}={val}")

            applet["cmd_args"] = cmd_args

            applets[start_time] = applet

        # If no brightness is provided, all applets have the default brightness.
        if not start_time_to_brightness:
            self._applets = applets
            for start_time, applet in self._applets.items():
                applet["brightness"] = 1.0
            return

        # We have some brightness information.
        brightness = SortedDict(UserConfig.identity_fn)
        for start_time_str, entry in start_time_to_brightness.items():
            start_time = UserConfig._parse_and_assert_time(start_time_str)
            brightness[start_time] = entry["value"]

        start_times = set()
        start_times.update(brightness.keys())
        start_times.update(applets.keys())

        self._applets = SortedDict(UserConfig.identity_fn)
        # Start with the last applet and brightness of the day
        last_applet = applets.peekitem(-1)[1]
        last_brightness = brightness.peekitem(-1)[1]
        for start_time in sorted(start_times):
            if start_time in brightness:
                last_brightness = brightness[start_time]
            if start_time in applets:
                last_applet = applets[start_time]

            last_applet["brightness"] = last_brightness
            last_applet["start_time"] = start_time
            self._applets[start_time] = copy.deepcopy(last_applet)

    def should_setup_brightness_api(self):
        """
        Returns True if the user wants to call a REST API to set the brightness of the display.
        """
        return self._should_setup_brightness_api

    def get_current_applet(self):
        """
        returns (current_applet, next_applet_time)
        returns (current_applet, None) if there is only one applet

        Called by main.py at the start and then again when get_day_time_secs() returns a
        value >= the returned next_applet_time. For simplicity, this function doesn't make assumtions
        based on previous calls.
        """

        # Simple time base automation.
        # Can be updated for more complex automation.
        if len(self._applets) == 1:
            return (self._applets.peekitem(0)[1], None)

        curr_time = UserConfig.get_day_time_secs()
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

    @staticmethod
    def _parse_and_assert_time(time_str):
        match = re.findall(_TIME_REGEX, time_str)
        assert (
            len(match) == 1
        ), f"Invalid time: '{time_str}'. start_time should match the pattern hh:mm"

        hhmm = match[0]
        (hh, mm) = (int(hhmm[0]), int(hhmm[1]))
        assert (
            0 <= hh and 23 >= hh
        ), f"Invalid time: '{time_str}'. {hh} should be between 0 and 23 inclusive"
        assert (
            0 <= mm and 59 >= mm
        ), f"Invalid time: '{time_str}'. {mm} should be between 0 and 59 inclusive"

        return (60 * 60 * hh) + (mm * 60)

    @staticmethod
    def get_day_time_secs():
        """
        returns the time passed in seconds since 00:00:00 hrs (midnight)
        Time resolution is of seconds
        output range: [0, 86340)
        """
        curr_time = time.localtime()
        hh = int(time.strftime("%H", curr_time))
        mm = int(time.strftime("%M", curr_time))
        ss = int(time.strftime("%S", curr_time))
        return (hh * 60 * 60) + (mm * 60) + ss

    @staticmethod
    def identity_fn(x):
        return x
