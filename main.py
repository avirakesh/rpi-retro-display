###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import time
from pixlet_wrapper import PixletWrapper
from display_controller import DisplayControllerDelegator

_MS_TO_S = 0.001
JSON_PATH = "config.json"

def main():
    with DisplayControllerDelegator() as display_controller, PixletWrapper(JSON_PATH) as pixlet_wrapper:
        applet = pixlet_wrapper.get_current_applet()
        print("Displaying Applet", applet["name"])

        gif_path = pixlet_wrapper.create_gif_from_sketch(applet["path"])
        display_controller.queue_gif_to_display(gif_path)

        try:
            while True:
                if not applet["dynamic"]:
                    time.sleep(60) # refresh every 60 seconds for non-dynamic display
                    continue

                gif_path = pixlet_wrapper.create_gif_from_sketch(applet["path"])
                display_controller.queue_gif_to_display(gif_path)

                update_time = time.perf_counter() + applet["refresh_interval_ms"]
                while time.perf_counter() > update_time:
                    time.sleep(update_time - time.perf_counter())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()
