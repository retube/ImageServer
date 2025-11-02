
# ImageServer - A simple digital photo frame app

Runs a Flask webapp, PIR motion detector service and chromium in kiosk mode on a Raspberry Pi, turning your monitor into a digital photo album

## Requirements

- A Raspberry Pi 4B 
- A PIR motion detector
- A USB thumb drive with image library (not obligatory, can also be saved directly on the Pi's micro SD if you prefer)

## Features

- Auto rotates through any image collection; handles 100k+ images
- Configurable image refresh frequency
- Power saving: screen will power down if no motion detected (timeout configurable), and halt image refreshing until motion next detected
- Manual pause, next and prev buttons
- Displays date taken per EXIF data

## Hardware Setup

- Micro SD card installed with Raspbian image
- Pi Micro HDMI to monitor
- 2x Pi USB 2.0 to keyboard + mouse (can later be disconnected/removed)
- PIR VCC to GPIO pin 2
- PIR GRD to GPIO pin 4
- PIR OUT to GPIO pin 11 (GPIO 17)

Pi power: USB-C from dedicated power supply or monitor USB-C with minimum 45 watts

## Software install

```
	> git clone https://github.com/retube/ImageServer.git
```

- Check you have the necessary python packages installed - just run the two scripts to check any dependency failures:

```
	> cd ImageServer
	> ./pir.py
	> ./app.py "/path/to/image_folder"
```

and `pip install` anything missing.

## System setup

- Set your window manager to X11 (not Wayland/Wayfire). Window manager can be checked/toggled by:

```
	> sudo raspi-config
```

   then Advanced Options -> Wayland/X11 

- Enable Screen Blanking: Preferences -> Raspberry Pi Configuration -> Display -> Screen Banking On
    - This ensures DPMS is running, needed by the PIR motion service

- Copy the three systemctl scripts in `config/` to `/etc/systemd/system/`. Change user names and path to images as appropriate.


- Add to system boot, and start immediately:

```
    > sudo systemctl daemon-reload
    > sudo systemctl enable --now pir-display.service
    > sudo systemctl enable --now image-viewer.service
    > sudo systemctl enable --now chromium-kiosk.service
```

And now with any luck, you are in kiosk mode showing images. Alt-F4 to exit and get the desktop back.


