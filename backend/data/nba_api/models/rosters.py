import json

from nba_api.stats.endpoints import commonteamroster
from pydantic import BaseModel, Field, field_validator


class Roster(BaseModel):
    team_id: int = Field(alias="TeamID")
    season: str = Field(alias="SEASON")
    player_id: int = Field(alias="PLAYER_ID")
    jersey_number: str | None = Field(default=None, alias="NUM")
    position: str | None = Field(default=None, alias="POSITION")
    height: str | None = Field(default=None, alias="HEIGHT")
    weight: str | None = Field(default=None, alias="WEIGHT")
    age: float | None = Field(default=None, alias="AGE")

    @field_validator("jersey_number", mode="before")
    @classmethod
    def clean_jersey_number(cls, value):
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        if any(c.isspace() for c in value):
            return None
        return value

class Coach(BaseModel):
    team_id: int = Field(alias="TEAM_ID")
    season: str | None = Field(default=None, alias="SEASON")
    coach_id: int | None = Field(default=None, alias="COACH_ID")
    coach_name: str | None = Field(default=None, alias="COACH_NAME")
    coach_type: str | None = Field(default=None, alias="COACH_TYPE")


def fetch_team_roster_data(team_id: int, season: str) -> dict:
    response = commonteamroster.CommonTeamRoster(
        team_id=team_id,
        season=season,
        timeout=10,
    )
    return json.loads(response.get_json())


def get_roster(data: dict) -> list[Roster]:
    result_sets = data.get("resultSets") or []
    if not result_sets:
        return []

    player_set = result_sets[0]
    headers = player_set.get("headers", [])
    rows = player_set.get("rowSet", [])

    if not rows:
        return []

    return [Roster(**dict(zip(headers, row))) for row in rows]


def get_coaches(data: dict) -> list[Coach]:
    result_sets = data.get("resultSets") or []
    for result_set in result_sets:
        if result_set.get("name") == "Coaches":
            headers = result_set.get("headers", [])
            rows = result_set.get("rowSet", [])
            return [Coach(**dict(zip(headers, row))) for row in rows]
    return []