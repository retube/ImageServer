
# ImageServer - A simple digital photo frame app

Runs a Flask webapp, PIR motion detector service and chromium in kiosk mode on a Raspberry Pi, turning your monitor into a digital photo screen

## Requirements

- A Raspberry Pi 4B or higher
- A USB thumb drive with image library (not obligatory, can also be saved directly on the Pi's micro SD if you prefer)

## Features

- Randomly auto rotates through any image collection; handles 100k+ images
- Configurable image refresh frequency
- Power saving: screen will power down if no motion detected (timeout configurable), and halt refreshing until motion next detected
- Manual pause and next/prev buttons
- Displays date taken per EXIF data

## Setup

- Set your window manager to X11 (not Wayland/Wayfire). Can be toggled by:

```
	> sudo raspi-config
```

then Advanced Options -> Wayland/X11 

- Enable Screen Blanking: Preferences -> Raspberry Pi Configuration -> Display -> Screen Banking On
    - This ensures DPMS is running, needed by the PIR motion service

- Copy the three systemctl scripts in `config/` to `/etc/systemd/system/`. Change user names and path to images as appropriate


- Add to system boot, and start immediately:

```
    > sudo systemctl daemon-reload
    > sudo systemctl enable --now pir-display.service
    > sudo systemctl enable --now image-viewer.service
    > sudo systemctl enable --now chromium-kiosk.service
```


