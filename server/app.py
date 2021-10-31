from datetime import datetime, timedelta
from io import BytesIO
from shutil import make_archive
import pytz
from flask import Flask, abort, request, send_file
from PIL import Image, ImageDraw

from scheduler import Scheduler
from skyfield_wallpaper import SkyFieldWallpaper

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
skyfield_wallpaper = SkyFieldWallpaper()


@app.route("/")
def get_earth_wallpaper():
    # parse wallpaper resolution
    default_resolution = list(valid_resolutions.keys()).pop()
    resolution = valid_resolutions.get(request.args.get("resolution", default_resolution).upper())
    if resolution is None:
        abort(400, f"resolution must be one of {list(valid_resolutions.keys())}")

    # parse timezone offset
    try:
        local_tz = pytz.timezone(request.args.get("timezone"))
        utc_tz_offset = (satelite_tz.utcoffset(datetime.now()) - local_tz.utcoffset(datetime.now())).seconds // 3600
    except pytz.exceptions.UnknownTimeZoneError:
        utc_tz_offset = 0

    # parse and clamp zoom
    try:
        zoom = float(request.args.get("zoom", 0.7))
    except ValueError:
        zoom = 1.0
    zoom = 0.5 + 0.5 * min(1.0, max(0.0, zoom))

    # build wallpaper
    current_date = scheduler.current_fetch_date
    if current_date is not None:
        current_date -= timedelta(hours=utc_tz_offset)
        earth_file = scheduler.get_file_destination(current_date)
        print("UTC", datetime.now(), resolution)
        if earth_file.exists():
            wallpaper = build_wallpaper(earth_file, resolution, zoom, current_date)
            image_data = BytesIO()
            wallpaper.save(image_data, format="png")
            image_data.seek(0)
            return send_file(image_data, mimetype="image/png")
    return send_file("404.png", mimetype="image/png")


def build_wallpaper(earth_file, resolution, zoom, current_date):
    width, height = resolution
    resize_size = int(zoom * min(resolution))
    masked_earth = Image.open(earth_file)
    masked_earth.thumbnail((resize_size, resize_size), Image.ANTIALIAS)
    wallpaper = Image.new("RGBA", resolution, color="black")

    # get astro data
    try:
        fov = float(request.args.get("fov", 70))
    except ValueError:
        fov = 70
    fov = min(180, max(30, fov))
    observed_stars, observed_constellations = skyfield_wallpaper.stereographic_projection(current_date, width, height, fov)

    # draw dots for stars
    try:
        stars_scaling = float(request.args.get("stars", 0.5))
    except ValueError:
        stars_scaling = 0.5
    stars_scaling = min(1.0, max(0.0, stars_scaling))
    draw = ImageDraw.Draw(wallpaper)
    for _, star in observed_stars.iterrows():
        s = star.s * stars_scaling  # max star radius
        draw.ellipse((star.x - s, star.y - s, star.x + s, star.y + s), fill="white", outline="white")

    # draw lines for constellations
    try:
        constellation_alpha = float(request.args.get("constellations", 0.05))
    except ValueError:
        constellation_alpha = 0.05
    constellation_alpha = int(min(1.0, max(0.0, constellation_alpha)) * 255)
    constellation_overlay = Image.new("RGBA", wallpaper.size)
    constellation_overlay_draw = ImageDraw.Draw(constellation_overlay)
    for p1, p2 in observed_constellations:
        constellation_overlay_draw.line((*p1, *p2), width=1, fill=(255, 255, 255, constellation_alpha))
    wallpaper.alpha_composite(constellation_overlay)

    # add earth to center
    wallpaper.alpha_composite(
        masked_earth,
        (
            int((width - masked_earth.size[0]) / 2),
            int((height - masked_earth.size[1]) / 2),
        ),
    )
    return wallpaper
