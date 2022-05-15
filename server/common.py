from datetime import datetime
from pathlib import Path


def get_file_destination(dtime: datetime) -> Path:
    directory = Path(f"data/{dtime.hour:02d}/{10 * (dtime.minute // 10):02d}")
    directory.mkdir(parents=True, exist_ok=True)
    return directory.joinpath(Path("earth.png"))
