import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer, hash_answer

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
    answer_hash: str


class MissingStatQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    hidden_stat: str
    choices: list[str]
    answer_hash: str


class SeasonGuessQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    choices: list[str]
    answer_hash: str


class TeamGuessQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    stats: StatLine
    season: str
    choices: list[str]
    answer_hash: str


def build_numeric_choices(correct_value: float, spread: float = 3.0) -> list[str]:
    wrong_values = set()
    while len(wrong_values) < 3:
        offset = random.uniform(-spread, spread)
        candidate = round(correct_value + offset, 1)
        if candidate != correct_value and candidate >= 0:
            wrong_values.add(candidate)

    choices = [str(correct_value)] + [str(v) for v in wrong_values]

    return choices


def build_stat_line(games, points, rebounds, assists, steals, blocks) -> tuple[StatLine, list[tuple[float, str]]]:
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
        SELECT 
            p.name,
            season.season_name,
            SUM(s.games_played) AS games,
            SUM(s.pts) AS points,
            SUM(s.reb) AS rebounds,
            SUM(s.ast) AS assists,
            SUM(s.stl) AS steals,
            SUM(s.blk) AS blocks
        FROM player_season s
        JOIN player p 
            ON p.player_id = s.player_id
        JOIN season
            ON s.season_id = season.season_id
        GROUP BY
            season.season_name,
            p.player_id,
            p.name
        HAVING 
            SUM(s.games_played) >= 20
            AND SUM(s.pts)::DECIMAL / SUM(s.games_played) >= 5
        ORDER BY RANDOM()
        LIMIT 1;
    """)

    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no season stats found"}

    player_name, season, games, points, rebounds, assists, steals, blocks = row

    stats, parts = build_stat_line(
        games,
        points,
        rebounds,
        assists,
        steals,
        blocks
    )

    parts_text = ", ".join(f"{value} {label}" for value, label in parts)

    question = f"Who averaged {parts_text} in the {season} season?"

    question_id, choices = build_question_base(player_name)

    return StatTriviaQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )


@router.get("/trivia/missing_stat", response_model=MissingStatQuestion)
def guess_missing_stat():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT
            p.name,
            season.season_name,
            SUM(s.games_played) AS games,
            SUM(s.pts) AS points,
            SUM(s.reb) AS rebounds,
            SUM(s.ast) AS assists,
            SUM(s.stl) AS steals,
            SUM(s.blk) AS blocks
        FROM player_season s
        JOIN player p
            ON p.player_id = s.player_id
        JOIN season
            ON s.season_id = season.season_id
        GROUP BY
            season.season_name,
            p.player_id,
            p.name
        HAVING
            SUM(s.games_played) >= 20
            AND SUM(s.pts)::DECIMAL / SUM(s.games_played) >= 5
        ORDER BY RANDOM()
        LIMIT 1
    """)

    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no season stats found"}

    player_name, season, games, points, rebounds, assists, steals, blocks = row

    stats, parts = build_stat_line(
        games,
        points,
        rebounds,
        assists,
        steals,
        blocks
    )

    if len(parts) < 2:
        return {"error": "not enough available stats for this season"}

    stat_field_map = {
        "PPG": "ppg",
        "RPG": "rpg",
        "APG": "apg",
        "SPG": "spg",
        "BPG": "bpg"
    }

    hidden_value, hidden_label = random.choice(parts)
    hidden_field = stat_field_map[hidden_label]

    shown_parts = [
        f"{value} {label}"
        for value, label in parts
        if label != hidden_label
    ]

    question = (
        f"{player_name} averaged {', '.join(shown_parts)} "
        f"in the {season} season. "
        f"What was his {hidden_label}?"
    )

    setattr(stats, hidden_field, None)

    choices = build_numeric_choices(hidden_value)
    question_id = register_answer(str(hidden_value))

    return MissingStatQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        hidden_stat=hidden_field,
        choices=choices,
        answer_hash=hash_answer(str(hidden_value)),
    )


@router.get("/trivia/season_guess", response_model=SeasonGuessQuestion)
def guess_the_season():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT
            p.name,
            season.season_name,
            SUM(s.games_played) AS games,
            SUM(s.pts) AS points,
            SUM(s.reb) AS rebounds,
            SUM(s.ast) AS assists,
            SUM(s.stl) AS steals,
            SUM(s.blk) AS blocks
        FROM player_season s
        JOIN player p
            ON p.player_id = s.player_id
        JOIN season
            ON s.season_id = season.season_id
        GROUP BY
            season.season_name,
            p.player_id,
            p.name
        HAVING
            SUM(s.games_played) >= 20
            AND SUM(s.pts)::DECIMAL / SUM(s.games_played) >= 5
        ORDER BY RANDOM()
        LIMIT 1;
    """)

    stat_row = cursor.fetchone()

    if stat_row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_name, season, games, points, rebounds, assists, steals, blocks = stat_row

    cursor.execute("""
        SELECT season_name
        FROM season
        WHERE season_name != %s
        ORDER BY RANDOM()
        LIMIT 3
    """, (season,))

    wrong_seasons = [r[0] for r in cursor.fetchall()]
    cursor.close()

    stats, parts = build_stat_line(
        games,
        points,
        rebounds,
        assists,
        steals,
        blocks
    )

    parts_text = ", ".join(
        f"{value} {label}"
        for value, label in parts
    )

    question = f"In which season did {player_name} average {parts_text}?"

    choices = [season] + wrong_seasons

    question_id = register_answer(season)

    return SeasonGuessQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        choices=choices,
        answer_hash=hash_answer(season)
    )