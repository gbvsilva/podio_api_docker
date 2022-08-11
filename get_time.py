import datetime
from os import environ as env
import time

TZ = datetime.timezone(datetime.timedelta(hours=int(env.get('TIMEZONE_OFFSET'))))

def getHour(**timedelta):
    if timedelta:
        hours = timedelta.get('hours', 0)
        minutes = timedelta.get('minutes', 0)
        seconds = timedelta.get('seconds', 0)
        microseconds = timedelta.get('microseconds', 0)
        offset = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
        return (datetime.datetime.now(TZ) + offset).strftime('%H:%M:%S')
    return datetime.datetime.now(TZ).strftime('%H:%M:%S')


def convert(seconds):
    hours = seconds // 3600
    seconds %= 3600
    mins = seconds // 60
    seconds %= 60
    return hours, mins, seconds

def timer(seconds):
    print('=== Temporizador ===')
    count = 0
    while count < seconds:
        hours, mins, secs = convert(count)
        timer = '{:02d}:{:02d}:{:02d}'.format(hours, mins, secs)
        print(timer, end='\r')
        time.sleep(1)
        count += 1
