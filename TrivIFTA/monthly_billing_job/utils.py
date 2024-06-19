from typing import List
from dateutil.parser import parse
import calendar

def last_day_of_month(year: int, month: int) -> int:
    '''
    Retrieves the last day of the month for the given year and month
    '''
    # calendar.monthrange returns a tuple (first_weekday, number_of_days)
    _, last_day = calendar.monthrange(year, month)
    return last_day