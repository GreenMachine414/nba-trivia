import json
from nba_api.stats.endpoints import playercareerstats

response = playercareerstats.PlayerCareerStats(
    player_id=203952,
    timeout=10,
)

data = json.loads(response.get_json())
result_sets = data.get("resultSets") or []

print(f"{len(result_sets)} result sets returned:")
for rs in result_sets:
    print(f"  - {rs.get('name')}: {len(rs.get('rowSet', []))} rows")

# Inspect the regular-season totals specifically
season_totals = next(
    (rs for rs in result_sets if rs.get("name") == "SeasonTotalsRegularSeason"),
    None,
)

if season_totals:
    headers = season_totals.get("headers", [])
    rows = season_totals.get("rowSet", [])
    print(f"\nSeasonTotalsRegularSeason headers: {headers}")
    for row in rows:
        print(dict(zip(headers, row)))
else:
    print("No SeasonTotalsRegularSeason result set found")