import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer, hash_answer

router = APIRouter()

QUESTION_TYPE = "Career Path"


class PathStop(BaseModel):
    team: str
    start_season: str
    end_season: str


class PathTriviaQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    path: list[PathStop]
    choices: list[str]
    answer_hash: str


class MissingStopQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    player_name: str
    path: list[PathStop]
    hidden_index: int
    choices: list[str]
    answer_hash: str


class TeamCountQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    player_name: str
    choices: list[str]
    answer_hash: str


def fetch_random_eligible_player(cursor):

    cursor.execute("""
        SELECT
            r.player_id,
            p.name
        FROM roster r
        JOIN player p
            ON p.player_id = r.player_id
        WHERE p.notice_flag = TRUE
        GROUP BY
            r.player_id,
            p.name
        ORDER BY RANDOM()
        LIMIT 1
    """)

    return cursor.fetchone()


def fetch_career_path(cursor, player_id: int) -> list[PathStop]:

    cursor.execute("""
        SELECT
            s.season_name,
            f.abbreviation
        FROM roster r
        JOIN franchise f
            ON f.team_id = r.team_id
        JOIN season s
            ON s.season_id = r.season_id
        WHERE r.player_id = %s
        ORDER BY s.start_year
    """, (player_id,))

    rows = cursor.fetchall()

    path: list[PathStop] = []

    for season, team in rows:

        if path and path[-1].team == team:
            path[-1].end_season = season
        else:
            path.append(
                PathStop(
                    team=team,
                    start_season=season,
                    end_season=season
                )
            )

    return path


@router.get("/trivia/career_path", response_model=PathTriviaQuestion)
def guess_career_path():

    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_eligible_player(cursor)

    if row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_id, player_name = row
    path = fetch_career_path(cursor, player_id)

    cursor.close()

    if not path:
        return {"error": "no career path found"}

    question = "Which player had this career path?"

    question_id, choices = build_question_base(player_name)

    return PathTriviaQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        path=path,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )


@router.get("/trivia/missing_stop", response_model=MissingStopQuestion)
def guess_missing_stop():

    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_eligible_player(cursor)

    if row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_id, player_name = row
    path = fetch_career_path(cursor, player_id)

    if not path:
        cursor.close()
        return {"error": "no career path found"}

    hidden_index = random.randint(0, len(path) - 1)
    correct_team = path[hidden_index].team

    cursor.execute("""
        SELECT abbreviation
        FROM franchise
        WHERE abbreviation != %s
        ORDER BY RANDOM()
        LIMIT 3
    """, (correct_team,))

    wrong_teams = [r[0] for r in cursor.fetchall()]

    cursor.close()

    if len(wrong_teams) < 3:
        return {"error": "not enough teams for choices"}

    visible_path = [
        PathStop(
            team="???",
            start_season=stop.start_season,
            end_season=stop.end_season
        )
        if i == hidden_index else stop
        for i, stop in enumerate(path)
    ]

    question = (
        f"Which team did {player_name} play for "
        f"during this part of his career?"
    )

    choices = [correct_team] + wrong_teams

    question_id = register_answer(correct_team)

    return MissingStopQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        player_name=player_name,
        path=visible_path,
        hidden_index=hidden_index,
        choices=choices,
        answer_hash=hash_answer(correct_team),
    )


@router.get("/trivia/team_count", response_model=TeamCountQuestion)
def guess_team_count():

    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_eligible_player(cursor)

    if row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_id, player_name = row
    path = fetch_career_path(cursor, player_id)

    cursor.close()

    if not path:
        return {"error": "no career path found"}

    correct_count = len(path)

    wrong_counts = set()

    while len(wrong_counts) < 3:
        candidate = correct_count + random.choice(
            [-2, -1, 1, 2, 3]
        )

        if candidate >= 1 and candidate != correct_count:
            wrong_counts.add(candidate)

    question = (
        f"How many different teams has {player_name} "
        f"played for in his career?"
    )

    choices = [str(correct_count)] + [
        str(count)
        for count in wrong_counts
    ]

    question_id = register_answer(str(correct_count))

    return TeamCountQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        player_name=player_name,
        choices=choices,
        answer_hash=hash_answer(str(correct_count)),
    )