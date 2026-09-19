from datetime import date

from pydantic import BaseModel, Field


class DayPassConfigIn(BaseModel):
    day: date
    cap: float = Field(gt=0)
    enabled: bool = False
