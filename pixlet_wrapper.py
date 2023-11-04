###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import subprocess

_OUTPUT_ROOT = "" # path where the output gifs should be placed. Should end with "/"
_OUTPUT_DIR = _OUTPUT_ROOT + "gifs"


class PixletWrapper:
    def __init__(self):
        cmd_out = subprocess.run(["which", "pixlet"])
        if (cmd_out.returncode != 0):
            print("Command 'pixlet' not found.")
            print("Make sure 'pixlet' binary is in PATH.")
            exit(1)

        cmd_out = subprocess.run(["which", "md5sum"])
        if (cmd_out.returncode != 0):
            print("Command 'md5sum' not found.")
            print("Make sure 'md5sum' binary is in PATH.")
            exit(1)


    def __enter__(self):
        cmd_out = subprocess.run(["mkdir", "-p", _OUTPUT_DIR])
        if (cmd_out.returncode != 0):
            print("Failed to create output 'gifs' directory:", _OUTPUT_DIR)
            exit(1)
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
