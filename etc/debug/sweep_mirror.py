from heliostat import Controller, AZIMUTH_MIN, AZIMUTH_MAX, ELEVATION_MIN, ELEVATION_MAX
import argparse
import logging

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='Sweep mirror to determine magnetic variation')

parser.add_argument('--azmin', dest='azimuth_min', type=int, default=AZIMUTH_MIN, help='min azimuth')
parser.add_argument('--azmax', dest='azimuth_max', type=int, default=AZIMUTH_MAX, help='max azimuth')
parser.add_argument('--elmin', dest='elevation_min', type=int, default=ELEVATION_MIN, help='min elevation')
parser.add_argument('--elmax', dest='elevation_max', type=int, default=ELEVATION_MAX, help='max elevation')

args = parser.parse_args()

DEGREE_STEP = 3

try:
    controller = Controller()
    moving_up = True

    controller.azimuth(args.azimuth_min)
    controller.elevation(args.elevation_min)

    for azimuth in xrange(args.azimuth_min, args.azimuth_max, DEGREE_STEP):
        logger.info("*** MOVING AZIMUTH TO %d", azimuth)
        az, el = controller.azimuth(azimuth)

        if moving_up:
            elevation = args.elevation_max
        else:
            elevation = args.elevation_min

        logger.info("*** MOVING ELEVATION TO %d", elevation)
        az, el = controller.elevation(elevation)

        moving_up = not moving_up
            
except KeyboardInterrupt:
    print "\nCaught keyboard interrupt; sending stop comand."
    controller.stop()
finally:
    controller.report_stats()
