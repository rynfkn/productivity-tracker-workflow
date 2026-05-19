import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


class TimezoneFormatter(logging.Formatter):
    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        dt = datetime.fromtimestamp(record.created, ZoneInfo(settings.SCHEDULER_TIMEZONE))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat(timespec="milliseconds")


def setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        TimezoneFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
