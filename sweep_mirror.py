from heliostat import Controller, AZIMUTH_MIN, AZIMUTH_MAX, ELEVATION_MIN, ELEVATION_MAX
import argparse

parser = argparse.ArgumentParser(description='Sweep mirror to determine magnetic variation')

parser.add_argument('--azmin', dest='azimuth_min', type=int, default=AZIMUTH_MIN, help='min azimuth')
parser.add_argument('--azmax', dest='azimuth_max', type=int, default=AZIMUTH_MAX, help='max azimuth')
parser.add_argument('--elmin', dest='elevation_min', type=int, default=ELEVATION_MIN, help='min elevation')
parser.add_argument('--elmax', dest='elevation_max', type=int, default=ELEVATION_MAX, help='max elevation')

args = parser.parse_args()

try:
    controller = Controller()
    moving_up = True

    for azimuth in xrange(args.azimuth_min, args.azimuth_max + 1):
        az, el = controller.azimuth(azimuth)
        print "AZ", az, el

        if moving_up:
            start, stop, step = args.elevation_min, args.elevation_max, 1
        else:
            start, stop, step = args.elevation_max, args.elevation_min, -1

        for elevation in xrange(start, stop, step):
            az, el = controller.elevation(elevation)
            print "EL", az, el

        moving_up = not moving_up
            
except KeyboardInterrupt:
    print "\nCaught keyboard interrupt; sending stop comand."
    controller.stop()
finally:
    controller.report_stats()
