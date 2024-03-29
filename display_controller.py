###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

from collections import deque
from dataclasses import dataclass
from multiprocessing import Process, Queue, Value
from PIL import Image, ImageEnhance
from rgbmatrix import FrameCanvas, RGBMatrix, RGBMatrixOptions
import numpy as np
import queue
import time

_DISPLAY_SIZE = (32, 64, 3) # 32 rows, 64 columns, 3 colors for each pixel
_DEFAULT_DISPLAY_TIME = 1 # default time to wait for next frame, in seconds
_MS_TO_S = 0.001

@dataclass
class Frame:
    img: Image # Should be of size _DISPLAY_SIZE
    duration: float = _DEFAULT_DISPLAY_TIME # time (in s) how long the frame should be on display.
    should_loop: bool  = False # true if the frames should loop
    loop_count: int = 0 # number of times the frames should loop
                        # 0 for infinite
    drawn_at: float = 0.0 # used and filled by DisplayController.
                          # Time (in s) at which the frame was drawn



class DisplayController:
    def __init__(self, should_exit, scene_queue):
        # multiprocessing.Value [boolean] object.
        # Used to check if the process should terminate.
        # The value will the changed by DisplayControllerDelegator when the program
        # is about to quit.
        self._should_exit = should_exit

        # muliprocessing.Queue object to pull new scenes from.
        # This will be populated by DisplayControllerDelegator
        # One scene consists of a list of Frames to display.
        self._scene_queue = scene_queue


    def run(self):
        print("Running DisplayController process.")

        self._init_process()

        while(self._should_exit.value == 0):
            self._process_frame()


    def _init_process(self):
        # Set up RGB Matrix
        options = RGBMatrixOptions()
        options.rows = _DISPLAY_SIZE[0]
        options.cols = _DISPLAY_SIZE[1]
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = "adafruit-hat-pwm"
        options.led_rgb_sequence = "RBG"
        options.gpio_slowdown = 2

        self._rgb_matrix = RGBMatrix(options=options)


        # Queue of Frames that need to be drawn.
        # The first frame is the frame currently on screen.
        self._frames_queue = deque()

        # seed frames queue with white frame followed by a black frame
        # this forces the black frame to be drawn immediately upon start
        white_img = Image.new("RGB", (_DISPLAY_SIZE[1], _DISPLAY_SIZE[0]), (255, 255, 255))
        white_canvas = self._rgb_matrix.CreateFrameCanvas()
        white_canvas.SetImage(white_img)
        self.canvas = self._rgb_matrix.SwapOnVSync(white_canvas)

        # Pretend this frame has already expired
        white_frame_drawn_at = time.perf_counter() - (2*_DEFAULT_DISPLAY_TIME)
        white_frame = Frame(img=white_img, drawn_at=white_frame_drawn_at)

        black_img = Image.new("RGB", (_DISPLAY_SIZE[1], _DISPLAY_SIZE[0]), (0, 0, 0))
        black_frame = Frame(img=black_img)


        self._frames_queue.append(white_frame)
        self._frames_queue.append(black_frame)



    def _process_frame(self):
        curr_frame = self._frames_queue[0]

        # time (in s) when the current frame expires
        curr_expiry = curr_frame.drawn_at + curr_frame.duration
        if curr_expiry <= time.perf_counter():
            # print("Current frame expired, drawing next frame")
            self._draw_next_frame()
            return

        try:
            # Wait for next scene to come in for as long
            # as the current frame lasts.

            # drop the refresh rate if there is only one frame to display
            curr_frame_duration = _DEFAULT_DISPLAY_TIME \
                                    if len(self._frames_queue) == 1 \
                                        else curr_frame.duration
            curr_expiry = curr_frame.drawn_at + curr_frame_duration

            # We don't want timeout to be negative or 0.
            # 0 blocks indefinitely, negative wait is undefined.
            # Wait at least 1ms instead.
            timeout = max(0.001, curr_expiry - time.perf_counter())

            scene = self._scene_queue.get(block=True, timeout=timeout)
            # print("Received new scene")
            self._queue_raw_frames(scene)
            self._draw_next_frame()
        except queue.Empty:
            # print("Empty raw frames queue, do nothing.")
            pass


    def _queue_raw_frames(self, scene):
        temp_frames = deque()

        for frame in scene:
            if np.shape(frame.img) != _DISPLAY_SIZE:
                print("Invalid frame shape. Skipping")
                print("Expected:",_DISPLAY_SIZE, "Received:", np.shape(frame.img))
                continue

            frame.drawn_at = 0.0
            temp_frames.append(frame)

        if len(temp_frames) == 0:
            # Don't do anything if we don't have new frames
            return

        last_frame = self._frames_queue.popleft()
        # Set up last frame to be immediately popped in the next cycle
        last_frame.should_loop = False
        last_frame.duration = 0
        last_frame.drawn_at = time.perf_counter()

        self._frames_queue.clear()
        self._frames_queue.append(last_frame) # re-insert last frame
        self._frames_queue.extend(temp_frames) # add new frames to queue, will be drawn


    def _draw_next_frame(self):
        if len(self._frames_queue) == 1:
            # print("Last frame in queue, redrawing last frame")
            self._frames_queue[0].drawn_at = time.perf_counter()
            return

        curr_frame = self._frames_queue[0]
        curr_time = time.perf_counter()
        curr_expiry = curr_frame.drawn_at + curr_frame.duration
        if (curr_expiry > curr_time):
            # print("Current frame has not expired yet")
            return

        curr_frame = self._frames_queue.popleft()
        self.canvas.SetImage(self._frames_queue[0].img)
        self.canvas = self._rgb_matrix.SwapOnVSync(self.canvas)
        self._frames_queue[0].drawn_at = time.perf_counter()

        if not curr_frame.should_loop:
            return

        if curr_frame.loop_count == 1:
            # Stop looping this frame if this was the last iteration of the loop
            curr_frame.should_loop = False
        elif curr_frame.loop_count > 0:
            curr_frame.loop_count -= 1

        # add frame to the back of the queue
        curr_frame.drawn_at = 0.0
        self._frames_queue.append(curr_frame)


