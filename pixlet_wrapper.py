###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import subprocess
import json

_OUTPUT_DIR = "gifs"


class PixletWrapper:
    def __init__(self, json_path):
        self._json_path = json_path
        cmd_out = subprocess.run(["which", "pixlet"])
        if (cmd_out.returncode != 0):
            print("Command 'pixlet' not found.")
            print("Make sure 'pixlet' binary is in path.")
            exit(1)

        cmd_out = subprocess.run(["mkdir", "-p", _OUTPUT_DIR])
        if (cmd_out.returncode != 0):
            print("Failed to create output 'gifs' directory")
            exit(1)

    def __enter__(self):
        with open(self._json_path) as json_file:
            json_data = json.load(json_file)
            self._applets = json_data["applets"]

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        rm = subprocess.run(["rm", "-rf", _OUTPUT_DIR])
        if (rm.returncode != 0):
            print("Failed to remove", _OUTPUT_DIR)
        else:
            print("Deleted dir:", _OUTPUT_DIR)

    def create_gif_from_sketch(self, applet_path):
        applet_name = applet_path.split("/")[-1]
        applet_name = applet_name.split(".")[0]

        output_name = applet_name + ".gif"
        output_path = _OUTPUT_DIR + "/" + output_name

        rm = subprocess.run(["rm", "-rf", output_path])
        if (rm.returncode != 0):
            print("Failed to remove previous gif:", output_path)
            return None

        pixlet_out = subprocess.run(["pixlet", "render", "--gif", "--output", output_path, applet_path])
        if (pixlet_out.returncode != 0):
            print("Failed to create gif from applet:", applet_path)
            return None

        return output_path

    def get_current_applet(self):
        # TODO: Add applet automation through config
        # Just assume the first config is the active one for now.
        return self._applets[0]
