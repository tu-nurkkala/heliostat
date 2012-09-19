# -*- coding: utf-8 -*-

from astral import City
from solar_finders import AstralSolarFinder, EmpiricalSolarFinder
import datetime

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

def compare_finders():
    sun = EmpiricalSolarFinder(jeffs_data)
    upland = City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
    sol = AstralSolarFinder(upland)

    delta = datetime.timedelta(minutes=+5)
    from_time = datetime.datetime(2012, 8, 21, 9, 0, tzinfo=upland.tz)
    to_time = datetime.datetime(2012, 8, 21, 17, 0, tzinfo=upland.tz)
    sunrise = upland.sunrise(from_time)
    sunset = upland.sunset(from_time)
    when = from_time
    while when < to_time:
        day_night = 'DAY' if sunrise < when < sunset else 'NIGHT'
        sun_az, sun_el = sun.find(when)
        sol_az, sol_el = sol.find(when)
        print "{0:%H:%M},'SUN',{1},{2},'SOL',{3},{4},'DELTA',{5},{6},'{7}'".format(
            when,
            sun_az, sun_el,
            sol_az, sol_el,
            sun_az - sol_az, sun_el - sol_el,
            day_night)
        when += delta


compare_finders()