class DisplayControllerDelegator:
    def __init__(self):
        self._should_exit = Value('b', 0, lock=False)
        self._scene_queue = Queue()
        self._current_scene_metadata = {
            "hash": None,
            "brightness": None
        }

        self._display_controller = DisplayController(self._should_exit, self._scene_queue)


    def __enter__(self):
        self._frame_writer_process = Process(target=DisplayController.run, args=[self._display_controller])
        self._frame_writer_process.start()
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        self._should_exit.value = True
        self._frame_writer_process.join()
        self._scene_queue.close()


    def queue_gif_to_display(self, gif_filepath, gif_hash, brightness):
        if not self._update_scene_metadata_if_needed(gif_hash, brightness):
            # The new gif has the same metadata as what is already displayed.
            # No need to queue this gif
            return


        frames = []
        with Image.open(gif_filepath) as im:
            im_info = im.info
            should_loop = False
            loop_count = 0
            frame_duration = _DEFAULT_DISPLAY_TIME

            if "loop" in im_info:
                should_loop = True
                loop_count = im_info["loop"]

            if "duration" in im_info:
                frame_duration = im_info["duration"] * _MS_TO_S


            frame_number = 0
            try:
                while True:
                    im.seek(frame_number)
                    frame_number += 1

                    if brightness != 1:
                        # temporary format to allow brightness changes
                        tmp_im = im.convert("RGBA")
                        img = ImageEnhance.Brightness(tmp_im).enhance(brightness)
                    else:
                        img = im

                    rgb_img = img.convert("RGB")

                    frame = Frame(img=rgb_img,
                                  should_loop=should_loop,
                                  duration=frame_duration,
                                  loop_count=loop_count)

                    frames.append(frame)

            except EOFError:
                # Finished processing all gif frames
                pass

        self._scene_queue.put(frames)


    def _update_scene_metadata_if_needed(self, gif_hash, brightness):
        """
        returns True if metadata was updated, False instead
        """
        curr_hash = self._current_scene_metadata["hash"]
        curr_brightness = self._current_scene_metadata["brightness"]

        self._current_scene_metadata["hash"] = gif_hash
        self._current_scene_metadata["brightness"] = brightness

        # return true if the current hash is None (can't detect if old and new gifs are same)
        #             or if the hash has changed
        #             or if the brightness has changed
        return curr_hash is None \
                or curr_hash != gif_hash \
                    or curr_brightness != brightness
