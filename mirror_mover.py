#!/usr/bin/env python2

from heliostat import Controller, SPEED_NORMAL
import argparse

parser = argparse.ArgumentParser(description='Mirror mover utility')

parser.add_argument('--azimuth', dest='azimuth', type=int, help='rotate to new azimuth')
parser.add_argument('--elevation', dest='elevation', type=int, help='tip to new elevation')
parser.add_argument('--stop', dest='stop', action='store_true', help='send stop command')
parser.add_argument('--speed', dest='speed', type=int, default=SPEED_NORMAL, help='set speed')

args = parser.parse_args()

controller = Controller()

if args.stop:
    # If the user asks for stop, just stop and be done.
    controller.stop()
else:
    if args.azimuth is not None:
        controller.azimuth(args.azimuth, args.speed)
    if args.elevation is not None:
        controller.elevation(args.elevation, args.speed)

controller.report_stats()


