#!/usr/bin/env python3
import argparse
from pathlib import Path
from gpiozero import MotionSensor
from subprocess import run, CalledProcessError
from time import time, sleep
import os


STATUS_FILE: str = ""


PIR_GPIO = 17           # GPIO pin for PIR OUT
QUIET_SECS = 300        # blank after 5 minutes of no motion
DISPLAY_ENV = ":0"      # X11 display
XAUTHORITY = "/home/rich/.Xauthority"  # adjust if your user isn’t 'pi'

os.environ["DISPLAY"] = DISPLAY_ENV
os.environ["XAUTHORITY"] = XAUTHORITY

pir = MotionSensor(PIR_GPIO)
last_motion = time()
display_on = True

def safe_run(cmd):
    try:
        return run(cmd, check=False)
    except FileNotFoundError:
        pass

def screen_on():
    safe_run(["xset", "dpms", "force", "on"])
    write_state(True)

def screen_off():
    safe_run(["xset", "dpms", "force", "off"])
    write_state(False)

def on_motion():
    global last_motion, display_on
    last_motion = time()
    if not display_on:
        screen_on()
        display_on = True

pir.when_motion = on_motion

def main():

    global display_on

    safe_run(["xset", "s", "off"])  # disable screensaver timer
    safe_run(["xset", "-dpms"])

    while True:
        if (time() - last_motion) > QUIET_SECS and display_on:
            screen_off()
            display_on = False
        sleep(1)

def write_state(on: bool):
    with open(STATUS_FILE, "w") as f:
        f.write("ON" if on else "OFF")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="PIR motion check script")
    parser.add_argument("status_file", type=Path, help="Location of file to write screen status")
    args = parser.parse_args()
    
    STATUS_FILE = args.status_file

    main()


