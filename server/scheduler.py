import atexit
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

    try:
        earth = ptree.download_full_disk(dtime)
    except UnidentifiedImageError:
        log.log(logging.WARNING, "Could not download full disk image")
        return

    # preprocess image: resize and mask earth
    log.log(logging.INFO, "Resize earth...")
    size = (2160, 2160)
    earth = earth.resize(size, Image.Resampling.LANCZOS)
    log.log(logging.INFO, "Mask earth...")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
    earth = ImageOps.fit(earth, mask.size, centering=(0.5, 0.5))
    earth.putalpha(mask)

    log.log(logging.INFO, "Composite earth and night background...")
    # add day earth to background
    for y in range(size[0]):
        for x in range(size[1]):
            r, g, b, _ = earth.getpixel((x, y))
            # alpha-out dark side of earth
            a = min(255, 10 * max(r, g, b))
            earth.putpixel((x, y), (r, g, b, a))
    background = Image.open("night_background.png")
    background.alpha_composite(earth)

    log.log(logging.INFO, "Save earth...")
    background.save(get_file_destination(dtime))
    log.log(logging.INFO, "... successfull!")


if __name__ == "__main__":
    log.log(logging.INFO, "--- Start scheduler application ---")
    scheduler.start()
