import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer

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


class MissingStopQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    player_name: str
    path: list[PathStop]
    hidden_index: int
    choices: list[str]


class TeamCountQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    player_name: str
    choices: list[str]


def fetch_random_eligible_player(cursor, min_stops: int = 3):
    """Returns (player_id, player_name) for a random player with at least
    min_stops distinct roster entries, or None if none qualify."""
    cursor.execute("""
        SELECT rosters.player_id, players.player_name
        FROM rosters
        JOIN players ON players.player_id = rosters.player_id
        GROUP BY rosters.player_id, players.player_name
        HAVING COUNT(*) >= %s
        ORDER BY RANDOM()
        LIMIT 1
    """, (min_stops,))
    return cursor.fetchone()


def fetch_career_path(cursor, player_id: int) -> list[PathStop]:
    """Builds a collapsed list of PathStop entries (consecutive seasons
    on the same team merged into one stop) for a given player."""
    cursor.execute("""
        SELECT rosters.season, teams.abbreviation
        FROM rosters
        JOIN teams ON rosters.team_id = teams.team_id
        WHERE rosters.player_id = %s
        ORDER BY rosters.season
    """, (player_id,))
    rows = cursor.fetchall()

    path: list[PathStop] = []
    for season, team in rows:
        if path and path[-1].team == team:
            path[-1].end_season = season
        else:
            path.append(PathStop(team=team, start_season=season, end_season=season))

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
    )


@router.get("/trivia/missing_stop", response_model=MissingStopQuestion)
def guess_missing_stop():
    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_eligible_player(cursor, min_stops=1)
    if row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_id, player_name = row
    path = fetch_career_path(cursor, player_id)
    cursor.close()

    if not path:
        return {"error": "no career path found"}

    hidden_index = random.randint(0, len(path) - 1)
    correct_team = path[hidden_index].team

    cursor2 = db.connection.cursor()
    cursor2.execute("""
        SELECT abbreviation FROM teams
        WHERE abbreviation != %s
        ORDER BY RANDOM()
        LIMIT 3
    """, (correct_team,))
    wrong_teams = [r[0] for r in cursor2.fetchall()]
    cursor2.close()

    visible_path = [
        PathStop(team="???", start_season=stop.start_season, end_season=stop.end_season)
        if i == hidden_index else stop
        for i, stop in enumerate(path)
    ]

    question = f"Which team did {player_name} play for during this part of his career?"

    choices = [correct_team] + wrong_teams
    random.shuffle(choices)

    question_id = register_answer(correct_team)

    return MissingStopQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        player_name=player_name,
        path=visible_path,
        hidden_index=hidden_index,
        choices=choices,
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
        candidate = correct_count + random.choice([-2, -1, 1, 2, 3])
        if candidate >= 1 and candidate != correct_count:
            wrong_counts.add(candidate)

    question = f"How many different teams has {player_name} played for in his career?"

    choices = [str(correct_count)] + [str(c) for c in wrong_counts]
    random.shuffle(choices)

    question_id = register_answer(str(correct_count))

    return TeamCountQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        player_name=player_name,
        path=path,
        choices=choices,
    )