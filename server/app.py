from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, send_file, abort
from ptree import PTree
from datetime import datetime, timedelta
from pathlib import Path
import atexit
import time
from PIL import Image

POLL_OFFSET_MINUTES = 20
POLL_INTERVAL_MINUTES = 10
POLL_RETRY_SECONDS = 60

DATA_DIR = Path("data")

valid_resolutions = {
    "4K": (3840, 2160),
    "WQHD": (2560, 1440),
    "WUXGA": (1920, 1200),
    "HD": (1920, 1080),
    "FHD": (1366, 768),
}

app = Flask(__name__)
ptree = PTree()
sched = BackgroundScheduler(daemon=True)
atexit.register(lambda: sched.shutdown(wait=False))
current_earth_file = None


def download():
    global current_earth_file
    earth_file = None
    while earth_file is None:
        date = datetime.utcnow() - timedelta(minutes=POLL_OFFSET_MINUTES)
        earth_file = ptree.download_full_disk(date, DATA_DIR)
        if earth_file is None:
            print("Retry")
            time.sleep(POLL_RETRY_SECONDS)
    # precompute all wallpapers
    for _, resolution in valid_resolutions.items():
        wallpaper_path = earth_file.parent.joinpath(f"earth_{resolution}.png")
        build_wallpaper(earth_file, resolution).save(wallpaper_path)
    current_earth_file = earth_file
    print("Success")


sched.add_job(
    download, "interval", minutes=POLL_INTERVAL_MINUTES, next_run_time=datetime.now()
)
sched.start()


def build_wallpaper(earth_file, resolution):
    original_img = Image.open(earth_file)
    # Resize original image, then create wallpaper
    resized_img = original_img.resize(resolution, Image.ANTIALIAS)
    resize_size = int(0.8 * min(resolution))
    resized_img = original_img.resize((resize_size, resize_size), Image.ANTIALIAS)
    wallpaper_img = Image.new("RGB", resolution)
    wallpaper_img.paste(
        resized_img,
        (
            int((resolution[0] - resized_img.size[0]) / 2),
            int((resolution[1] - resized_img.size[1]) / 2),
        ),
    )
    return wallpaper_img


@app.route("/")
def get_earth_wallpaper():
    # parse wallpaper resolution
    default_resolution = list(valid_resolutions.keys()).pop()
    resolution = valid_resolutions.get(
        request.args.get("resolution", default_resolution).upper()
    )
    if resolution is None:
        abort(400, f"resolution must be one of {list(valid_resolutions.keys())}")

    # build wallpaper
    if current_earth_file is not None:
        wallpaper_path = current_earth_file.parent.joinpath(f"earth_{resolution}.png")
        if wallpaper_path.exists():
            return send_file(wallpaper_path, mimetype="image/png")
    return send_file("404.png", mimetype="image/png")
