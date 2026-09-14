from pathlib import Path
import time

from data.database import db
from data.nba_api.models.teams import get_teams
from data.nba_api.models.players import get_players
from data.nba_api.models.season_stats import get_player_season_stats
from data.nba_api.models.draft_history import get_draft_history
from data.nba_api.models.rosters import get_roster, get_coaches, fetch_team_roster_data
from data.nba_api.models.awards import get_player_awards

NBA_SCHEMA_PATH = Path(__file__).parent / "nba_api" / "schema.sql"
AUTH_SCHEMA_PATH = Path(__file__).parent / "accounts" / "auth_schema.sql"


def load_schema(schema_path: Path):
    with open(schema_path, "r") as f:
        schema = f.read()

    cursor = db.connection.cursor()
    cursor.execute(schema)
    db.connection.commit()
    cursor.close()
    print(f"Schema loaded: {schema_path.name}")


def generate_seasons(start_year: int = 1960, end_year: int = 2025) -> list[str]:
    return [f"{year}-{str(year + 1)[-2:]}" for year in range(start_year, end_year + 1)]


def remove_unknown_players(data: list, valid_player_ids: set, player_id_field: str) -> list:
    return [entry for entry in data if getattr(entry, player_id_field) in valid_player_ids]


def qualifying_players() -> set[int]:
    cursor = db.connection.cursor()
    cursor.execute("""
    SELECT players.player_id, players.player_name
    FROM players
    INNER JOIN season_stats ON players.player_id = season_stats.player_id
    GROUP BY players.player_id, players.player_name
    HAVING SUM(games_played) >= 100 AND SUM(pts) / SUM(games_played) > 5
    """)
    player_ids = {row[0] for row in cursor.fetchall()}
    cursor.close()
    return player_ids


def load_nba_data():
    teams = get_teams()
    db.load_data("teams", teams)
    print(f"Loaded {len(teams)} teams.")

    valid_team_ids = {t.team_id for t in teams}

    players = get_players()
    db.load_data("players", players)
    print(f"Loaded {len(players)} players.")

    valid_player_ids = {p.player_id for p in players}

    season_stats = []
    skipped_players = []
    for player in players:
        try:
            stats = get_player_season_stats(player.player_id)
        except Exception as e:
            print(f"Skipping player {player.player_id}: {e}")
            skipped_players.append(player.player_id)
            time.sleep(0.3)
            continue

        for stat in stats:
            stat.season_start_year = int(stat.season[:4])

        season_stats.extend(stats)
        print(f"Loaded season stats for player {player.player_id}")
        time.sleep(0.3)

    if skipped_players:
        print(f"Skipped {len(skipped_players)} players due to errors: {skipped_players}")

    season_stats = [s for s in season_stats if s.team_id in valid_team_ids]

    db.load_data("season_stats", season_stats)

    rosters = []
    coaches = []
    for season in generate_seasons():
        for team_id in valid_team_ids:
            data = fetch_team_roster_data(team_id, season)

            season_rosters = get_roster(data)
            for r in season_rosters:
                r.season_start_year = int(r.season)
            rosters.extend(season_rosters)

            coaches.extend(get_coaches(data))
            print(f"Loaded roster for team {team_id} in {season}")
            time.sleep(0.3)

    rosters = remove_unknown_players(rosters, valid_player_ids, "player_id")
    db.load_data("rosters", rosters)

    db.load_data("coaches", coaches)

    draft_history = get_draft_history()

    for entry in draft_history:
        if entry.team_id not in valid_team_ids:
            entry.team_id = None

    draft_history = remove_unknown_players(draft_history, valid_player_ids, "player_id")
    db.load_data("draft_history", draft_history)
    print(f"Loaded {len(draft_history)} draft history entries.")

    qualifying_player_ids = qualifying_players()

    awards = []
    for player_id in qualifying_player_ids:
        awards.extend(get_player_awards(player_id))
        print(f"Loaded awards for player {player_id}")
        time.sleep(0.3)

    db.load_data("awards", awards)


def main():
    db.ensure_connected()

    load_schema(NBA_SCHEMA_PATH)
    load_schema(AUTH_SCHEMA_PATH)

    load_nba_data()

    db.close()


if __name__ == "__main__":
    main()