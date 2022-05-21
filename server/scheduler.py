import atexit
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from PIL import Image, ImageDraw, ImageEnhance, ImageOps
from pyresample import AreaDefinition
from satpy import Scene, find_files_and_readers

from common import get_data_directory, get_earth_path
from ptree import PTree

# full disk image is 11k x 11k pixel
Image.MAX_IMAGE_PIXELS = 11e3**2

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
log = logging.getLogger("scheduler")

scheduler = BlockingScheduler()
atexit.register(lambda: scheduler.shutdown(wait=False))

ptree = PTree()

width = 2160
height = 2160

area = AreaDefinition(
    area_id="FLDK",
    description="AHI FLDK area",
    proj_id="geosh8",
    projection={
        "a": "6378137",
        "h": "35785863",
        "lon_0": "140.7",
        "no_defs": "None",
        "proj": "geos",
        "rf": "298.257024882273",
        "type": "crs",
        "units": "m",
        "x_0": "0",
        "y_0": "0",
    },
    width=width,
    height=height,
    area_extent=(-5499999.9684, -5499999.9684, 5499999.9684, 5499999.9684),
)


def preprocess(dtime: datetime, earth_path: Path, night_ir_path: Path):
    background = Image.open("BlackMarble_2016_Himawari8_preprocessed.png")

    # add night clouds to background
    if night_ir_path:
        log.info("Compose night background and IR clouds...")
        night_ir = Image.open(night_ir_path)
        night_ir = ImageEnhance.Brightness(night_ir).enhance(0.01)
        background.alpha_composite(night_ir)

    # preprocess image: resize and mask earth
    log.info("Resize and mask earth...")
    earth = Image.open(earth_path)
    earth = earth.resize((width, height), Image.Resampling.LANCZOS)
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + (width, height), fill=255)
    earth = ImageOps.fit(earth, mask.size, centering=(0.5, 0.5))
    earth.putalpha(mask)

    log.info("Composite earth and night background...")
    # add day earth to background
    for y in range(height):
        for x in range(width):
            r, g, b, _ = earth.getpixel((x, y))
            # alpha-out dark side of earth
            a = min(255, 10 * max(r, g, b))
            earth.putpixel((x, y), (r, g, b, a))
    background.alpha_composite(earth)

    earth_path = get_earth_path(dtime)
    background.save(earth_path)
    log.info(f"Saved {earth_path}")


@scheduler.scheduled_job(trigger=CronTrigger(minute=",".join(str(i) for i in range(5, 60, 10))), max_instances=3)
def download_job():
    """
    Download latest full disk image of earth
    """
    dtime = datetime.utcnow() - timedelta(minutes=15)

    try:
        fldk_path, night_cloud_paths = ptree.download_all(dtime)

        # verify full disk image
        Image.open(fldk_path).verify()

        # generate night IR clouds
        night_clouds_file_path = None
        if len(night_cloud_paths) > 0 and all(night_cloud_paths):
            try:
                data_directory_path = get_data_directory(dtime)
                scene_files = find_files_and_readers(base_dir=str(data_directory_path), reader="ahi_hsd")
                scene = Scene(filenames=scene_files, reader="ahi_hsd")
                scene.load(scene.available_dataset_names())
                scene_re = scene.resample(area)
                scene_re.load(["night_ir_alpha"])
                night_clouds_file_path = data_directory_path.joinpath("night_clouds.png")
                scene_re.save_dataset("night_ir_alpha", str(night_clouds_file_path))
            except UnicodeDecodeError as e:
                log.warning(f"Night cloud data decode error! {e}")

        preprocess(dtime, fldk_path, night_clouds_file_path)
    except Exception as e:
        log.exception(f"Image composition failed! {e}")
    finally:
        for path in [fldk_path, night_clouds_file_path] + night_cloud_paths:
            if path and path.is_file:
                path.unlink(missing_ok=True)
        log.info("Removed downloaded files!")


if __name__ == "__main__":
    log.info("--- Start scheduler application ---")
    scheduler.start()
