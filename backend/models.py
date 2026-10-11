from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Preference = Literal['greenery', 'scenic', 'fruit', 'water']
class Preferences(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    mode: Literal['walking', 'jogging'] = 'walking'
    minutes: int = Field(default=30, ge=10, le=120)
    preferences: list[Preference] = Field(default_factory=list, max_length=4)
    stop_minutes: int = Field(default=0, ge=0, le=30)

    @model_validator(mode='after')
    def check_budget(self):
        if self.stop_minutes >= self.minutes:
            raise ValueError('Stop time must be less than available minutes')
        self.preferences = list(dict.fromkeys(self.preferences))
        return self

class Point(BaseModel):
    model_config = ConfigDict(extra='forbid')
    lat: float = Field(ge=-85, le=85)
    lon: float = Field(ge=-180, le=180)

class RouteRequest(Preferences):
    start: Point

class ParseRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    current: Preferences
