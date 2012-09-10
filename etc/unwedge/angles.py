
from math import sin, asin, cos, acos, tan, degrees, radians, pi
import datetime

# Phi - Angle between a point on the earth's surface, the observer, and the earth's
# equitorial plane. Simply the latitude of a given goegrphic position.
latitude_angle = radians(40.456)
print "latitude_angle", latitude_angle

# t_s - Solar timeof observer's location. A 24-hour clock depending on the sun. When sun
# due south, solar time is 12:00.
solar_time = 11.192

# Omega - Angle between the meridian plane of the observer and the meridian plan that
# passes throught he sun. In the range [-180, 180] with zero at solar noon (sun at highest
# point in the sky).
hour_angle = radians(15 * (solar_time - 12))
print "hour_angle", hour_angle

# N - Days passed since January 1.
today = datetime.date.today()
jan1 = datetime.date(year=today.year, month=1, day=1)
days_passed = (today - jan1).days
days_passed = 205               # Testing

# Delta - Angle between the sun and the equatorial plane. Depends on the date.
solar_declination = asin(0.39795 * cos(radians(0.98563 * (days_passed - 173))))
print 'solar_declination', solar_declination

print

# Alpha - Elevation angle of the sun
elevation = asin((sin(solar_declination) * sin(latitude_angle)) +
                 (cos(solar_declination) * cos(hour_angle) * cos(latitude_angle)))
print "elevation", degrees(elevation)

print

# A - Azimuth angle of the sun
azimuth1 = asin(- cos(solar_declination) * sin(hour_angle) / cos(elevation))
print "azimuth1", degrees(azimuth1)

a1_2 = cos(hour_angle) - (tan(solar_declination) / tan(latitude_angle))
print "a1_2", a1_2

a1_3 = 180 - degrees(azimuth1)
print "a1_3", a1_3

if cos(hour_angle) >= tan(solar_declination) / tan(latitude_angle):
    azimuth1 = pi - azimuth1
else:
    azimuth1 = 2 * pi + azimuth1
print "azimuth1", degrees(azimuth1)

print

azimuth2 = acos(((sin(solar_declination) * cos(latitude_angle)) -
                 (cos(solar_declination) * cos(hour_angle) * sin(latitude_angle))) / cos(elevation))
print "azimuth2", degrees(azimuth2)

a2_2 = sin(hour_angle)
print "a2_2", a2_2

a2_3 = degrees(azimuth2)
print "a2_3", a2_3

if sin(hour_angle) > 0:
    azimuth2 = 2 * pi - azimuth2
else:
    azimuth2 = azimuth2
print "azimuth2", degrees(azimuth2)
