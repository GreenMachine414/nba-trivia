import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db
from trivia.engine import hash_answer

router = APIRouter()

METRIC_KEYS = [
    "position", "height", "team", "season", "college", "overall_pick",
    "ppg", "rpg", "apg", "bpg", "spg", "awards", "trend",
]

ROUND_REVEAL_COUNTS = [5, 7, 9, 11, 13]

TREND_STAT_COLUMNS = {
    "pts": "games_played",
    "reb": "games_played",
    "ast": "games_played",
}


class TrendPoint(BaseModel):
    season: str
    value: float


class GuessPlayerStart(BaseModel):
    metrics: dict
    trend: list[TrendPoint]
    reveal_order: list[str]
    round_reveal_counts: list[int]
    answer_hash: str


class SearchResult(BaseModel):
    names: list[str]


@router.get("/guess-player/start", response_model=GuessPlayerStart)
def start_game():
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT p.player_id, p.name, ps.season_id, s.season_name,
                   ps.games_played, ps.pts, ps.reb, ps.ast, ps.blk, ps.stl,
                   r.position, r.height, f.abbreviation
            FROM player_season ps
            JOIN player p ON p.player_id = ps.player_id AND p.notice_flag = TRUE
            JOIN season s ON s.season_id = ps.season_id
            JOIN roster r ON r.season_id = ps.season_id
                AND r.player_id = ps.player_id
                AND r.team_id = ps.team_id
            JOIN franchise f ON f.team_id = ps.team_id
            WHERE ps.games_played >= 20
              AND ps.pts::DECIMAL / ps.games_played >= 5
            ORDER BY RANDOM()
            LIMIT 1
        """)
        row = cursor.fetchone()

        if row is None:
            return {"error": "no eligible players found"}

        (player_id, name, season_id, season_name, games, pts, reb,
         ast, blk, stl, position, height, team) = row

        cursor.execute("""
            SELECT organization, overall_pick FROM draft
            WHERE player_id = %s
            LIMIT 1
        """, (player_id,))
        draft_row = cursor.fetchone()
        college = draft_row[0] if draft_row and draft_row[0] else "Undrafted / International"
        overall_pick = str(draft_row[1]) if draft_row and draft_row[1] else "Undrafted"

        cursor.execute("""
            SELECT award FROM player_award
            WHERE player_id = %s AND season_id = %s
        """, (player_id, season_id))
        award_rows = cursor.fetchall()

        award_counts: dict[str, int] = {}
        for (award,) in award_rows:
            award_counts[award] = award_counts.get(award, 0) + 1

        awards = ", ".join(
            f"{count}x {award}" if count > 1 else award
            for award, count in award_counts.items()
        ) if award_counts else "None"
        
        trend_stat = random.choice(list(TREND_STAT_COLUMNS.keys()))

        cursor.execute(f"""
            SELECT s.season_name, s.start_year,
                   SUM(ps2.{trend_stat})::DECIMAL / SUM(ps2.games_played)
            FROM player_season ps2
            JOIN season s ON s.season_id = ps2.season_id
            WHERE ps2.player_id = %s
            GROUP BY s.season_name, s.start_year
            ORDER BY s.start_year
        """, (player_id,))
        trend_rows = cursor.fetchall()

    metrics = {
        "position": position,
        "height": height,
        "team": team,
        "season": season_name,
        "college": college,
        "overall_pick": overall_pick,
        "ppg": round(pts / games, 1),
        "rpg": round(reb / games, 1),
        "apg": round(ast / games, 1),
        "bpg": round(blk / games, 1),
        "spg": round(stl / games, 1),
        "awards": awards,
        "trend": "Career trend",
    }

    trend = [
        TrendPoint(season=season_name, value=round(float(value), 1))
        for season_name, _, value in trend_rows
    ]

    reveal_order = METRIC_KEYS.copy()
    random.shuffle(reveal_order)

    return GuessPlayerStart(
        metrics=metrics,
        trend=trend,
        reveal_order=reveal_order,
        round_reveal_counts=ROUND_REVEAL_COUNTS,
        answer_hash=hash_answer(name),
    )


@router.get("/guess-player/search", response_model=SearchResult)
def search_players(q: str = ""):
    if len(q.strip()) < 2:
        return SearchResult(names=[])

    with db.cursor() as cursor:
        cursor.execute("""
            SELECT name FROM player
            WHERE name ILIKE %s AND notice_flag = TRUE
            ORDER BY name
            LIMIT 8
        """, (f"%{q.strip()}%",))
        names = [r[0] for r in cursor.fetchall()]

    return SearchResult(names=names)