import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = 11e3 ** 2

image = Image.open("BlackMarble_2016_Himawari8.png")
width, height = image.size
for y in range(height):
    print((100 * y) // height, "%")
    for x in range(width):
        r, g, b, a = image.getpixel((x, y))
        if a > 0:
            d_m = np.sqrt((2 * y / height - 1) ** 2 + (2 * x / width - 1) ** 2)
            d = 1 - (0.99 * d_m) ** 10
            l = max(r, g, b) / 255

            r = min(255, int(r * d * l))
            g = min(255, int(g * d * l))
            b = min(255, int(b * d * l))
            image.putpixel((x, y), (r, g, b, a))

image = image.resize((2160, 2160), Image.Resampling.LANCZOS)
image.save("BlackMarble_2016_Himawari8_preprocessed.png")
