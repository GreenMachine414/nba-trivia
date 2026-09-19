import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, hash_answer

router = APIRouter()

QUESTION_TYPE = "Awards"

SINGLE_WINNER_AWARDS = [
    "NBA Most Valuable Player",
    "NBA Rookie of the Year",
    "NBA Defensive Player of the Year",
    "NBA Sixth Man of the Year",
    "NBA Finals Most Valuable Player",
    "NBA All-Star Most Valuable Player",
    "NBA Sporting News Most Valuable Player of the Year",
    "NBA Sporting News Rookie of the Year",
]


class AwardWinnerQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


class CareerResumeQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    resume: list[str]
    choices: list[str]
    answer_hash: str


@router.get("/trivia/award_winner", response_model=AwardWinnerQuestion)
def guess_award_winner():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT a.player_id, p.player_name, a.season, a.description
        FROM awards a
        JOIN players p ON p.player_id = a.player_id
        WHERE a.description = ANY(%s)
        ORDER BY RANDOM()
        LIMIT 1
    """, (SINGLE_WINNER_AWARDS,))
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no award data found"}

    player_id, player_name, season, description = row

    question = f"Who won {description} in the {season} season?"

    question_id, choices = build_question_base(player_name)

    return AwardWinnerQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )


@router.get("/trivia/career_resume", response_model=CareerResumeQuestion)
def guess_career_resume():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT player_id, description, COUNT(*) AS times_won
        FROM awards
        GROUP BY player_id, description
    """)
    rows = cursor.fetchall()

    resumes: dict[int, list[tuple[str, int]]] = {}
    for player_id, description, times_won in rows:
        resumes.setdefault(player_id, []).append((description, times_won))

    signature_to_players: dict[tuple, list[int]] = {}
    for player_id, entries in resumes.items():
        signature = tuple(sorted(entries))
        signature_to_players.setdefault(signature, []).append(player_id)

    unique_signatures = [
        (sig, players[0]) for sig, players in signature_to_players.items()
        if len(players) == 1 and len(sig) >= 2  # require a real, non-trivial resume
    ]

    if not unique_signatures:
        cursor.close()
        return {"error": "no eligible players found"}

    signature, player_id = random.choice(unique_signatures)

    cursor.execute("SELECT player_name FROM players WHERE player_id = %s", (player_id,))
    name_row = cursor.fetchone()
    cursor.close()

    if name_row is None:
        return {"error": "player not found"}

    player_name = name_row[0]

    resume_lines = [
        f"{description} ({times_won}x)" if times_won > 1 else description
        for description, times_won in sorted(signature, key=lambda x: x[0])
    ]

    question = "Which player has this exact career award resume?"

    question_id, choices = build_question_base(player_name)

    return CareerResumeQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        resume=resume_lines,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )