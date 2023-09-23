###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import time

from display_controller import DisplayControllerDelegator
from numpy import exp
from pixlet_wrapper import PixletWrapper

_SECS_IN_AN_HOUR = 60 * 60
_SECS_IN_A_DAY = 24 * _SECS_IN_AN_HOUR
_MS_TO_S = 0.001
JSON_PATH = "config.json"

def main():
    with DisplayControllerDelegator() as display_controller, \
         PixletWrapper(JSON_PATH) as pixlet_wrapper:

        # start by forcing a render of the applet
        (curr_applet, next_applet_time) = pixlet_wrapper.get_current_applet()
        print(f"Displaying Applet: {curr_applet['name']}")
        curr_render_time = _render_applet_if_needed(pixlet_wrapper, display_controller, curr_applet)

        # main program loop
        try:
            while True:
                if _should_update_applet(curr_applet, next_applet_time):
                    (curr_applet, next_applet_time) = pixlet_wrapper.get_current_applet()
                    # Force render the new applet
                    print(f"Displaying Applet: {curr_applet['name']}")
                    curr_render_time = _render_applet_if_needed(pixlet_wrapper,
                                                                display_controller,
                                                                curr_applet)
                elif curr_applet["dynamic"]:
                    curr_render_time = _render_applet_if_needed(pixlet_wrapper,
                                                                display_controller,
                                                                curr_applet,
                                                                curr_render_time)

                wakeup_time = _get_wake_up_time(curr_applet, curr_render_time, next_applet_time)
                while time.perf_counter() < wakeup_time:
                    time.sleep(wakeup_time - time.perf_counter())
        except KeyboardInterrupt:
            pass


# returns True if the thread should ask PixletWrapper for a new applet, False otherwise
def _should_update_applet(curr_applet, next_applet_time):
    if next_applet_time is None:
        # Never update applet
        return False

    curr_applet_time = curr_applet["start_time"]
    curr_time = PixletWrapper.get_day_time_secs()

    # Simple case: next applet is scheduled for sometime today
    if curr_applet_time < next_applet_time :
         return curr_time >= next_applet_time

    # Weird case: Last applet of the day is currently displayed

    # We're still in the same day
    # Do not update applet as this is the last applet of the day
    if curr_time >= curr_applet_time:
        return False

    # It is the next day!
    # Update applet if curr_time is past next_applet_time
    return curr_time >= next_applet_time


# Returns the time at which this thread should wake up. This could be to update the applet, to
# re-render the applet, or just to keep the OS from deprioritizing the script.
# This is calculated as minimum of time for curr_applet to update and time at which the current
# applet expires.
def _get_wake_up_time(curr_applet, curr_applet_render_time, next_applet_day_time):
    curr_time = time.perf_counter()
    curr_day_time = PixletWrapper.get_day_time_secs()

    # figure out time after which the applet should be updated
    if next_applet_day_time is None:
        # No next applet, default to an hour
        time_to_next_applet = _SECS_IN_AN_HOUR
    elif curr_day_time > next_applet_day_time:
        # next_applet_time is the next day
        # Wait all of today + until next applet has to come up
        time_to_next_applet = (_SECS_IN_A_DAY - curr_day_time) + next_applet_day_time
    else:
        # next_applet_time is on the same day
        time_to_next_applet = next_applet_day_time - curr_day_time


    if not curr_applet["dynamic"]:
        # Static applet, default to an hour
        time_to_curr_applet = _SECS_IN_AN_HOUR
    else:
        curr_applet_render_time = curr_time if curr_applet_render_time is None else curr_applet_render_time
        curr_applet_expiry = curr_applet_render_time + (curr_applet["refresh_interval_ms"] * _MS_TO_S)
        time_to_curr_applet = curr_applet_expiry - curr_time

    return curr_time + min(time_to_next_applet, time_to_curr_applet, _SECS_IN_AN_HOUR)


# Queues passed applet to display_controller
# current_render_time = None forces the applet to be queued
# return the time at which the applet was queued to render
def _render_applet_if_needed(pixlet_wrapper, display_controller, applet, curr_render_time=None):
    if curr_render_time is None:
        # Force expired
        expired = True
    else:
        expiry = curr_render_time + (applet["refresh_interval_ms"] * _MS_TO_S)
        expired = time.perf_counter() >= expiry

    if not expired:
        # return early if the applet has not expired yet
        return curr_render_time

    (gif_path, gif_hash) = pixlet_wrapper.create_gif_from_sketch(applet)
    if gif_path is not None:
        display_controller.queue_gif_to_display(gif_path, gif_hash, applet["brightness"])
    else:
        print(f"Error creating gif for '{applet['name']}'")
        # didn't render, don't update render time
        return curr_render_time

    return time.perf_counter()

if __name__ == "__main__":
    main()
