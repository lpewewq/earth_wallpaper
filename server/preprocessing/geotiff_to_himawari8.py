from multiprocessing import Pool

import numpy as np
from geotiff import GeoTiff
from PIL import Image, ImageFilter
from pyresample import AreaDefinition

# https://neo.gsfc.nasa.gov/archive/blackmarble/2016/
# https://visibleearth.nasa.gov/grid.php

width = 11000
height = 11000
Image.MAX_IMAGE_PIXELS = 11e3 ** 2

# Himawari-8 projection
area = AreaDefinition(
    area_id="FLDK",
    description="AHI FLDK area",
    proj_id="geosh8",
    projection={
        "a": "6378137",
        "h": "35785863",
        "lon_0": "140.7",
        "no_defs": "None",
        "proj": "geos",
        "rf": "298.257024882273",
        "type": "crs",
        "units": "m",
        "x_0": "0",
        "y_0": "0",
    },
    width=width,
    height=height,
    area_extent=(-5499999.9684, -5499999.9684, 5499999.9684, 5499999.9684),
)
lons, lats = area.get_lonlats()
blur_filter = ImageFilter.GaussianBlur(radius=5)


def build_partial_image(file):
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    geo_tiff = GeoTiff(file)
    black_marble_image = Image.fromarray(np.array(geo_tiff.read()))
    black_marble_image = black_marble_image.filter(blur_filter)

    (lon_min, lat_max), (lon_max, lat_min) = geo_tiff.tif_bBox_wgs_84
    for y in range(height):
        for x in range(width):
            lon = lons[y][x]
            lat = lats[y][x]
            if np.isinf(lon) or np.isinf(lat):
                continue
            if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
                geo_tiff_x = geo_tiff._get_x_int(lon)
                geo_tiff_y = geo_tiff._get_y_int(lat)
                xy = (geo_tiff_x, geo_tiff_y)
                r, g, b = black_marble_image.getpixel(xy)
                image.putpixel((x, y), (r, g, b, 255))

    result_file = file + ".png"
    image.save(result_file)
    print("Saved", result_file)
    return result_file


results = Pool(processes=4).map(
    build_partial_image,
    [
        "BlackMarble_2016_A1_geo.tif",
        "BlackMarble_2016_A2_geo.tif",
        "BlackMarble_2016_C1_geo.tif",
        "BlackMarble_2016_C2_geo.tif",
        "BlackMarble_2016_D1_geo.tif",
        "BlackMarble_2016_D2_geo.tif",
    ],
    chunksize=1,
)


print("Compose result image...")
result_image = Image.open(results[0])
for res in results[1:]:
    result_image.alpha_composite(Image.open(res))
result_image.save("BlackMarble_2016_Himawari8.png")
