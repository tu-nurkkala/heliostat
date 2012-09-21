# -*- coding: utf-8 -*-

from astral import City
from collections import defaultdict
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

DELTA_MINUTES = 1
MODE='Delta'

def average_value_by_key(which, dd):
    av_d = { }
    for key, val in dd.items():
        av_d[key] = sum(val) / len(val)

    for key in sorted(av_d.keys()):
        print "{0},{1},{2}".format(which, key, av_d[key])

def compare_finders():
    az_correction = defaultdict(list)
    el_correction = defaultdict(list)
    
    empirical = EmpiricalSolarFinder(jeffs_data)
    upland = City(("Upland", "USA", "40°28'N", "85°30'W", "US/Eastern"))
    astral = AstralSolarFinder(upland)

    delta = datetime.timedelta(minutes=DELTA_MINUTES)
    from_time = datetime.datetime(2012, 8, 21, 9, 0, tzinfo=upland.tz)
    to_time = datetime.datetime(2012, 8, 21, 17, 0, tzinfo=upland.tz)
    sunrise = upland.sunrise(from_time)
    sunset = upland.sunset(from_time)
    when = from_time
    while when <= to_time:
        day_night = 'DAY' if sunrise < when < sunset else 'NIGHT'
        empirical_az, empirical_el = empirical.find(when)
        astral_az, astral_el = astral.find(when)
        if MODE == 'Full':
            print "{0:%H:%M},'EMPIRICAL',{1},{2},'ASTRAL',{3},{4},'DELTA',{5},{6},'{7}'".format(
                when,
                empirical_az, empirical_el,
                astral_az, astral_el,
                empirical_az - astral_az, empirical_el - astral_el,
                day_night)
        elif MODE == 'Delta':
            # print "{0},{1},{2},{3}".format(astral_az, empirical_az, astral_el, empirical_el)
            az_correction[astral_az].append(empirical_az)
            el_correction[astral_el].append(empirical_el)
        else:
            raise ValueException()

        when += delta

    if MODE == 'Delta':
        average_value_by_key('AZ', az_correction)
        average_value_by_key('EL', el_correction)

compare_finders()

