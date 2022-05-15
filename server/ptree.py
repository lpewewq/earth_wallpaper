import ftplib
import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from retry import retry

log = logging.getLogger("ptree")


class PTree:
    hostname = "ftp.ptree.jaxa.jp"
    hsd_root_path = Path("jma").joinpath(Path("hsd"))

    def __init__(self):
        self.username = os.environ.get("PTREE_USERNAME")
        assert self.username is not None, "PTREE_USERNAME not found in system environment."
        self.password = os.environ.get("PTREE_PASSWORD")
        assert self.password is not None, "PTREE_PASSWORD not found in system environment."

    def _download(self, file_path: Path) -> BytesIO:
        log.log(logging.INFO, f"Download {file_path}")
        data = BytesIO()
        try:
            with ftplib.FTP(self.hostname, self.username, self.password, timeout=30) as ftp:
                ftp.retrbinary(f"RETR {file_path}", data.write)
        except ftplib.all_errors as e:
            log.log(logging.WARNING, f"Download excepted: {e}")
        return data

    def _get_full_disk_path(self, dtime: datetime) -> Path:
        timecode = f"{dtime.year}{dtime.month:02d}{dtime.day:02d}_{dtime.hour:02d}{10 * (dtime.minute // 10):02d}"
        return self.hsd_root_path.joinpath(
            Path(f"{dtime.year}{dtime.month:02d}")
            .joinpath(Path(f"{dtime.day:02d}"))
            .joinpath(Path(f"{dtime.hour:02d}"))
            .joinpath(Path(f"PI_H08_{timecode}_TRC_FLDK_R10_PGPFD.png"))
        )

    @retry(UnidentifiedImageError, tries=10, delay=60, jitter=60)
    def download_full_disk(self, dtime: datetime) -> Image:
        ftp_full_disk_path = self._get_full_disk_path(dtime)
        image_data = self._download(ftp_full_disk_path)
        Image.open(image_data).verify()
        log.log(logging.INFO, f"Image verification successfull!")
        return Image.open(image_data)
