from datetime import datetime
from pathlib import Path


def get_data_directory(dtime: datetime) -> Path:
    directory = Path(f"data/{dtime.hour:02d}/{10 * (dtime.minute // 10):02d}")
    directory.mkdir(parents=True, exist_ok=True)
    return Path.cwd().joinpath(directory)


def get_earth_path(dtime: datetime) -> Path:
    return get_data_directory(dtime).joinpath(Path("earth.png"))
