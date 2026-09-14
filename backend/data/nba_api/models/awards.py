import json

from nba_api.stats.endpoints import playerawards
from pydantic import BaseModel, Field


class PlayerAward(BaseModel):
    player_id: int = Field(alias="PERSON_ID")
    season: str | None = Field(default=None, alias="SEASON")
    description: str = Field(alias="DESCRIPTION")


def get_player_awards(player_id: int) -> list[PlayerAward]:
    response = playerawards.PlayerAwards(
        player_id=player_id,
        timeout=10,
    )

    data = json.loads(response.get_json())
    result_sets = data.get("resultSets") or []

    if not result_sets:
        return []

    result_set = result_sets[0]
    headers = result_set.get("headers", [])
    rows = result_set.get("rowSet", [])

    return [PlayerAward(**dict(zip(headers, row))) for row in rows]
