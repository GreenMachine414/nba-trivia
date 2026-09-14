import json

from nba_api.stats.endpoints import commonallplayers
from pydantic import BaseModel, Field


class Player(BaseModel):
    player_id: int = Field(alias="PERSON_ID")
    player_name: str = Field(alias="DISPLAY_FIRST_LAST")
    from_year: int = Field(alias="FROM_YEAR")
    to_year: int = Field(alias="TO_YEAR")
    is_active: bool = Field(alias="ROSTERSTATUS")
    games_played_flag: str | None = Field(default=None, alias="GAMES_PLAYED_FLAG", exclude=True)


def get_players() -> list[Player]:
    response = commonallplayers.CommonAllPlayers(
        is_only_current_season=0,
        league_id="00",
        season="2025-26",
        timeout=10,
    )

    data = json.loads(response.get_json())
    result_sets = data.get("resultSets") or []

    if not result_sets:
        return []

    result_set = result_sets[0]
    headers = result_set.get("headers", [])
    rows = result_set.get("rowSet", [])

    players = [Player(**dict(zip(headers, row))) for row in rows]

    return [
        p for p in players
        if p.to_year >= 1960 and p.games_played_flag == "Y"
    ]