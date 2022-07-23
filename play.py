###############################################################################
# "THE BEER-WARE LICENSE" (Revision 42):
# Avichal Rakesh wrote this file. As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
###############################################################################

import time
import sys
from getch import getche
from rgbmatrix import RGBMatrix, RGBMatrixOptions

## Simple script to check if the diplay is working or not.

ROWS = 32
COLS = 64

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = ROWS
options.cols = COLS
options.chain_length = 1
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'

matrix = RGBMatrix(options = options)

print("Press x to stop.")

prev_pos = [0, 0]
pos = [0, 0]

color = [255, 255, 255]

while True:
    input = getche()
    print()
    if input == "x":
        break

    if input == "w":
        pos[0] = (pos[0] - 1) % ROWS
    elif input == "s":
        pos[0] = (pos[0] + 1) % ROWS
    elif input == "a":
        pos[1] = (pos[1] - 1) % COLS
    elif input == "d":
        pos[1] = (pos[1] + 1) % COLS
    elif input == "r":
        color[0] = 255 if color[0] == 0 else 0
    elif input == "g":
        color[1] = 255 if color[1] == 0 else 0
    elif input == "b":
        color[2] = 255 if color[2] == 0 else 0
    elif input == "i":
        color = [255, 255, 255]
    elif input == "c":
        matrix.Fill(0, 0, 0)
        pos = [0, 0]
        color = [0, 0, 0]

    matrix.SetPixel(pos[1], pos[0], color[0], color[1], color[2])

    prev_pos = pos
