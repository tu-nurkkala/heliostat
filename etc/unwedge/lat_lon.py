# -*- coding: utf-8 -*-

from astral import Astral, City
import datetime

astral = Astral()
location = City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
print "LAT {0:.2f} LON {1:.2f}".format(location.latitude, location.longitude)

from_time = datetime.datetime(2012, 6, 21, 8, tzinfo=location.tz)
to_time = datetime.datetime(2012, 6, 21, 19, tzinfo=location.tz)
delta = datetime.timedelta(minutes=60)

when = from_time
while when < to_time:
    azimuth, elevation = (location.solar_azimuth(when),
                          location.solar_elevation(when))
    print "{0:%H:%M} AZ {1:5.2f} EL {2:5.2f}".format(when, azimuth, elevation)
    when += delta
