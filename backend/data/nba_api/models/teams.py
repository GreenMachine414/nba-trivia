from nba_api.stats.static import teams
from pydantic import BaseModel, Field


class Team(BaseModel):
    team_id: int = Field(alias="id")
    full_name: str = Field(alias="full_name")
    abbreviation: str = Field(alias="abbreviation")
    city: str = Field(alias="city")
    state: str = Field(alias="state")
    year_founded: int = Field(alias="year_founded")


def get_teams() -> list[Team]:
    all_teams = teams.get_teams()
    return [Team(**t) for t in all_teams]