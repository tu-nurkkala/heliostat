# -*- coding: utf-8 -*-

from __future__ import division
from math import sin, asin, cos, acos, tan, degrees, radians, pi
import datetime

class SunFinder(object):
    def __init__(self, latitude_angle, month, day, solar_time):
        # Phi - Angle between a point on the earth's surface, the observer, and the
        # earth's equitorial plane. Simply the latitude of a given goegrphic position.
        self.latitude_angle = radians(latitude_angle)

        # t_s - Solar time of observer's location. A 24-hour clock depending on the
        # sun. When sun due south, solar time is 12:00.
        self.solar_time = solar_time

        self.month = month
        self.day = day

    @property
    def hour_angle(self):
        # Omega - Angle between the meridian plane of the observer and the meridian plan
        # that passes throught he sun. In the range [-180, 180] with zero at solar noon
        # (sun at highest point in the sky).
        return radians(15 * (self.solar_time - 12))

    @property
    def days_passed(self):
        # N - Days passed since January 1.
        today = datetime.date.today()
        today = datetime.date(year=today.year, month=self.month, day=self.day)
        jan1 = datetime.date(year=today.year, month=1, day=1)
        return (today - jan1).days

    @property
    def solar_declination(self):
        # Delta - Angle between the sun and the equatorial plane. Depends on the date.
        return asin(0.39795 * cos(radians(0.98563 * (self.days_passed - 173))))

    @property
    def elevation_radians(self):
        # Alpha - Elevation angle of the sun
        return asin((sin(self.solar_declination) *
                     sin(self.latitude_angle)) +
                    (cos(self.solar_declination) *
                     cos(self.hour_angle) *
                     cos(self.latitude_angle)))

    @property
    def azimuth1_radians(self):
        # A - Azimuth angle of the sun (first version)
        az = asin(- cos(self.solar_declination) *
                    sin(self.hour_angle) /
                    cos(self.elevation_radians))

        if cos(self.hour_angle) >= tan(self.solar_declination) / tan(self.latitude_angle):
            az = pi - az
        else:
            az = 2 * pi + az
        return az

    @property
    def azimuth2_radians(self):
        # A - Azimuth angle of the sun (second version)
        az = acos(((sin(self.solar_declination) *
                    cos(self.latitude_angle)) -
                   (cos(self.solar_declination) *
                    cos(self.hour_angle) *
                    sin(self.latitude_angle))) /
                  cos(self.elevation_radians))

        if sin(self.hour_angle) > 0:
            az = 2 * pi - az
        else:
            az = az
        return az

    @property
    def elevation(self):
        return degrees(self.elevation_radians)

    @property
    def mirror_elevation(self):
        return degrees((self.elevation_radians / 2) + (pi / 4))

    @property
    def azimuth1(self):
        return degrees(self.azimuth1_radians)

    @property
    def azimuth2(self):
        return degrees(self.azimuth2_radians)


sun = SunFinder(40.47, 7, 24, 12.00001)
print "AZ1", sun.azimuth1
print "AZ2", sun.azimuth2
print "EL ", sun.elevation
print "ELM", sun.mirror_elevation

import astral
upland = astral.City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
print upland

noon = upland.solar_noon(datetime.date(2012, 7, 24))
print noon
print "AZ", upland.solar_azimuth(noon)
print "EL", upland.solar_elevation(noon)
