# -*- coding: utf-8 -*-

import time
import astral

from heliostat import CompassController
from solar_finders import AstralSolarFinder, EmpiricalSolarFinder

import logging
logger = logging.getLogger(__name__)

SLEEP_TIME = 60                 # Sleep time in seconds

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

def mirror_elevation(solar_elevation):
    """Convert solar elevation to the elevation value for the mirror."""
    return 90 - ((90 - solar_elevation) / 2)

def track(controller, finder):
    cur_azimuth, cur_mirror_elevation = controller.stop()
    logger.info("Current AZ {0}, MEL {1}".format(cur_azimuth, cur_mirror_elevation))

    while True:
        azimuth, solar_elevation = controller.clamp_azimuth_elevation(*finder.find())
        logger.info("AZ %d SEL %d", azimuth, solar_elevation)
        new_mirror_elevation = mirror_elevation(solar_elevation)
        logger.info("AZ %d MEL %d", azimuth, new_mirror_elevation)
        
        if (cur_azimuth != azimuth or cur_mirror_elevation != new_mirror_elevation):
            logger.info("Sun moved to AZ {0}, SEL {1}".format(azimuth, solar_elevation))

            # Note that we are not updating our current position based
            # on the return value from the heliostat. Doing so causes
            # unnecessary movement of the mirror due to mapping the
            # string-pot azimuth back to a compass azimuth. Instead,
            # we assume the heliostat did the Right Thing.
            if cur_azimuth != azimuth:
                controller.azimuth(azimuth)
                cur_azimuth = azimuth

            if cur_mirror_elevation != new_mirror_elevation:
                controller.elevation(new_mirror_elevation)
                cur_mirror_elevation = new_mirror_elevation

        else:
            logger.info("Sun in same location.")

        logger.info("Sleeping %ds", SLEEP_TIME)
        time.sleep(SLEEP_TIME)


controller = CompassController()

upland = astral.Location(("Upland", "USA",
                          """40°27'22"N""",
                          """85°29'43"W""",
                          "US/Eastern"))

finder = AstralSolarFinder(upland)

try:
    track(controller, finder)
except KeyboardInterrupt:
    logger.warning("Caught keyboard interrupt; sending stop comand.")
    controller.stop()
finally:
    controller.report_stats()
