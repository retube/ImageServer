#!/usr/bin/env python3
import argparse
from pathlib import Path
from gpiozero import MotionSensor
from subprocess import run, CalledProcessError
from time import time, sleep
import os, signal, logging, logging.handlers

PIR_GPIO: int = 17
QUIET_SECS: int = 300
DISPLAY_ENV: str = ":0"

HOME: Path = Path.home()

STATUS_FILE: Path = Path.home() / "temp" / "screen_status.txt"
STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

XAUTHORITY: str = str(Path.home() / "Xauthority")
LOG_PATH: Path = Path.home() / "temp" / "pir.log"

os.environ["DISPLAY"] = DISPLAY_ENV
os.environ["XAUTHORITY"] = XAUTHORITY

pir = MotionSensor(PIR_GPIO)
last_motion = time()
display_on = True
running = True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_PATH, maxBytes=512*1024, backupCount=5, encoding="utf-8"
        )
    ],
)
log = logging.getLogger("pir")

def update_state(on: bool):
    global display_on
    display_on = on
    with open(STATUS_FILE, "w") as f:
        f.write("ON" if on else "OFF")

def safe_run(cmd: str):
    try:
        return run(cmd, check=False)
    except FileNotFoundError:
        pass

def screen_on():
    log.info("Turning screen ON")
    safe_run(["xset", "dpms", "force", "on"])
    update_state(True)

def screen_off():
    log.info("Turning screen OFF")
    safe_run(["xset", "dpms", "force", "off"])
    update_state(False)

def on_motion():
    log.info("Motion detected")
    global last_motion
    last_motion = time()
    if not display_on:
        screen_on()

pir.when_motion = on_motion

def shutdown(signum, frame):
    log.info("Caught shutdown")
    global running
    running = False
    
signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)
    
def main():

    log.info("Running pir.py")

    # Start assuming screen on
    update_state(True)

    safe_run(["xset", "dpms", "0", "0", "0"])
    safe_run(["xset", "s", "off"])

    try:
        while running:
            time_delta = time() - last_motion
            log.debug(f'Time delta {time_delta}, display_on: {display_on}')
        
            if (time() - last_motion) > QUIET_SECS and display_on:
                screen_off()
            sleep(1)
    finally:
        pir.when_motion = None
        pir.close()
        log.info("PIR closed")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="PIR motion check script")
    parser.add_argument("--timeout", type=int, default=300, help="Display timeout in seconds")
    args = parser.parse_args()

    QUIET_SECS = max(10, args.timeout)

    main()


