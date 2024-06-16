import datetime


def is_valid_date(date_text: str) -> bool:
    try:
        datetime.date.fromisoformat(date_text)
    except ValueError:
        return False
    return True
