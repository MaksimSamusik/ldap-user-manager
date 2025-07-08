from datetime import datetime, timedelta


def nt_time_to_datetime(nt_time: int) -> datetime:
    windows_epoch = datetime(1601, 1, 1)
    return windows_epoch + timedelta(microseconds=nt_time // 10)

def filetime_to_datetime(filetime):
    if filetime in (0, 9223372036854775807):
        return None
    epoch = datetime(1601, 1, 1)
    return epoch + timedelta(microseconds=int(filetime)//10)

def get_current_filetime():
    delta = datetime.now() - datetime(1601, 1, 1)
    return int(delta.total_seconds() * 10**7)


def format_iso_time(iso_time: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_time.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except (ValueError, AttributeError):
        return "Incorrect time format"