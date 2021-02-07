import ftplib
import os
from io import BytesIO
from pathlib import Path

from PIL import Image


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

    def _download(self, file: Path) -> BytesIO:
        try:
            # Connect FTP Server
            ftp_server = ftplib.FTP(self.hostname, self.username, self.password)
            # force UTF-8 encoding
            ftp_server.encoding = "utf-8"
            # Command for Downloading the file
            data = BytesIO()
            ftp_server.retrbinary(f"RETR {file}", data.write)
            # Close the Connection
            ftp_server.quit()
            return data
        except ftplib.all_errors:
            pass
        return None

    def download_hsd(self, file: Path) -> BytesIO:
        root_path = Path("jma").joinpath(Path("hsd"))
        return self._download(root_path.joinpath(file))
