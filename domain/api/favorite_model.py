

from typing import List
from pydantic import BaseModel


class FavoriteItem(BaseModel):
    USER_ID: str = None
    TYPE: str
    STATION_CODE: str
    STATION_NAME: str
    STATION_GROUP_CODE: str
    LINE_NAME: str
    LINE_NAME_WITH_EMOJI: str
    LINE_CODE: str
    coordinates: List[float]

class FavoritePostRequest(BaseModel):
    item: FavoriteItem

class FavoriteDeleteRequest(BaseModel):
    type: str
    station_code: str