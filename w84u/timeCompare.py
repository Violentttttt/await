from psycopg2.extras import DateTimeRange
from django.utils.dateparse import parse_datetime
from datetime import datetime
from psycopg2.extras import DateTimeTZRange
from dateutil import parser


#ЭТО ДЛЯ СОХРАНЕНИЯ ВРЕМЕНИ


def combine_date_time(date_str, time_str):
    if date_str and time_str:
        date_part = parser.isoparse(date_str)
        time_part = parser.isoparse(time_str)
        return datetime.combine(date_part, time_part.time())
    return None


def create_datetime_range(date_range_begin, date_range_end, time_range_begin, time_range_end):
    start = combine_date_time(date_range_begin, time_range_begin)
    end = combine_date_time(date_range_end, time_range_end)
    print("Start datetime:", start)
    print("End datetime:", end)
    if start and end:
        return DateTimeTZRange(start, end)
    return None