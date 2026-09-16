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


def year_to_season(year: int) -> str:
    """Converts a plain 4-digit year (e.g. 1996) into NBA season format
    (e.g. "1996-97"), correctly handling the turn-of-century case
    (1999 -> "1999-00")."""
    return f"{year}-{str(year + 1)[-2:]}"


def remove_unknown_players(data: list, valid_player_ids: set, player_id_field: str) -> list:
    return [entry for entry in data if getattr(entry, player_id_field) in valid_player_ids]


def qualifying_season_stats(season_stats: list) -> list:
    """Keeps only individual season rows that clear the bar: 20+ games
    played and 5+ PPG for that specific season."""
    return [
        s for s in season_stats
        if s.games_played and s.games_played >= 20 and (s.pts or 0) / s.games_played >= 5
    ]


def load_teams_and_players():
    teams = get_teams()
    db.load_data("teams", teams)
    print(f"Loaded {len(teams)} teams.")

    players = get_players()
    db.load_data("players", players)
    print(f"Loaded {len(players)} players.")

    return teams, players


def load_season_stats(players, valid_team_ids) -> set[int]:
    """Loads season_stats, keeping only rows that clear the qualifying
    bar. Returns the set of player_ids with at least one surviving row,
    so rosters/draft_history/awards can be scoped to only those players."""
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

        season_stats.extend(stats)
        print(f"Loaded season stats for player {player.player_id}")
        time.sleep(0.3)

    if skipped_players:
        print(f"Skipped {len(skipped_players)} players due to errors: {skipped_players}")

    season_stats = [s for s in season_stats if s.team_id in valid_team_ids]
    season_stats = qualifying_season_stats(season_stats)

    db.load_data("season_stats", season_stats)

    return {s.player_id for s in season_stats}


def load_rosters_and_coaches(valid_team_ids, qualifying_player_ids):
    rosters = []
    coaches = []

    for year_str in generate_seasons():
        year = int(year_str[:4])
        season = year_to_season(year)

        for team_id in valid_team_ids:
            data = fetch_team_roster_data(team_id, year_str)

            season_rosters = get_roster(data)
            for r in season_rosters:
                r.season = season
            rosters.extend(season_rosters)

            season_coaches = get_coaches(data)
            for c in season_coaches:
                c.season = season
            coaches.extend(season_coaches)

            print(f"Loaded roster for team {team_id} in {season}")
            time.sleep(0.3)

    rosters = remove_unknown_players(rosters, qualifying_player_ids, "player_id")
    db.load_data("rosters", rosters)
    db.load_data("coaches", coaches)


def load_draft_history(valid_team_ids, qualifying_player_ids):
    draft_history = get_draft_history()

    for entry in draft_history:
        if entry.team_id not in valid_team_ids:
            entry.team_id = None
        entry.season = year_to_season(int(entry.season))

    draft_history = remove_unknown_players(draft_history, qualifying_player_ids, "player_id")
    db.load_data("draft_history", draft_history)
    print(f"Loaded {len(draft_history)} draft history entries.")


def load_awards(qualifying_player_ids):
    awards = []
    for player_id in qualifying_player_ids:
        awards.extend(get_player_awards(player_id))
        print(f"Loaded awards for player {player_id}")
        time.sleep(0.3)

    db.load_data("awards", awards)


def load_nba_data():
    teams, players = load_teams_and_players()
    valid_team_ids = {t.team_id for t in teams}

    qualifying_player_ids = load_season_stats(players, valid_team_ids)

    load_rosters_and_coaches(valid_team_ids, qualifying_player_ids)
    load_draft_history(valid_team_ids, qualifying_player_ids)
    load_awards(qualifying_player_ids)


def main():
    db.ensure_connected()

    load_schema(NBA_SCHEMA_PATH)
    load_schema(AUTH_SCHEMA_PATH)

    load_nba_data()

    db.close()


if __name__ == "__main__":
    main()