import ftplib
import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Tuple, List
from multiprocessing.pool import ThreadPool
from functools import partial

from retry import retry

from common import get_data_directory

log = logging.getLogger("ptree")


class PTree:
    hostname = "ftp.ptree.jaxa.jp"
    hsd_root_path = Path("jma").joinpath(Path("hsd"))

    def __init__(self):
        self.username = os.environ.get("PTREE_USERNAME")
        assert self.username is not None, "PTREE_USERNAME not found in system environment."
        self.password = os.environ.get("PTREE_PASSWORD")
        assert self.password is not None, "PTREE_PASSWORD not found in system environment."

    @retry(ftplib.all_errors, tries=10, delay=30, jitter=(0, 10))
    def _download(self, file_path: Path) -> BytesIO:
        log.debug(f"Download {file_path}")
        data = BytesIO()
        with ftplib.FTP(self.hostname, self.username, self.password, timeout=10) as ftp:
            ftp.retrbinary(f"RETR {file_path}", data.write)
        return data

    def _get_hsd_dir_path(self, dtime: datetime) -> Tuple[Path, str]:
        timecode = f"{dtime.year}{dtime.month:02d}{dtime.day:02d}_{dtime.hour:02d}{10 * (dtime.minute // 10):02d}"
        directory_path = self.hsd_root_path.joinpath(
            Path(f"{dtime.year}{dtime.month:02d}").joinpath(Path(f"{dtime.day:02d}")).joinpath(Path(f"{dtime.hour:02d}"))
        )
        return (directory_path, timecode)

    def download_path(self, path: Path, dtime: datetime) -> Path:
        try:
            data = self._download(path)
        except ftplib.all_errors:
            log.warning(f"Download failed! {path}")
            return None

        file_destination = get_data_directory(dtime).joinpath(path.name)
        log.debug(f"Save file {file_destination}")
        with open(file_destination, "wb") as outfile:
            outfile.write(data.getbuffer())

        return file_destination

    def download_all(self, dtime: datetime) -> Tuple[Path, List[Path]]:
        paths = []
        hsd_dir_path, timecode = self._get_hsd_dir_path(dtime)
        # high resolution color image of full disk
        paths.append(hsd_dir_path.joinpath(Path(f"PI_H08_{timecode}_TRC_FLDK_R10_PGPFD.png")))
        # IR bands for night clouds
        for band in [7, 13, 15]:
            for part in range(1, 11):
                paths.append(hsd_dir_path.joinpath(Path(f"HS_H08_{timecode}_B{band:02d}_FLDK_R20_S{part:02d}10.DAT.bz2")))
        # Download concurrently
        log.debug(f"Download {len(paths)} files...")
        results = ThreadPool(len(paths)).map(partial(self.download_path, dtime=dtime), paths)
        return results[0], results[1:]
