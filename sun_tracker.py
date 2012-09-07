from heliostat import Controller
import datetime
import time

#               Time     Az   El
jeffs_data = [ ['09:08', 135, 56],
               ['09:30', 137, 57],
               ['10:00', 141, 60],
               ['10:30', 144, 63],
               ['11:00', 148, 65],
               ['11:30', 152, 68],
               ['12:00', 157, 70],
               ['12:30', 163, 72],
               ['13:00', 169, 73],
               ['13:30', 178, 74],
               ['14:00', 186, 74],
               ['14:30', 196, 73],
               ['15:00', 208, 71],
               ['15:30', 213, 70],
               ['16:00', 219, 68],
               ['16:30', 225, 66],
               ['17:00', 228, 63] ]

def time_from_string(str):
    hr, mn = [int(val) for val in str.split(':')]
    time = datetime.time(hour=hr, minute=mn)
    return time

# Convert times from strinsg to time objects.
for datum in jeffs_data:
    datum[0] = time_from_string(datum[0])

# Find starting position in data.
cur_dt = datetime.datetime.now()
cur_time = cur_dt.time()

if cur_time < jeffs_data[0][0] or cur_time > jeffs_data[-1][0]:
    start_idx = 0
else:
    for start_idx in range(len(jeffs_data)):
        if cur_time <= datum[0][0]:
            break

for idx in range(start_idx, len(jeffs_data)):
    next_time = jeffs_data[idx][0]
    sleep_time = next_time - cur_time
    print sleep_time
    time.sleep(sleep_time)

