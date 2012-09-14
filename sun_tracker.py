
# -*- coding: utf-8 -*-

from __future__ import division

import datetime
import time

import astral

from heliostat import Controller, MockController
from heliostat import AZIMUTH_MIN, AZIMUTH_MAX, ELEVATION_MIN, ELEVATION_MAX
from util import clamp

import logging
logger = logging.getLogger(__name__)

SLEEP_TIME = 60                 # Sleep time in seconds

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
    ELEVATION_FUDGE_FACTOR = -1
    AZIMUTH_FUDGE_FACTOR = -13

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

        logger.debug("At %s, AZ %d, EL %d", when, azimuth, elevation)
        return (azimuth, elevation)


## Data taken by Jeff Dailey, 21-Aug-2012.
jeffs_data = (
    ('09:08', 135, 56),         # Time, azimuth, elevation
    ('09:30', 137, 57),
    ('10:00', 141, 60),
    ('10:30', 144, 63),
    ('11:00', 148, 65),
    ('11:30', 152, 68),
    ('12:00', 157, 70),
    ('12:30', 163, 72),
    ('13:00', 169, 73),
    ('13:30', 178, 74),
    ('14:00', 186, 74),
    ('14:30', 196, 73),
    ('15:00', 208, 71),
    ('15:30', 213, 70),
    ('16:00', 219, 68),
    ('16:30', 225, 66),
    ('17:00', 228, 63) )


class AstralSolarFinder(object):
    """Finder using the Python Astral package."""
    def __init__(self, location, magnetic_declination):
        logger.debug("Location %s", location)
        self.location = location
        self.magnetic_declination = magnetic_declination
        
    def find(self, when):
        def mirror_elevation(solar_elevation):
            """Convert solar elevation to the elevation value for the mirror."""
            return solar_elevation / 2 + 45

        true_azimuth = int(self.location.solar_azimuth(when) + self.magnetic_declination)
        azimuth = clamp(true_azimuth, AZIMUTH_MIN, AZIMUTH_MAX)

        true_elevation = int(mirror_elevation(self.location.solar_elevation(when)))
        elevation = clamp(true_elevation, ELEVATION_MIN, ELEVATION_MAX)

        msge = [ ]
        msge.append("AZ {0:d}".format(azimuth))
        if true_azimuth != azimuth:
            msge.append(" ({0:d} true)".format(true_azimuth))
        msge.append(" EL {0:d}".format(elevation))
        if true_elevation != elevation:
            msge.append(" ({0:d} true)".format(true_elevation))
        logger.debug("".join(msge))

        return (azimuth, elevation)

def main(controller):
    sun = EmpiricalSolarFinder(jeffs_data)

    upland = astral.City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
    upland_magnetic_declination = 5.1059
    sol = AstralSolarFinder(upland, upland_magnetic_declination)

    cur_azimuth, cur_elevation = controller.stop()
    while True:
        when = datetime.datetime.now(tz=upland.tz)
        azimuth, elevation = sun.find(when.time())
        logger.debug("SUN AZ {0} EL {1}".format(azimuth, elevation))
        
        sol_azimuth, sol_elevation = sol.find(when)
        logger.debug("SOL AZ {0} EL {1}".format(sol_azimuth, sol_elevation))

        if (cur_azimuth != azimuth or cur_elevation != elevation):
            logger.info("Sun moved to AZ {0}, EL {1}".format(azimuth, elevation))

        if cur_azimuth != azimuth:
            cur_azimuth = controller.azimuth(azimuth)

        if cur_elevation != elevation:
            cur_elevation = controller.elevation(elevation)

        logger.debug("Sleeping %ds", SLEEP_TIME)
        time.sleep(SLEEP_TIME)

def compare_controllers():
    sun = EmpiricalSolarFinder(jeffs_data)
    upland = astral.City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
    upland_magnetic_declination = 5.1059
    sol = AstralSolarFinder(upland, upland_magnetic_declination)

    delta = datetime.timedelta(minutes=+5)
    from_time = datetime.datetime(2012, 8, 21, 0, 0, tzinfo=upland.tz)
    to_time = datetime.datetime(2012, 8, 22, 0, 0, tzinfo=upland.tz)
    sunrise = upland.sunrise(from_time)
    sunset = upland.sunset(from_time)
    when = from_time
    while when < to_time:
        day_night = 'DAY' if sunrise < when < sunset else 'NIGHT'
        sun_az, sun_el = sun.find(when.time())
        sol_az, sol_el = sol.find(when)
        print "{0:%I:%M} - SUN {1:3d} {2:2d} - SOL {3:3d} {4:2d} - DELTA {5:3d} {6:3d} - {7:5s}".format(
            when,
            sun_az, sun_el,
            sol_az, sol_el,
            sun_az - sol_az, sun_el - sol_el,
            day_night)
        when += delta

# compare_controllers()
# exit(1)

try:
    controller = Controller()
    main(controller)
except KeyboardInterrupt:
    logger.info("Caught keyboard interrupt; sending stop comand.")
    controller.stop()
finally:
    controller.report_stats()
