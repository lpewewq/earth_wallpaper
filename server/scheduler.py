import atexit
import time
from datetime import datetime, timedelta
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

from ptree import PTree

Image.MAX_IMAGE_PIXELS = 11e3 ** 2


class Scheduler:
    POLL_OFFSET_MINUTES = 20
    POLL_INTERVAL_MINUTES = 10
    POLL_RETRY_SECONDS = 60
    DATA_DIR = Path("data")

    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._ptree = PTree()
        atexit.register(lambda: self._scheduler.shutdown(wait=False))
        self._scheduler.add_job(
            self.download_job,
            "interval",
            minutes=self.POLL_INTERVAL_MINUTES,
            next_run_time=datetime.now(),
        )
        self._scheduler.start()
        self.current_fetch_date = None

    def get_fetch_datetime(self):
        d = datetime.utcnow() - timedelta(minutes=self.POLL_OFFSET_MINUTES)
        return d.replace(minute=10 * (d.minute // 10))

    def get_full_disk_path(self, d: datetime) -> Path:
        return (
            Path(f"{d.year}{d.month:02d}")
            .joinpath(Path(f"{d.day:02d}"))
            .joinpath(Path(f"{d.hour:02d}"))
            .joinpath(
                Path(
                    f"PI_H08_{d.year}{d.month:02d}{d.day:02d}_{d.hour:02d}{d.minute:02d}_TRC_FLDK_R10_PGPFD.png"
                )
            )
        )

    def get_file_destination(self, d: datetime) -> Path:
        destination = self.DATA_DIR.joinpath(Path(f"{d.hour:02d}/{d.minute:02d}"))
        destination.mkdir(parents=True, exist_ok=True)
        return destination.joinpath(Path("earth.png"))

    def download_job(self):
        """
        Download latest satelite image of earth
        """
        for _ in range(10):
            fetch_date = self.get_fetch_datetime()
            file_destination = self.get_file_destination(fetch_date)

            # check if image is still up to date
            if (
                file_destination.exists()
                and datetime.fromtimestamp(file_destination.stat().st_mtime).day
                == fetch_date.day
            ):
                self.current_fetch_date = fetch_date
                break

            # download new image
            ftp_path = self.get_full_disk_path(fetch_date)
            image_data = self._ptree.download_hsd(ftp_path)

            # verify image
            try:
                Image.open(image_data).verify()
            except (UnidentifiedImageError, AttributeError):
                time.sleep(self.POLL_RETRY_SECONDS)
                continue

            # preprocess image: resize to 4K and mask earth
            size = (2160, 2160)
            image = Image.open(image_data)
            image = image.resize(size, Image.ANTIALIAS)
            mask = Image.new("L", size, 0)
            ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
            image = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
            image.putalpha(mask)
            image.save(file_destination)
            self.current_fetch_date = fetch_date
            break
