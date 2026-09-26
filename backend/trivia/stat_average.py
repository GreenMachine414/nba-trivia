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


def build_stat_line(
    games,
    points,
    rebounds,
    assists,
    steals,
    blocks
) -> tuple[StatLine, list[tuple[float, str]]]:
    ppg = round(points / games, 1)
    rpg = round(rebounds / games, 1)
    apg = round(assists / games, 1)
    spg = round(steals / games, 1) if steals is not None else None
    bpg = round(blocks / games, 1) if blocks is not None else None

    stats = StatLine(
        ppg=ppg,
        rpg=rpg,
        apg=apg,
        spg=spg,
        bpg=bpg
    )

    parts = [
        (ppg, "PPG"),
        (rpg, "RPG"),
        (apg, "APG")
    ]

    if spg is not None:
        parts.append((spg, "SPG"))

    if bpg is not None:
        parts.append((bpg, "BPG"))

    return stats, parts


@router.get("/trivia/season_average", response_model=StatTriviaQuestion)
def guess_season_average():
    with db.cursor() as cursor:
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
            WHERE p.notice_flag = TRUE
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

    if row is None:
        return {"error": "no season stats found"}

    (
        player_name,
        season,
        games,
        points,
        rebounds,
        assists,
        steals,
        blocks
    ) = row

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

    question = (
        f"Who averaged {parts_text} "
        f"in the {season} season?"
    )

    question_id, choices = build_question_base(player_name)

    return StatTriviaQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        stats=stats,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )


@router.get("/trivia/season_guess", response_model=SeasonGuessQuestion)
def guess_the_season():
    with db.cursor() as cursor:
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
            WHERE p.notice_flag = TRUE
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

        stat_row = cursor.fetchone()

        if stat_row is None:
            return {"error": "no eligible players found"}

        (
            player_name,
            season,
            games,
            points,
            rebounds,
            assists,
            steals,
            blocks
        ) = stat_row

        cursor.execute("""
            SELECT season_name
            FROM season
            WHERE season_name != %s
            ORDER BY RANDOM()
            LIMIT 3
        """, (season,))

        wrong_seasons = [
            row[0]
            for row in cursor.fetchall()
        ]

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

    question = (
        f"In which season did {player_name} "
        f"average {parts_text}?"
    )

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