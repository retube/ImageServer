#!/usr/bin/env python3
"""
Simple HTTP server that:
  a) On startup, recursively indexes image files in a given directory
     (provided as a runtime argument) and keeps that list in memory.
  b) Exposes endpoints for:
       - /file/<int:index>   : returns the indexed file (0-based)
       - /meta/<int:index>   : returns metadata (EXIF date, computed on-demand with caching)
       - /count              : returns number of indexed files
       - /healthz            : simple health check
       - /                   : serves base HTML page
  c) The base page (index.html) displays an image and cycles through images.

Usage:
    python app.py /path/to/images --host 127.0.0.1 --port 8000 --interval-ms 3000
"""

from __future__ import annotations

import argparse
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List
from functools import lru_cache
import random
from flask import Flask, abort, jsonify, make_response, render_template, send_file
from PIL import Image, ExifTags

app = Flask(__name__)

FILES: List[Path] = []   # indexed image files
INTERVAL_MS: int = 10000  # client refresh interval in ms
SCREEN_STATUS_FILE: str = ""

# Supported image extensions
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"}

# ------------------------------------------------------------------------------
# Directory indexing
# ------------------------------------------------------------------------------
def index_directory(root: Path, all_files: bool) -> List[Path]:
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    collected: List[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            p = Path(dirpath) / fn
            if all_files:
                collected.append(p)
            else:
                if p.suffix.lower() in IMAGE_EXTS:
                    collected.append(p)
    # Sorting gives deterministic order; for 100k files this is still usually fine.
    collected.sort(key=lambda p: str(p.resolve()))
    return collected


# ------------------------------------------------------------------------------
# On-demand EXIF helpers (cached)
# ------------------------------------------------------------------------------
def _exif_date_from_pillow(img: "Image.Image") -> str | None:
    """Extracts EXIF date fields and returns ISO 8601 UTC string, if found."""
    try:
        exif = getattr(img, "getexif", None)
        raw = exif() if callable(exif) else getattr(img, "_getexif", lambda: None)()
        if not raw:
            return None
        tagmap = {ExifTags.TAGS.get(k, k): v for k, v in raw.items()} if ExifTags else raw
        for key in ["DateTimeOriginal", "DateTime", "DateTimeDigitized"]:
            val = tagmap.get(key)
            if not val:
                continue
            if isinstance(val, bytes):
                val = val.decode(errors="ignore")
            val = str(val)
            try:
                # Typical EXIF: 'YYYY:MM:DD HH:MM:SS'
                dt = datetime.strptime(val[:19], "%Y:%m:%d %H:%M:%S")
                return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            except Exception:
                continue
    except Exception:
        return None
    return None


@lru_cache(maxsize=10000)  # adjust size based on memory/usage
def _compute_meta_cached(path_str: str, mtime: float) -> dict:
    """
    Compute metadata for a file path. Cached by (path, mtime) so changes invalidate.
    Returns a dict with keys: date_taken, date_source, filename.
    """
    date_taken = None
    path = Path(path_str)

    # Special handling for the images in the 2010-2012 folder which were scanned from prints,
    # so have the scan date in the exif data and not the actual snapshot date
    if "2010-2012" in str(path):
        return {"date_taken": "2010-2012", "date_source": "unknown", "filename": path.name}

    # Then try EXIF (if likely an image)
    if Image and path.suffix.lower() in IMAGE_EXTS:
        try:
            with Image.open(path) as im:
                iso = _exif_date_from_pillow(im)
                if iso:
                    return {"date_taken": iso, "date_source": "exif", "filename": path.name}
        except Exception:
            pass

    return {"date_taken": date_taken, "date_source": "unknown", "filename": path.name}


# ------------------------------------------------------------------------------
# HTTP endpoints
# ------------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {"ok": True, "count": len(FILES)}


@app.get("/count")
def count():
    return {"count": len(FILES)}


@app.get("/should_load_next")
def should_load_next():
    try:
        with open(SCREEN_STATUS_FILE) as f:
            return {"load_next": f.read().strip() == "ON"}
    except FileNotFoundError as e:
        print(e)
        pass

    return {"load_next": True}


@app.get("/meta/<int:index>")
def get_meta(index: int):
    if index < 0 or index >= len(FILES):
        abort(404, description=f"Index out of range: {index}")
    path = FILES[index]
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        abort(404, description="File not found")
    info = _compute_meta_cached(str(path.resolve()), mtime)
    payload = {
        "index": index,
        "filename": info.get("filename"),
        "date_taken": info.get("date_taken"),
        "date_source": info.get("date_source"),
    }
    return jsonify(payload)


@app.get("/file/<int:index>")
def get_file(index: int):
    if index < 0 or index >= len(FILES):
        abort(404, description=f"Index out of range: {index}")
    path = FILES[index]
    mime, _ = mimetypes.guess_type(str(path))
    if mime is None:
        mime = "application/octet-stream"
    resp = make_response(send_file(path, mimetype=mime, as_attachment=False, conditional=True))
    # Avoid overly aggressive caching while we rotate images
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp


@app.get("/")
def index_page():
    return render_template("index.html", count=len(FILES), interval_ms=INTERVAL_MS)


# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------
def main():
    global FILES, INTERVAL_MS, SCREEN_STATUS_FILE

    parser = argparse.ArgumentParser(description="Simple rotating image HTTP server")
    parser.add_argument("directory", type=Path, help="Directory to recursively index")
    parser.add_argument("--screen_status_file", type=Path, default="static/screen_status.txt", help="Location of screen status file written by PIR")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--interval-ms", type=int, default=10000, help="Client refresh interval in ms")
    parser.add_argument("--all-files", action="store_true", help="Index ALL files, not just images")
    args = parser.parse_args()

    INTERVAL_MS = max(3000, int(args.interval_ms))
    FILES = index_directory(args.directory, all_files=args.all_files)
    SCREEN_STATUS_FILE = args.screen_status_file

    if not FILES:
        print("[warn] No files found to index. The page will show 'no files'.")
    else:
        print(f"Indexed {len(FILES)} file(s). Example: /file/0 -> {FILES[0]}")

    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
