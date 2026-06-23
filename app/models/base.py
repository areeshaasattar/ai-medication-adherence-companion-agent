from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase

def get_utc_now():
    return datetime.now(timezone.utc)

class Base(DeclarativeBase):
    pass
