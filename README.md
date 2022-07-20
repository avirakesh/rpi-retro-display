# rpi-retro-display

A Simple program to create a [TidByt&copy;](https://tidbyt.com/) like retro display using a
Raspberry Pi and a 32x64 LED Matrix.


## Disclaimer

This project is **not** affiliated or endorsed by [TidByt Inc](https://tidbyt.com/). This is one
person's attempt to use the excellent [Pixlet SDK](https://github.com/tidbyt/pixlet) to create
a TidByt&copy; clone.

## Setting Things Up

**NOTE:** I used Raspberry Pi 3B for the project. Raspberry Pi 4 is probably safe to use, but
YMMV with other models.

### 1. Setting up the Display

I used an [Adafruit Display](https://www.adafruit.com/product/5036) with an
[Adafruit's RPi HAT](https://www.adafruit.com/product/2345)

The RPi HAT has a comprehensive
[tutorial](https://learn.adafruit.com/adafruit-rgb-matrix-plus-real-time-clock-hat-for-raspberry-pi)
that installs a python library to control the display. The tutorial installs python bindings from
[rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) which this project uses.

_Make sure you can run the python samples from the tutorial before proceeding._

### 2. Setting Up Raspberry Pi

0. Install Pre-requisites
    There are two main pre-requisites for the project
    - Python
        ```console
        $ python --version
        Python 3.9.2
        ```

        Python versions >= 3.9 should work!
    - `md5sum`
        ```console
        $ md5sum --version
        md5sum (GNU coreutils) 8.32
        Copyright (C) 2020 Free Software Foundation, Inc.
        License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.
        This is free software: you are free to change and redistribute it.
        There is NO WARRANTY, to the extent permitted by law.

        Written by Ulrich Drepper, Scott Miller, and David Madore.
        ```

    They should both be bundled by default with Raspbian. In case they are not, make sure they are
    both installed and their binaries present in `PATH`.

1. Install [pixlet](https://github.com/tidbyt/pixlet)

    Pixlet has prebuilt `linux_arm64` binaries that can be used with RPi 4. For RPi 3/Zero, `pixlet`
    needs to be [built from source](https://github.com/tidbyt/pixlet/blob/main/docs/BUILD.md).

    Make sure the downloaded/built `pixlet` binary is in `PATH`.

    Try rendering a sample applet before continuining.

    ```console
    $ pixlet render --gif path/to/sample_applet.star
    ```

2. Download this repo

    Clone or download this repo to a directory of your choice.

3. Install project dependencies

    ```console
    $ pip3 install -r requirements.txt
    ```

### 3. Running the script

Go to this repo's directory, and run the script with
```console
$ python main.py
```

`rpi-rgb-led-matrix` asks to be run with `sudo` privileges to work properly. However, `sudo`
uses a separate environment. For `sudo` environment to find the `pixlet` binary, run

```console
$ sudo visudo
```

and add the path to `pixlet` binary in `secure_path`. It should look something like:

```
Defaults        secure_path="....:/dir/containing/pixlet"
```

With that, run the script with:

```console
$ sudo -E python main.py
```

The `-E` flag is needed for sudo to pick up all python modules available in the current environment.

You should see something like

<img src="./doc/hello_world.jpg" alt="hello_world display" width="700"/>

If the script throws permission error when reading/writing to the project directory, add write
permission for `Other`:

```console
$ chmod o+w /path/to/project
```

### 4. Configure Display

The script _should_ be capable of rendering all outputs from `pixlet` so feel free to drop in
any applet you want.

To configure which applet shows on screen, add the `.star` file to [`applets/`](./applets/)
directory, and update [`config.json`](./config.json) to point to the applet.

[`config.json`](./config.json) should have the following structure:
```javascript
{
    // NOTE: Comments are **NOT** allowed in JSON.
    "applets": [
        {
            "name": "display name of applet",
            "path": "applets/my_applet.star",
            "dynamic": false, // 'true' if the applet should be called periodically to be
                              // re-rendered. Ex: the clock applet needs to be
                              // updated every minute
            "refresh_interval_ms": 0, // in milliseconds.
                                      // Interval at which the applet should be re-rendered.
                                      // Ignored if dynamic = false.
                                      // This interval is not very precise, so err on the side of
                                      // more frequent rendering. The display will only update as
                                      // needed.
            "start_time": "15:00" // time of day at which the applet should be enabled
                                  // two applets should not start at the same time
                                  // should be a valid 24 hour time
        },
        {
            ...
        },
    ],
}
```

The script supports basic time based automation. The `start_time` attribute of each applet will be
honored if multiple applets are present.

### 5. [Optional] Extend life expectancy of your SD Card

SD Cards have limited read/write cycles and are prone to corruption if the power goes out while
being written to.

To update the display, this script calls the `pixlet` binary which writes a GIF file to the file
system. Depending on your [`config.json`](./config.json), this might happen multiple times a second
which can significantly reduce the SD Card's lifespan.

A simple solution is to mount a [RAM Disk](https://en.wikipedia.org/wiki/RAM_drive) which treats
your RAM as a disk drive.

A quick and dirty guide to mounting and using a ramdisk with the script follows:
1. Create a mount point for the ramdisk. I am using `/tmp/ramdisk`
    ```console
    $ sudo mkdir /tmp/ramdisk
    ```

2. Add correct permissions to the mount point
    ```console
    $ sudo chmod 777 /tmp/ramdisk
    ```

3. Mount ramdisk at the mount point
    ```console
    $ sudo mount -t tmpfs -o size=25m myramdisk /tmp/ramdisk
    ```

    **Note:** [tmpfs](https://en.wikipedia.org/wiki/Tmpfs) will use swap space if your device
    runs out of memory, which defeats the purpose of us creating a ramdisk, so make sure your
    Raspberry Pi has consistent 25MB free when under load. If you know your applets don't create
    large gifs, the tmpfs size can be reduced.

4. Check if mouting was successful
    ```console
    $ mount | grep myramdisk
    ```

    You should see an output like:
    ```console
    $ ramdisk mount | grep myramdisk
    myramdisk on /tmp/ramdisk type tmpfs (rw,relatime,size=25600k)
    ```

5. Update the script to write files to ramdisk

    Open [`pixlet_wrapper.py`](./pixlet_wrapper.py) and set `_OUTPUT_ROOT` to `"/tmp/ramdisk/"`.
    The line should look like:
    ```python
    _OUTPUT_ROOT = "/tmp/ramdisk/" # update this line
    _OUTPUT_DIR = _OUTPUT_ROOT + "gifs" # don't need to change this line
    ```

6. And voila! SD Card saved!

    Note that you will have to remount the ramdisk if the Raspberry Pi reboots and all information
    in the ramdisk will be lost. How to automate mounting on boot is left as an exercise for the
    reader.



## License
```
"THE BEER-WARE LICENSE" (Revision 42):
Avichal Rakesh wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
```
