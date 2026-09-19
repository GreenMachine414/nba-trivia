import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer, hash_answer

router = APIRouter()

QUESTION_TYPE = "Player Identity"


class JerseyPlayerQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


class JerseyNumberQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


class CareerJerseysQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


def parse_jersey_numbers(raw: str) -> list[int]:
    if raw is None:
        return []
    parts = raw.split("-")
    numbers = []
    for part in parts:
        part = part.strip()
        if part.isdigit():
            numbers.append(int(part))
    return numbers


def build_numeric_choices(correct_value: int, spread: int = 20, min_value: int = 0, max_value: int = 99) -> list[str]:
    wrong_values = set()
    while len(wrong_values) < 3:
        offset = random.randint(-spread, spread)
        candidate = correct_value + offset
        if candidate != correct_value and min_value <= candidate <= max_value:
            wrong_values.add(candidate)

    choices = [str(correct_value)] + [str(v) for v in wrong_values]
    random.shuffle(choices)
    return choices


@router.get("/trivia/jersey_player", response_model=JerseyPlayerQuestion)
def guess_jersey_player():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT r.player_id, p.player_name, r.season, r.jersey_number, t.abbreviation
        FROM rosters r
        JOIN players p ON p.player_id = r.player_id
        JOIN teams t ON t.team_id = r.team_id
        WHERE r.jersey_number IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no roster data found"}

    player_id, player_name, season, jersey_number, team = row

    numbers = parse_jersey_numbers(jersey_number)
    if not numbers:
        return {"error": "no valid jersey number found"}

    jersey_number_display = random.choice(numbers)

    question = f"Who wore #{jersey_number_display} for the {team} in the {season} season?"

    question_