from datetime import date, datetime, timedelta

import exchange_calendars as xcals

NSE_CALENDAR = xcals.get_calendar("XNSE")


def is_trading_minute(ts: datetime) -> bool:
    return NSE_CALENDAR.is_open_on_minute(ts)


def is_holiday(day: date) -> bool:
    return not NSE_CALENDAR.is_session(day)


def is_weekly_expiry(day: date) -> bool:
    return day.weekday() == 3 and NSE_CALENDAR.is_session(day)


def is_monthly_expiry(day: date) -> bool:
    if day.weekday() != 3 or not NSE_CALENDAR.is_session(day):
        return False
    nxt = day + timedelta(days=7)
    return nxt.month != day.month
