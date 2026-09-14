import json

from nba_api.stats.endpoints import drafthistory
from pydantic import BaseModel, Field


class DraftHistoryEntry(BaseModel):
    player_id: int = Field(alias="PERSON_ID")
    season: str = Field(alias="SEASON")
    round_number: int | None = Field(default=None, alias="ROUND_NUMBER")
    round_pick: int | None = Field(default=None, alias="ROUND_PICK")
    overall_pick: int | None = Field(default=None, alias="OVERALL_PICK")
    team_id: int | None = Field(default=None, alias="TEAM_ID")
    organization: str | None = Field(default=None, alias="ORGANIZATION")
    organization_type: str | None = Field(default=None, alias="ORGANIZATION_TYPE")


def get_draft_history() -> list[DraftHistoryEntry]:
    response = drafthistory.DraftHistory(
        league_id="00",
        timeout=10,
    )

    data = json.loads(response.get_json())
    result_sets = data.get("resultSets") or []

    if not result_sets:
        return []

    result_set = result_sets[0]
    headers = result_set.get("headers", [])
    rows = result_set.get("rowSet", [])

    entries = [DraftHistoryEntry(**dict(zip(headers, row))) for row in rows]
    return [e for e in entries if 1970 <= int(e.season)]


if __name__ == "__main__":
    draft_history = get_draft_history()
    for entry in draft_history:
        print(entry)