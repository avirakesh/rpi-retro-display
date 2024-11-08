###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import subprocess
from os import path, symlink, makedirs

_WORKING_DIR_ROOT = ""
_OUTPUT_DIR = path.join(_WORKING_DIR_ROOT, "gifs")

# this path is a workaround for pixlet bug https://github.com/tidbyt/pixlet/issues/1084
_INPUT_DIR = path.join(_WORKING_DIR_ROOT, "input")


class PixletWrapper:
    def __init__(self):
        cmd_out = subprocess.run(["which", "pixlet"])
        if cmd_out.returncode != 0:
            print("Command 'pixlet' not found.")
            print("Make sure 'pixlet' binary is in PATH.")
            exit(1)

        cmd_out = subprocess.run(["which", "md5sum"])
        if cmd_out.returncode != 0:
            print("Command 'md5sum' not found.")
            print("Make sure 'md5sum' binary is in PATH.")
            exit(1)

    def __enter__(self):
        cmd_out = subprocess.run(["mkdir", "-p", _OUTPUT_DIR])
        if cmd_out.returncode != 0:
            print("Failed to create output 'gifs' directory:", _OUTPUT_DIR)
            exit(1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Cleaning up {_OUTPUT_DIR}")
        rm = subprocess.run(["rm", "-rf", _OUTPUT_DIR])
        if rm.returncode != 0:
            print("Failed to remove", _OUTPUT_DIR)
        else:
            print("Deleted dir:", _OUTPUT_DIR)

        print(f"Cleaning up {_INPUT_DIR}")
        rm = subprocess.run(["rm", "-rf", _INPUT_DIR])
        if rm.returncode != 0:
            print("Failed to remove", _INPUT_DIR)
        else:
            print("Deleted dir:", _INPUT_DIR)

    def create_gif_from_sketch(self, applet):
        """
        returns (path_to_gif, md5 checksum of gif)
        """
        applet_path = path.abspath(applet["path"])
        applet_file = applet_path.split("/")[-1]
        applet_name = applet_file.split(".")[0]

        # To workaround the pixlet bug, each applet should be it it's own directory
        # with no siblings.
        # Simply symlink the applet to its own directory in _INPUT_DIR
        input_dir = path.join(_INPUT_DIR, applet_file)
        input_path = path.join(input_dir, applet_file)

        if not path.isfile(input_path):
            print(
                f"{input_path} does not exist. Symlinking {applet_path} to {input_path}"
            )
            makedirs(input_dir, exist_ok=True)
            symlink(applet_path, input_path)

        output_name = applet_name + ".gif"
        output_path = _OUTPUT_DIR + "/" + output_name

        rm = subprocess.run(["rm", "-rf", output_path])
        if rm.returncode != 0:
            print("Failed to remove previous gif:", output_path)
            return (None, None)

        cmd = ["pixlet", "render", "--gif", "--output", output_path, input_path]
        cmd.extend(applet["cmd_args"])
        pixlet_out = subprocess.run(cmd)
        if pixlet_out.returncode != 0:
            print("Failed to create gif from applet:", input_path)
            return (None, None)

        md5_proc = subprocess.run(["md5sum", output_path], capture_output=True)
        if md5_proc.returncode != 0:
            print("Successfully created gif but failed to generate hash.")
            return (output_path, None)

        # expecting output of type: "<some_hash> <file_name>\n"
        md5_output = md5_proc.stdout.decode()
        md5_hash = md5_output.split(" ")[0]

        return (output_path, md5_hash)
