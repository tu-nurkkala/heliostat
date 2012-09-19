# -*- coding: utf-8 -*-

from solar_finders import AstralSolarFinder, EmpiricalSolarFinder

def compare_controllers():
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


compare_controllers()

