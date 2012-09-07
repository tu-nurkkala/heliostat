#!/usr/bin/env python2

from heliostat import Controller, MockController
import datetime
import time

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
        if when < self.observations[0].time:
            return self.observations[0].position()
        elif when > self.observations[-1].time:
            return self.observations[-1].position()
        else:
            for idx in range(len(self.observations) - 1):
                if (when >= self.observations[idx].time and
                    when <= self.observations[idx + 1].time):
                    return self.observations[idx].position()
        raise RuntimeError("Should never get here")


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


controller = Controller()
cur_azimuth, cur_elevation = controller.stop()

sun = EmpiricalSolarFinder(jeffs_data)

while True:
    when = datetime.datetime.now().time()
    azimuth, elevation = sun.find(when)

    if cur_azimuth != azimuth:
        cur_azimuth = controller.azimuth(azimuth)

    if cur_elevation != elevation:
        cur_elevation = controller.elevation(elevation)

    time.sleep(60)


