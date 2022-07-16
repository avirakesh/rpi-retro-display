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

0. Install Python 3
    ```console
    $ python --version
    Python 3.9.2
    ```

    Python versions >= 3.9 should work!

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
$ sudo python main.py
```

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
            "refresh_interval_ms": 0 // in milliseconds.
                                        // Interval at which the applet should be re-rendered.
                                        // Ignored if dynamic = false.
                                        // This interval is not very precise, so err on the side of
                                        // more frequent rendering
        },
        {
            ...
        },
    ],
}
```

**NOTE:** The script will only use the first applet in [`config.json`](./config.json) for now.
The plan is to allow some basic automation in the future.

## License
```
"THE BEER-WARE LICENSE" (Revision 42):
Avichal Rakesh wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return. Avichal Rakesh
```
