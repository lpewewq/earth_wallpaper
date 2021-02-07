from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytz
from flask import Flask, abort, request, send_file
from PIL import Image

from scheduler import Scheduler

satelite_tz = pytz.timezone("Asia/Jayapura")
valid_resolutions = {
    "4K": (3840, 2160),
    "WQHD": (2560, 1440),
    "WUXGA": (1920, 1200),
    "HD": (1920, 1080),
    "FHD": (1366, 768),
}

app = Flask(__name__)
scheduler = Scheduler()


@app.route("/")
def get_earth_wallpaper():
    # parse wallpaper resolution
    default_resolution = list(valid_resolutions.keys()).pop()
    resolution = valid_resolutions.get(
        request.args.get("resolution", default_resolution).upper()
    )
    if resolution is None:
        abort(400, f"resolution must be one of {list(valid_resolutions.keys())}")

    # parse timezone offset
    try:
        local_tz = pytz.timezone(request.args.get("timezone"))
        utc_tz_offset = (
            satelite_tz.utcoffset(datetime.now()) - local_tz.utcoffset(datetime.now())
        ).seconds // 3600
    except pytz.exceptions.UnknownTimeZoneError:
        utc_tz_offset = 0

    # parse and clamp zoom
    try:
        zoom = float(request.args.get("zoom", 1.0))
    except ValueError:
        zoom = 1.0
    zoom = 0.5 + 0.5 * min(1.0, max(0.0, zoom))

    # build wallpaper
    current_date = scheduler.current_fetch_date
    if current_date is not None:
        current_date -= timedelta(hours=utc_tz_offset)
        earth_file = scheduler.get_file_destination(current_date)
        if earth_file.exists():
            wallpaper = build_wallpaper(earth_file, resolution, zoom)
            image_data = BytesIO()
            wallpaper.save(image_data, format="png")
            image_data.seek(0)
            return send_file(image_data, mimetype="image/png")
    return send_file("404.png", mimetype="image/png")


def build_wallpaper(earth_file, resolution, zoom):
    resize_size = int(zoom * min(resolution))
    masked_earth = Image.open(earth_file)
    masked_earth = masked_earth.resize((resize_size, resize_size), Image.ANTIALIAS)
    wallpaper = Image.new("RGB", resolution)
    wallpaper.paste(
        masked_earth,
        (
            int((resolution[0] - masked_earth.size[0]) / 2),
            int((resolution[1] - masked_earth.size[1]) / 2),
        ),
    )
    return wallpaper
