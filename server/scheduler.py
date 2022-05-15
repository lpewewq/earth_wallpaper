import atexit
import gc
import logging
import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from common import get_file_destination
from ptree import PTree

# full disk image is 11k x 11k pixel
Image.MAX_IMAGE_PIXELS = 11e3**2

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger("scheduler")

scheduler = BlockingScheduler()
atexit.register(lambda: scheduler.shutdown(wait=False))

ptree = PTree()


@scheduler.scheduled_job(trigger=CronTrigger(minute=",".join(str(i) for i in range(5, 60, 10))), max_instances=3)
def download_job():
    """
    Download latest full disk image of earth
    """
    dtime = datetime.utcnow() - timedelta(minutes=10)

    # check if image is still up to date
    file_destination = get_file_destination(dtime)
    if file_destination.exists() and datetime.fromtimestamp(file_destination.stat().st_mtime).day == dtime.day:
        log.log(logging.INFO, f"Still up to date {file_destination}")
        return

    try:
        image = ptree.download_full_disk(dtime)
    except UnidentifiedImageError:
        log.log(logging.WARNING, "Could not download full disk image")
        return

    # preprocess image: resize and mask earth
    log.log(logging.INFO, "Resize image...")
    size = (2160, 2160)
    image = image.resize(size, Image.Resampling.LANCZOS)
    log.log(logging.INFO, "Mask image...")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
    image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
    image.putalpha(mask)
    log.log(logging.INFO, "Save image...")
    image.save(file_destination)
    log.log(logging.INFO, "... successfull!")
    gc.collect()


if __name__ == "__main__":
    log.log(logging.INFO, "--- Start scheduler application ---")
    scheduler.start()
