import time
from pixlet_wrapper import PixletWrapper
from display_controller import DisplayControllerDelegator

_MS_TO_S = 0.001
JSON_PATH = "config.json"

def main():
    # pixlet_wrapper = PixletWrapper()
    # print(pixlet_wrapper.create_gif_from_sketch("applets/hello_world.star"))
    # pixlet_wrapper.clean_up()

    with DisplayControllerDelegator() as display_controller, PixletWrapper(JSON_PATH) as pixlet_wrapper:
        applet = pixlet_wrapper.get_current_applet()
        print("Displaying Applet", applet["name"])

        try:
            while True:
                gif_path = pixlet_wrapper.create_gif_from_sketch(applet["path"])
                display_controller.queue_gif_to_display(gif_path)

                if not applet["dynamic"]:
                    time.sleep(5) # refresh every 5 seconds for non-dynamic display
                    continue

                update_time = time.perf_counter() + applet["refresh_interval_ms"]
                while time.perf_counter() > update_time:
                    time.sleep(update_time - time.perf_counter())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    main()