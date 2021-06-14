from datetime import datetime, timezone
from typing import List
from tzlocal import get_localzone


def parse_time_stamp(t) -> datetime:
    return datetime.fromtimestamp(t)


def to_time_utc_iso(dt: datetime) -> str:
    local_tz = get_localzone()
    t = dt.replace(tzinfo=local_tz)
    return t.isoformat()
