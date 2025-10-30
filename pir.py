#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


STATUS_FILE: str = ""


def safe_run():
    pass

def screen_on():
    print("hello")

def run():
    #print(STATUS_FILE)
    write_state(True)


def write_state(on: bool):
    with open(STATUS_FILE, "w") as f:
        f.write("ON" if on else "OFF")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="PIR motion check script")
    parser.add_argument("status_file", type=Path, help="Location of file to write screen status")
    args = parser.parse_args()
    
    STATUS_FILE = args.status_file

    run()


