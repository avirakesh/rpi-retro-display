import numpy as np
import time

if __name__ == "__main__":
    old_frame = np.zeros([32, 64, 3], dtype=np.int16)
    new_frame = np.ones([32, 64, 3], dtype=np.int16) * 255

    start = time.time_ns()
    mask = new_frame != old_frame
    mask = np.any(mask, 2)
    end = time.time_ns()

    print("clock time: %d ns" % (end - start))
    print(mask)
    print("mask size: ", np.shape(mask))

