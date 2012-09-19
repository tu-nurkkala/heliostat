from __future__ import division

import datetime
import time

from astral import City

from heliostat import Controller, MockController
from heliostat import AZIMUTH_MIN, AZIMUTH_MAX, ELEVATION_MIN, ELEVATION_MAX
from util import clamp

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
    # ELEVATION_FUDGE_FACTOR = -1
    # AZIMUTH_FUDGE_FACTOR = -13
    ELEVATION_FUDGE_FACTOR = 0
    AZIMUTH_FUDGE_FACTOR = 0

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

            azimuth = azimuth + azimuth_adjust + EmpiricalSolarFinder.AZIMUTH_FUDGE_FACTOR
            elevation = elevation + elevation_adjust + EmpiricalSolarFinder.ELEVATION_FUDGE_FACTOR

        return (azimuth, elevation)

class AstralSolarFinder(object):
    """Finder using the Python Astral package."""
    def __init__(self, location):
        logger.debug("Location %s", location)
        self.location = location
        
    def find(self, when):
        def mirror_elevation(solar_elevation):
            """Convert solar elevation to the elevation value for the mirror."""
            return 90 - ((90 - solar_elevation) / 2)

        when = when.replace(tzinfo=self.location.tz)
        true_azimuth = int(self.location.solar_azimuth(when))
        azimuth = clamp(true_azimuth, AZIMUTH_MIN, AZIMUTH_MAX)

        true_elevation = int(self.location.solar_elevation(when))
        elevation = clamp(int(mirror_elevation(true_elevation)), ELEVATION_MIN, ELEVATION_MAX)

        msge = [ ]
        msge.append("AZ {0:d}".format(azimuth))
        if true_azimuth != azimuth:
            msge.append(" ({0:d} true)".format(true_azimuth))
        msge.append(" EL {0:d}".format(elevation))
        if true_elevation != elevation:
            msge.append(" ({0:d} true)".format(true_elevation))
        logger.debug("".join(msge))

        return (azimuth, elevation)
