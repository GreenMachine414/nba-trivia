import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer

router = APIRouter()

QUESTION_TYPE = "Season Average"


class StatLine(BaseModel):
    ppg: float
    rpg: float
    apg: float
    spg: float | None = None
    bpg: float | None = None


class StatTriviaQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    choices: list[str]


class MissingStatQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    hidden_stat: str
    choices: list[str]


class SeasonGuessQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    choices: list[str]


class TeamGuessQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    season: str
    choices: list[str]


def build_numeric_choices(correct_value: float, spread: float = 3.0) -> list[str]:
    """Generate 3 plausible-but-wrong numeric decoys near the correct value."""
    wrong_values = set()
    while len(wrong_values) < 3:
        offset = random.uniform(-spread, spread)
        candidate = round(correct_value + offset, 1)
        if candidate != correct_value and candidate >= 0:
            wrong_values.add(candidate)

    choices = [str(correct_value)] + [str(v) for v in wrong_values]
    random.shuffle(choices)
    return choices


def build_stat_line(games, points, rebounds, assists, steals, blocks) -> tuple[StatLine, list[tuple[float, str]]]:
    """Builds a StatLine (nulling out unavailable categories) and a parallel
    list of (value, label) pairs for only the stats that actually exist,
    so question text never references a stat this season doesn't track."""
    ppg = round(points / games, 1)
    rpg = round(rebounds / games, 1)
    apg = round(assists / games, 1)
    spg = round(steals / games, 1) if steals is not None else None
    bpg = round(blocks / games, 1) if blocks is not None else None

    stats = StatLine(ppg=ppg, rpg=rpg, apg=apg, spg=spg, bpg=bpg)

    parts = [(ppg, "PPG"), (rpg, "RPG"), (apg, "APG")]
    if spg is not None:
        parts.append((spg, "SPG"))
    if bpg is not None:
        parts.append((bpg, "BPG"))

    return stats, parts


@router.get("/trivia/season_average", response_model=StatTriviaQuestion)
def guess_season_average():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT p.player_id, p.player_name, s.season,
               s.games_played, s.pts, s.reb, s.ast, s.stl, s.blk
        FROM season_stats s
        JOIN players p ON p.player_id = s.player_id
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no season stats found"}

    player_id, player_name, season, games, points, rebounds, assists, steals, blocks = row

    stats, parts = build_stat_line(games, points, rebounds, assists, steals, blocks)
    parts_text = ", ".join(f"{value} {label}" for value, label in parts)

    question = f"Who averaged {parts_text} in the {season} season?"

    question_id, choices = build_question_base(player_name)

    return StatTriviaQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        choices=choices,
    )


@router.get("/trivia/missing_stat", response_model=MissingStatQuestion)
def guess_missing_stat():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT p.player_name, s.season,
               s.games_played, s.pts, s.reb, s.ast, s.stl, s.blk
        FROM season_stats s
        JOIN players p ON p.player_id = s.player_id
        WHERE s.games_played >= 20
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no season stats found"}

    player_name, season, games, points, rebounds, assists, steals, blocks = row

    stats, parts = build_stat_line(games, points, rebounds, assists, steals, blocks)

    if len(parts) < 2:
        return {"error": "not enough available stats for this season"}

    stat_field_map = {"PPG": "ppg", "RPG": "rpg", "APG": "apg", "SPG": "spg", "BPG": "bpg"}
    hidden_value, hidden_label = random.choice(parts)
    hidden_field = stat_field_map[hidden_label]

    shown_parts = [f"{value} {label}" for value, label in parts if label != hidden_label]

    question = (
        f"{player_name} averaged {', '.join(shown_parts)} in the {season} season. "
        f"What was his {hidden_label}?"
    )

    setattr(stats, hidden_field, None)  # hide the answer from the returned stat line

    choices = build_numeric_choices(hidden_value)
    question_id = register_answer(str(hidden_value))

    return MissingStatQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        hidden_stat=hidden_field,
        choices=choices,
    )


@router.get("/trivia/season_guess", response_model=SeasonGuessQuestion)
def guess_the_season():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT p.player_id, p.player_name
        FROM players p
        JOIN season_stats s ON p.player_id = s.player_id
        GROUP BY p.player_id, p.player_name
        HAVING COUNT(*) >= 3
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_id, player_name = row

    cursor.execute("""
        SELECT season, games_played, pts, reb, ast, stl, blk
        FROM season_stats
        WHERE player_id = %s
        ORDER BY RANDOM()
        LIMIT 1
    """, (player_id,))
    stat_row = cursor.fetchone()

    if stat_row is None:
        cursor.close()
        return {"error": "no season stats found"}

    season = stat_row[0]

    cursor.execute("""
        SELECT season FROM (
            SELECT DISTINCT season FROM season_stats
            WHERE season != %s
        ) AS distinct_seasons
        ORDER BY RANDOM()
        LIMIT 3
    """, (season,))
    wrong_seasons = [r[0] for r in cursor.fetchall()]
    cursor.close()

    season, games, points, rebounds, assists, steals, blocks = stat_row

    stats, parts = build_stat_line(games, points, rebounds, assists, steals, blocks)
    parts_text = ", ".join(f"{value} {label}" for value, label in parts)

    question = f"In which season did {player_name} average {parts_text}?"

    choices = [season] + wrong_seasons
    random.shuffle(choices)

    question_id = register_answer(season)

    return SeasonGuessQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        choices=choices,
    )