from __future__ import division

import datetime
import time

MAGNETIC_DECLINATION = 5.1      # Declination in degrees at Upland

from astral import City

import logging
logger = logging.getLogger(__name__)

class Observation(object):
    def __init__(self, time_str, azimuth, elevation):
        def time_from_string(str):
            hr, mn = [int(val) for val in str.split(':')]
            time = datetime.time(hour=hr, minute=mn)
            return time

        self.time = time_from_string(time_str)
        self.azimuth = azimuth
        self.elevation = elevation

    def position(self):
        return self.azimuth, self.elevation

class EmpiricalSolarFinder(object):
    def __init__(self, observations):
        self.observations = [Observation(*ob) for ob in observations]

    def find(self, when):

        def time_delta(t1, t2):
            """Caculate delta between two time objects in seconds. Because
            these don't support subtraction directly, convert to datetime
            objects first.
            """
            today = datetime.date.today()
            dt1 = datetime.datetime.combine(today, t1)
            dt2 = datetime.datetime.combine(today, t2)
            return (dt2 - dt1).total_seconds()

        azimuth_adjust = elevation_adjust = 0
        when = when.time()      # We only need the time for this finder

        if when < self.observations[0].time or when > self.observations[-1].time:
            azimuth, elevation = self.observations[0].position()
        else:
            for idx in range(len(self.observations) - 1):
                low, high = self.observations[idx], self.observations[idx + 1]
                if (when >= low.time and when <= high.time):
                    # Interpolate values between samples.
                    low_to_high = time_delta(low.time, high.time)
                    low_to_when = time_delta(low.time, when)
                    if low_to_high == 0:
                        fraction = 0.0
                    else:
                        fraction = low_to_when / low_to_high
                    azimuth_adjust = int((high.azimuth - low.azimuth) * fraction)
                    elevation_adjust = int((high.elevation - low.elevation) * fraction)

                    azimuth, elevation = self.observations[idx].position()

            azimuth = azimuth + azimuth_adjust
            elevation = elevation + elevation_adjust

        return (azimuth, elevation)

class AstralSolarFinder(object):
    """Finder using the Python Astral package."""
    def __init__(self, location):
        logger.info("Location %s", location)
        self.location = location

    def find(self, when):
        def mirror_elevation(solar_elevation):
            """Convert solar elevation to the elevation value for the mirror."""
            return 90 - ((90 - solar_elevation) / 2)

        def minutes_since_start(when):
            """Return the number of minutes from the start time (09:00) until time when."""
            first_sample = when.replace(hour=9, minute=0)
            delta_seconds = (when - first_sample).total_seconds()
            return delta_seconds / 60

        def azimuth_correction(when):
            """Return the azimuth correction at time when.  This is a
            piecewise linear apporoximation based on Jeff's data.
            """
            minutes = minutes_since_start(when)
            if minutes > 300:
                minutes -= 300
                m = -(4/180)
                b = -29
            else:
                m = -(65/480)
                b = 32

            return m * minutes + b
            
        def elevation_correction(when):
            """Return the elevation correction at time when. Also based on Jeff's data."""
            m = (12/480)
            b = -7
            return m * minutes_since_start(when) + b

        when = when.replace(tzinfo=self.location.tz)
        azimuth = int(self.location.solar_azimuth(when) + azimuth_correction(when) + MAGNETIC_DECLINATION)
        elevation = int(mirror_elevation(self.location.solar_elevation(when)) + elevation_correction(when))
        return (azimuth, elevation)
