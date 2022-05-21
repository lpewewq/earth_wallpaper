from datetime import datetime
from pathlib import Path


def get_data_directory(dtime: datetime) -> Path:
    root = Path("/")
    directory = root.joinpath("image_data")
    directory = directory.joinpath(f"{dtime.hour:02d}")
    directory = directory.joinpath(f"{10 * (dtime.minute // 10):02d}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_earth_path(dtime: datetime) -> Path:
    return get_data_directory(dtime).joinpath(Path("earth.png"))
