import ftplib
from datetime import datetime, timedelta
from pathlib import Path
import time
import os
from PIL import Image


DISPLAY_WIDTH = 1366
DISPLAY_HEIGHT = 768
FILL_PERCENTAGE = 0.9

POLL_OFFSET_MINUTES = 30
POLL_SLEEP_MINUTES = 10

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

    def _download(self, target_file: Path, destination_file: Path) -> None:
        # Connect FTP Server
        ftp_server = ftplib.FTP(self.hostname, self.username, self.password)
        # force UTF-8 encoding
        ftp_server.encoding = "utf-8"
        # check if file exists
        ftp_server.dir(str(target_file))
        # Write file in binary mode
        with open(destination_file, "wb") as file:
            # Command for Downloading the file "RETR filename"
            ftp_server.retrbinary(f"RETR {target_file}", file.write)
        # Close the Connection
        ftp_server.quit()

    def download_current_full_disk_png(self, d: datetime) -> Path:
        """
        Download full disk color png
        Example for 2021/01/23 at 22:40 UTC:
        jma/hsd/202101/23/22/PI_H08_20210123_2240_TRC_FLDK_R10_PGPFD.png
        """
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

        # Check if file already cached
        destination_file = file_path.joinpath(Path(f"{minute:02d}.png"))
        if not destination_file.exists():
            file_path.mkdir(parents=True, exist_ok=True)
            self._download(target_file, destination_file)
        return destination_file


ptree = PTree()
while True:
    utcnow = datetime.utcnow()
    file_path = ptree.download_current_full_disk_png(
        utcnow - timedelta(minutes=POLL_OFFSET_MINUTES)
    )

    original_img = Image.open(file_path)
    if original_img.size != (DISPLAY_WIDTH, DISPLAY_HEIGHT):
        # Resize original image, then create wallpaper
        resize_size = int(FILL_PERCENTAGE * min(DISPLAY_WIDTH, DISPLAY_HEIGHT))
        resized_img = original_img.resize((resize_size, resize_size), Image.ANTIALIAS)
        wallpaper_img = Image.new("RGB", (DISPLAY_WIDTH, DISPLAY_HEIGHT))
        wallpaper_img.paste(
            resized_img,
            (
                int((DISPLAY_WIDTH - resized_img.size[0]) / 2),
                int((DISPLAY_HEIGHT - resized_img.size[1]) / 2),
            ),
        )
        wallpaper_img.save(file_path)
        wallpaper_img.save("wallpaper.png")

    # Wait
    s = ((utcnow + timedelta(minutes=POLL_SLEEP_MINUTES) - datetime.utcnow())).seconds
    print(f"Wait: {s // 60}:{s % 60}")
    time.sleep(s)
