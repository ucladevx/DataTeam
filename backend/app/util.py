from dateutil import parser
from .models import Interval
from pytz import timezone
import datetime, time, pytz



def convertDateToRFC3339(date):
    # Parse date into datetime object
    date_time = parser.parse(date)

    # Return RFC3339 date after switching to UTC format
    return date_time.astimezone(tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def convertDateTimeToRFC3339(date_time):
    return date_time.astimezone(tz=pytz.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

def duration(start, end):
    difference_seconds = (end - start).total_seconds()
    hours, leftover_seconds = divmod(difference_seconds, 3600)
    return float(hours) + float(leftover_seconds/3600)

def formulate_open_timeslots(events, current_date):
    time_slots = []
    local_timezone = timezone('US/Pacific')
    start_time = local_timezone.localize(datetime.datetime.combine(current_date, datetime.time(7, 0)))   # beginning of first interval is 7am day 1
    end_time = local_timezone.localize(datetime.datetime.combine(current_date + datetime.timedelta(days = 1), datetime.time(0, 0))) #end of first interval is beginning of next day
    curr_interval = (start_time, end_time)
    i = 1

    for event in events:
        event_start = parser.parse(event['start']['dateTime']).astimezone(local_timezone) #assume event time is PST timezone
        event_end = parser.parse(event['end']['dateTime']).astimezone(local_timezone) #assume event time is PST timezone

        if event_start > curr_interval[0]:
            new_interval = (event_end, curr_interval[1])
            changed_curr_interval = (curr_interval[0], event_start)
            time_slots.append(Interval(changed_curr_interval[0], changed_curr_interval[1], i, duration(changed_curr_interval[0], changed_curr_interval[1])))

            i += 1
            curr_interval = new_interval
        elif event_end > curr_interval[0]:
            new_interval = (event_end, curr_interval[1])
            curr_interval = new_interval

    time_slots.append(Interval(curr_interval[0], curr_interval[1], i, duration(curr_interval[0], curr_interval[1])))

    return time_slots
