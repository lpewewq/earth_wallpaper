import ftplib
from pathlib import Path
import os
from PIL import Image, UnidentifiedImageError
from datetime import datetime


Image.MAX_IMAGE_PIXELS = 11e3 ** 2


class PTree:
    hostname = "ftp.ptree.jaxa.jp"

    def __init__(self):
        self.username = os.environ.get("PTREE_USERNAME")
        assert (
            self.username is not None
        ), "PTREE_USERNAME not found in system environment."
        self.password = os.environ.get("PTREE_PASSWORD")
        assert (
            self.password is not None
        ), "PTREE_PASSWORD not found in system environment."

    def _download(self, target_file: Path, destination_file: Path) -> bool:
        try:
            # Connect FTP Server
            ftp_server = ftplib.FTP(self.hostname, self.username, self.password)
            # force UTF-8 encoding
            ftp_server.encoding = "utf-8"
            # Write file in binary mode
            with open(destination_file, "wb") as file:
                # Command for Downloading the file "RETR filename"
                ftp_server.retrbinary(f"RETR {target_file}", file.write)
            # Close the Connection
            ftp_server.quit()
            return True
        except ftplib.all_errors:
            return False

    def verify_image(self, file: Path) -> bool:
        try:
            Image.open(file).verify()
            return True
        except UnidentifiedImageError:
            return False

    def download_full_disk(self, d: datetime, destination: Path) -> Path:
        """
        Download full disk color png
        Example for 2021/01/23 at 22:40 UTC:
        jma/hsd/202101/23/22/PI_H08_20210123_2240_TRC_FLDK_R10_PGPFD.png
        """
        # Build path on ftp server
        year = d.year
        month = d.month
        day = d.day
        hour = d.hour
        minute = 10 * (d.minute // 10)
        root_path = Path("jma").joinpath(Path("hsd"))
        file_path = (
            root_path.joinpath(Path(f"{year}{month:02d}"))
            .joinpath(Path(f"{day:02d}"))
            .joinpath(Path(f"{hour:02d}"))
        )
        target_file = file_path.joinpath(
            Path(
                f"PI_H08_{year}{month:02d}{day:02d}_{hour:02d}{minute:02d}_TRC_FLDK_R10_PGPFD.png"
            )
        )
        # create directory for destination
        name = "earth.png"
        destination = destination.joinpath(Path(f"{hour:02d}/{minute:02d}"))
        destination.mkdir(parents=True, exist_ok=True)
        destination_file = destination.joinpath(Path(name))

        # check if image is still up to date
        if (
            destination_file.exists()
            and datetime.fromtimestamp(destination_file.stat().st_mtime).day == d.day
            and self.verify_image(destination_file)
        ):
            return destination_file

        # download to tmp file
        tmp_file = destination.joinpath(Path(f"~{name}"))
        print(
            f"Download full disk image at {hour:02d}:{minute:02d} UTC at",
            datetime.utcnow(),
        )
        if self._download(target_file, tmp_file):
            # copy to actual file, removing tmp file
            os.rename(tmp_file, destination_file)
            # verify image
            if self.verify_image(destination_file):
                return destination_file
        # fallback if unsuccessfull
        tmp_file.unlink(missing_ok=True)
        return None
