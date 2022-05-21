from datetime import datetime
from enum import Enum
from io import BytesIO

import pytz
from fastapi import FastAPI, Query, Response, exceptions
from PIL import Image, ImageDraw, ImageFilter

from common import get_earth_path
from skyfield_wallpaper import SkyFieldWallpaper

Timezone = Enum("Timezone", ((x, x) for x in pytz.all_timezones))
Timezone.get_timezone = lambda self: pytz.timezone(self.value)
satellite_tz = Timezone("Asia/Jayapura")


app = FastAPI()
skyfield_wallpaper = SkyFieldWallpaper()


@app.get("/")
def earth_wallpaper(
    width: int = Query(..., gt=512, le=4096),
    height: int = Query(..., gt=512, le=4096),
    timezone: Timezone = Query(satellite_tz),
    zoom: float = Query(0.7, ge=0.0, le=1.0),
    fov: int = Query(70, ge=30, le=180),
    stars: float = Query(0.5, ge=0.0, le=1.0),
    constellations: float = Query(0.05, ge=0.0, le=1.0),
):
    # parse timezone offset
    local_now = datetime.now()
    dtime = datetime.utcnow()
    dtime -= satellite_tz.get_timezone().utcoffset(local_now) - timezone.get_timezone().utcoffset(local_now)

    # get earth file
    earth_file = get_earth_path(dtime)
    if not earth_file.exists():
        raise exceptions.HTTPException(404)

    # build entire wallpaper
    wallpaper = build_wallpaper(earth_file, width, height, zoom, dtime, fov, stars, constellations)
    image_data = BytesIO()
    wallpaper.save(image_data, format="png")
    return Response(image_data.getvalue(), media_type="image/png")


def build_wallpaper(
    earth_file,
    width: int,
    height: int,
    zoom: float,
    dtime: datetime,
    fov: int,
    stars_scaling: float,
    constellation_alpha: float,
):
    relative_size = min(width, height)
    masked_earth = Image.open(earth_file)
    earth_resized_size = int(zoom * relative_size)
    masked_earth.thumbnail((earth_resized_size, earth_resized_size), Image.Resampling.LANCZOS)
    wallpaper = Image.new("RGBA", (width, height), color="black")

    # get astro data
    observed_stars, observed_constellations = skyfield_wallpaper.stereographic_projection(dtime, width, height, fov)

    relative_star_size = int(relative_size / 300)

    # draw dots for stars
    draw = ImageDraw.Draw(wallpaper)
    for _, star in observed_stars.iterrows():
        s = star.s * stars_scaling * relative_star_size  # max star radius
        draw.ellipse((star.x - s, star.y - s, star.x + s, star.y + s), fill="white", outline="white")
    wallpaper = wallpaper.filter(ImageFilter.GaussianBlur(radius=1))

    # draw lines for constellations
    constellation_alpha = int(constellation_alpha * 255)
    constellation_overlay = Image.new("RGBA", wallpaper.size)
    constellation_overlay_draw = ImageDraw.Draw(constellation_overlay)
    for p1, p2 in observed_constellations:
        constellation_overlay_draw.line((*p1, *p2), width=relative_star_size, fill=(255, 255, 255, constellation_alpha))
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
