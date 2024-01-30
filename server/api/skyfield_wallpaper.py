from skyfield.data import hipparcos, stellarium
from skyfield.api import Star, load, utc
from skyfield.projections import build_stereographic_projection
import numpy as np


class SkyFieldWallpaper:
    himawari_9_tle_url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR=41836"
    # TODO: 404 constellation file
    # constellations_url = (
    #     "https://raw.githubusercontent.com/Stellarium/stellarium/master" "/skycultures/western_SnT/constellationship.fab"
    # ) 

    def __init__(self):
        self.ts = load.timescale()

        # load ephemeris data
        self.eph = load("de421.bsp")

        # load and filter stars
        limiting_magnitude = 7.0
        with load.open(hipparcos.URL) as f:
            self.stars = hipparcos.load_dataframe(f)
            self.stars = self.stars[self.stars.magnitude <= limiting_magnitude]
            self.stars["s"] = (0.5 + limiting_magnitude - self.stars.magnitude) ** 2.0 / (
                0.5 + limiting_magnitude - self.stars.magnitude.min()
            ) ** 2.0

        # load constellations data
        # with load.open(self.constellations_url) as f:
        #     constellations = stellarium.parse_constellations(f)
        # self.constellation_edges = [edge for _, edges in constellations for edge in edges]

        # load himawari tle
        self.satellite = self.load_himawari_tle()

    def load_himawari_tle(self):
        reload = not hasattr(self, "satellite") or self.satellite is None or abs(self.satellite.epoch - self.ts.now()) > 14
        print("Load himawari TLE file, reload =", reload)
        data = load.tle_file(self.himawari_9_tle_url, filename="himawari-9.txt", reload=reload)
        if len(data) > 0:
            return data[0]
        else:
            print("Could not load himawari TLE file")
            return None

    def stereographic_projection(self, datetime, width, height, fov):
        if self.satellite is None or self.stars is None:
            return []

        earth = self.eph["earth"]
        t = self.ts.from_datetime(datetime.replace(tzinfo=utc))

        # center earth
        satellite_position = (earth + self.satellite).at(t)
        center = satellite_position.observe(earth)
        projection = build_stereographic_projection(center)

        # observe stars
        observed_stars = self.stars[["s"]].copy()
        star_positions = satellite_position.observe(Star.from_dataframe(self.stars))
        observed_stars["x"], observed_stars["y"] = projection(star_positions)

        # filter stars outside FOV
        angle = np.pi - fov / 360.0 * np.pi
        projection_limit = np.sin(angle) / (1.0 - np.cos(angle))
        aspect_ratio = height / width
        observed_stars = observed_stars[observed_stars.x.abs() <= projection_limit]
        observed_stars = observed_stars[observed_stars.y.abs() <= projection_limit * aspect_ratio]

        # scale to width/height and flip y axis
        max_dim = max(width, height)
        observed_stars.s *= max_dim * 0.0005  # max star radius in pixel
        observed_stars.x = max_dim * (observed_stars.x + projection_limit) / (2 * projection_limit)
        observed_stars.y = max_dim * (projection_limit - observed_stars.y) / (2 * projection_limit)

        # correct positions
        if width == max_dim:
            observed_stars.y -= (max_dim - height) / 2
        else:
            observed_stars.x -= (max_dim - width) / 2

        # constellations
        observed_constellations = []
        # observed_constellations = [
        #     (observed_stars[["x", "y"]].loc[e1].values, observed_stars[["x", "y"]].loc[e2].values)
        #     for e1, e2 in self.constellation_edges
        #     if e1 in observed_stars.index.values and e2 in observed_stars.index.values
        # ]

        return observed_stars, observed_constellations
