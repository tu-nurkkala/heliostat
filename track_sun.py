# -*- coding: utf-8 -*-

import datetime
import time

from astral import City

from heliostat import Controller, clamp_azimuth_elevation
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

def track(controller, finder):
    cur_azimuth, cur_elevation = controller.stop()
    while True:
        location = City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
        when = datetime.datetime.now(tz=location.tz)
        azimuth, elevation = clamp_azimuth_elevation(*finder.find(when))
        logger.debug("Current AZ {0} EL {1}".format(azimuth, elevation))
        
        if (cur_azimuth != azimuth or cur_elevation != elevation):
            logger.info("Sun moved to AZ {0}, EL {1}".format(azimuth, elevation))

        if cur_azimuth != azimuth:
            cur_azimuth = controller.azimuth(azimuth)

        if cur_elevation != elevation:
            cur_elevation = controller.elevation(elevation)

        logger.debug("Sleeping %ds", SLEEP_TIME)
        time.sleep(SLEEP_TIME)

import argparse
parser = argparse.ArgumentParser(description='Track the sun')
parser.set_defaults(finder='analytic')

parser.add_argument('--empirical', action='store_const', const='empirical', dest='finder',
                    help='use empirical solar finder')
parser.add_argument('--analytical', action='store_const', const='analytic', dest='finder',
                    help='use analytic solar finder')
args = parser.parse_args()

controller = Controller()

if args.finder == 'analytic':
    upland = City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
    finder = AstralSolarFinder(upland)
elif args.finder == 'empirical':
    finder = EmpiricalSolarFinder(jeffs_data)
else:
    raise ValueError("Invalid finder '%s'", args.finder)

try:
    track(controller, finder)
except KeyboardInterrupt:
    logger.info("Caught keyboard interrupt; sending stop comand.")
    controller.stop()
finally:
    controller.report_stats()
