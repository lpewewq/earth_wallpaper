from datetime import datetime
from pathlib import Path
import logging
import os

log = logging.getLogger("common")

def get_data_directory(dtime: datetime, mkdir=False) -> (Path | None):
    directory_env = os.environ.get("DATA_DIRECTORY")
    if directory_env is None:
        log.error("DATA_DIRECTORY not set!")
        return None
    directory = Path(directory_env)
    directory = directory.joinpath(f"{dtime.hour:02d}")
    directory = directory.joinpath(f"{10 * (dtime.minute // 10):02d}")
    if mkdir:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_earth_path(dtime: datetime, mkdir=False) -> (Path | None):
    directory = get_data_directory(dtime, mkdir)
    if directory is None:
        return None
    return directory.joinpath(Path("earth.png"))
