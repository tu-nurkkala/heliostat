from heliostat import AZIMUTH_MIN, AZIMUTH_MAX, ELEVATION_MIN, ELEVATION_MAX
import fileinput
import re

requested_az = None
requested_el = None

adjusting_el = False

az_offset = [ [ None for i in range(AZIMUTH_MAX + 1)] for j in range(ELEVATION_MAX + 1) ]

print len(az_offset)
print len(az_offset[0])

for line in fileinput.input():
    line = line.strip()

    m = re.search(r'MOVING AZIMUTH TO (?P<az>\d+)', line)
    if m:
        requested_az = int(m.group('az'))
        adjusting_el = False
        print 'REQ AZ', requested_az
        
    m = re.search(r'MOVING ELEVATION TO (?P<el>\d+)', line)
    if m:
        requested_el = int(m.group('el'))
        adjusting_el = True
        print 'REQ EL', requested_el

    if adjusting_el:
        m = re.search(r'DEBUG.*91\) AZ (?P<az>\d+) EL (?P<el>\d+)', line)
        if m:
            actual_az = int(m.group('az'))
            actual_el = int(m.group('el'))
            print 'ACT AZ', actual_az, 'ACT EL', actual_el
            az_offset[actual_el][requested_az] = actual_az - requested_az

print '  ',
moving_up = True
for j in xrange(AZIMUTH_MIN, AZIMUTH_MAX, 3):
    print ' UP' if moving_up else ' DN',
    moving_up = not moving_up
print

print '  ',
for az in xrange(AZIMUTH_MIN, AZIMUTH_MAX, 3):
    print '{:3d}'.format(az),
print

for el in xrange(ELEVATION_MIN, ELEVATION_MAX + 1):
    print el,
    for az in xrange(AZIMUTH_MIN, AZIMUTH_MAX + 1, 3):
        offset = az_offset[el][az]
        if offset is not None:
            print '{:3d}'.format(offset),
        else:
            print '   ',
    print

        
