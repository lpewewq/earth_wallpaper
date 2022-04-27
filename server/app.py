from datetime import datetime, timedelta
from io import BytesIO
import pytz
import regex as re
from fastapi import FastAPI, Query, Response, exceptions
from PIL import Image, ImageDraw
from enum import Enum

from scheduler import Scheduler
from skyfield_wallpaper import SkyFieldWallpaper

satelite_tz = pytz.timezone("Asia/Jayapura")
Timezone = Enum("Timezone", ((x, x) for x in pytz.all_timezones))


class Resolution(str, Enum):
    UHD_4K = "4K"
    WQHD = "WQHD"
    WUXGA = "WUXGA"
    HD = "HD"
    FHD = "FHD"

    @property
    def width(self):
        if self == Resolution.UHD_4K:
            return 3840
        elif self == Resolution.WQHD:
            return 2560
        elif self == Resolution.WUXGA:
            return 1920
        elif self == Resolution.HD:
            return 1920
        elif self == Resolution.FHD:
            return 1366

    @property
    def height(self):
        if self == Resolution.UHD_4K:
            return 2160
        elif self == Resolution.WQHD:
            return 1440
        elif self == Resolution.WUXGA:
            return 1200
        elif self == Resolution.HD:
            return 1080
        elif self == Resolution.FHD:
            return 768


app = FastAPI()
scheduler = Scheduler()
skyfield_wallpaper = SkyFieldWallpaper()


@app.get("/")
async def earth_wallpaper(
    resolution: Resolution = Query(Resolution("4K")),
    timezone: Timezone = Query(Timezone("Europe/Berlin")),
    zoom: float = Query(0.7, ge=0.0, le=1.0),
    fov: int = Query(70, ge=30, le=180),
    stars: float = Query(0.5, ge=0.0, le=1.0),
    constellations: float = Query(0.05, ge=0.0, le=1.0),
):
    # build wallpaper
    current_date = scheduler.current_fetch_date
    if current_date is None:
        raise exceptions.HTTPException(404)

    # parse timezone offset
    now = datetime.now()
    current_date -= satelite_tz.utcoffset(now) - pytz.timezone(timezone.value).utcoffset(now)
    earth_file = scheduler.get_file_destination(current_date)
    if not earth_file.exists():
        raise exceptions.HTTPException(404)

    wallpaper = build_wallpaper(earth_file, resolution, zoom, current_date, fov, stars, constellations)
    image_data = BytesIO()
    wallpaper.save(image_data, format="png")
    return Response(image_data.getvalue(), media_type="image/png")


def build_wallpaper(
    earth_file,
    resolution: Resolution,
    zoom: float,
    current_date: datetime,
    fov: int,
    stars_scaling: float,
    constellation_alpha: float,
):
    width, height = resolution.width, resolution.height
    resize_size = int(zoom * min(width, height))
    masked_earth = Image.open(earth_file)
    masked_earth.thumbnail((resize_size, resize_size), Image.Resampling.LANCZOS)
    wallpaper = Image.new("RGBA", (width, height), color="black")

    # get astro data
    observed_stars, observed_constellations = skyfield_wallpaper.stereographic_projection(current_date, width, height, fov)

    # draw dots for stars
    draw = ImageDraw.Draw(wallpaper)
    for _, star in observed_stars.iterrows():
        s = star.s * stars_scaling  # max star radius
        draw.ellipse((star.x - s, star.y - s, star.x + s, star.y + s), fill="white", outline="white")

    # draw lines for constellations
    constellation_alpha = int(constellation_alpha * 255)
    constellation_overlay = Image.new("RGBA", wallpaper.size)
    constellation_overlay_draw = ImageDraw.Draw(constellation_overlay)
    for p1, p2 in observed_constellations:
        constellation_overlay_draw.line((*p1, *p2), width=1, fill=(255, 255, 255, constellation_alpha))
    wallpaper.alpha_composite(constellation_overlay)

    # add earth to center
    wallpaper.alpha_composite(
        masked_earth,
        (
            int((width - masked_earth.size[0]) / 2),
            int((height - masked_earth.size[1]) / 2),
        ),
    )
    return wallpaper


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="46.38.251.80", port=4026)
