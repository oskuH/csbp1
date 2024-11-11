from pythonjsonlogger.jsonlogger import JsonFormatter
from datetime import datetime, timezone

class UTCJsonFormatter(JsonFormatter):
    def formatTime(self, record, datefmt=None):
        return datetime.fromtimestamp(record.created, timezone.utc).isoformat()