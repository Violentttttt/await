from datetime import datetime
from dateutil import parser
from psycopg2.extras import DateTimeTZRange


def combine_date_time(date_str, time_str):
    if date_str and time_str:
        # Парсим строку даты и времени
        date_part = parser.isoparse(date_str).date()
        time_part = parser.isoparse(time_str).time()
        return datetime.combine(date_part, time_part)
    return None


def create_datetime_range(date_range_begin, date_range_end, time_range_begin, time_range_end):
    start = combine_date_time(date_range_begin, time_range_begin)
    end = combine_date_time(date_range_end, time_range_end)

    print("Start datetime:", start)
    print("End datetime:", end)

    # Возвращаем объект DateTimeTZRange вместо кортежа
    if start and end:
        return DateTimeTZRange(start, end)  # Возвращаем объект DateTimeTZRange
    return None
