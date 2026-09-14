import json

from nba_api.stats.endpoints import playercareerstats
from pydantic import BaseModel, Field


class SeasonStats(BaseModel):
    player_id: int = Field(alias="PLAYER_ID")
    team_id: int = Field(alias="TEAM_ID")
    season: str = Field(alias="SEASON_ID")
    season_start_year: int | None = None
    age: float | None = Field(default=None, alias="PLAYER_AGE")
    games_played: int | None = Field(default=None, alias="GP")
    minutes: float | None = Field(default=None, alias="MIN")
    fgm: float | None = Field(default=None, alias="FGM")
    fga: float | None = Field(default=None, alias="FGA")
    fg_pct: float | None = Field(default=None, alias="FG_PCT")
    fg3m: float | None = Field(default=None, alias="FG3M")
    fg3a: float | None = Field(default=None, alias="FG3A")
    fg3_pct: float | None = Field(default=None, alias="FG3_PCT")
    ftm: float | None = Field(default=None, alias="FTM")
    fta: float | None = Field(default=None, alias="FTA")
    ft_pct: float | None = Field(default=None, alias="FT_PCT")
    pts: float | None = Field(default=None, alias="PTS")
    oreb: float | None = Field(default=None, alias="OREB")
    dreb: float | None = Field(default=None, alias="DREB")
    reb: float | None = Field(default=None, alias="REB")
    ast: float | None = Field(default=None, alias="AST")
    tov: float | None = Field(default=None, alias="TOV")
    stl: float | None = Field(default=None, alias="STL")
    blk: float | None = Field(default=None, alias="BLK")


def get_player_season_stats(player_id: int) -> list[SeasonStats]:
    response = playercareerstats.PlayerCareerStats(
        player_id=player_id,
        timeout=10,
    )

    data = json.loads(response.get_json())
    result_sets = data.get("resultSets") or []

    result_set = next(
        (rs for rs in result_sets if rs.get("name") == "SeasonTotalsRegularSeason"),
        None,
    )
    if result_set is None:
        return []

    headers = result_set.get("headers", [])
    rows = result_set.get("rowSet", [])

    stats = [SeasonStats(**dict(zip(headers, row))) for row in rows]

    return [s for s in stats if int(s.season[:4]) >= 1960]