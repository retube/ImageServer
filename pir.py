#!/usr/bin/env python3
import argparse
from pathlib import Path
from gpiozero import MotionSensor
from subprocess import run, CalledProcessError
from time import time, sleep
import os, signal

STATUS_FILE: str = "temp/screen_status.txt"
PIR_GPIO = 17
QUIET_SECS = 300
DISPLAY_ENV = ":0"
XAUTHORITY = "/home/rich/.Xauthority"

os.environ["DISPLAY"] = DISPLAY_ENV
os.environ["XAUTHORITY"] = XAUTHORITY

pir = MotionSensor(PIR_GPIO)
last_motion = time()
display_on = True
running = True

def safe_run(cmd):
    try:
        return run(cmd, check=False)
    except FileNotFoundError:
        pass

def screen_on():
    print(f'Turning screen ON {time()}')
    safe_run(["xset", "dpms", "force", "on"])
    update_state(True)

def screen_off():
    print(f'Turning screen OFF {time()}')
    safe_run(["xset", "dpms", "force", "off"])
    update_state(False)

def on_motion():
    print(f'Motion detected {time()}')
    global last_motion
    last_motion = time()
    if not display_on:
        screen_on()

pir.when_motion = on_motion

def shutdown(signum, frame):
    print("Caught shutdown")
    global running
    running = False
    
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
    
def main():

    print("Running pir.py")

    #safe_run(["xset", "s", "off"])  # disable screensaver timer
    #safe_run(["xset", "-dpms"])

    try:
        while running:
            time_delta = time() - last_motion
            print(f'Time delta {time_delta}')
        
            if (time() - last_motion) > QUIET_SECS and display_on:
                screen_off()
            sleep(1)
    finally:
        print("Closing PIR")
        pir.when_motion = None
        pir.close()

def update_state(on: bool):
    global display_on
    display_on = on
    with open(STATUS_FILE, "w") as f:
        f.write("ON" if on else "OFF")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="PIR motion check script")
    parser.add_argument("--timeout", type=int, default=300, help="Display timeout in seconds")
    args = parser.parse_args()

    QUIET_SECS = max(10, args.timeout)

    main()


