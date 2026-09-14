import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer

router = APIRouter()

QUESTION_TYPE = "Player Identity"


class JerseyPlayerQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


class JerseyNumberQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


class CareerJerseysQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


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
    """Generate 3 plausible-but-wrong jersey number decoys near the correct value."""
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

    question_id, choices = build_question_base(player_name)

    return JerseyPlayerQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )


@router.get("/trivia/jersey_number", response_model=JerseyNumberQuestion)
def guess_jersey_number():
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

    jersey_number_int = random.choice(numbers)

    question = f"What jersey number did {player_name} wear for the {team} in the {season} season?"

    choices = build_numeric_choices(jersey_number_int)
    question_id = register_answer(str(jersey_number_int))

    return JerseyNumberQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )


@router.get("/trivia/career_jerseys", response_model=CareerJerseysQuestion)
def guess_career_jerseys():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT rosters.player_id, players.player_name
        FROM rosters
        JOIN players ON players.player_id = rosters.player_id
        WHERE rosters.jersey_number IS NOT NULL
        GROUP BY rosters.player_id, players.player_name
        HAVING COUNT(DISTINCT rosters.jersey_number) >= 2
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    if row is None:
        cursor.close()
        return {"error": "no eligible players found"}

    player_id, player_name = row

    cursor.execute("""
        SELECT DISTINCT jersey_number FROM rosters
        WHERE player_id = %s AND jersey_number IS NOT NULL
    """, (player_id,))
    real_numbers = sorted({
        n for raw in cursor.fetchall() for n in parse_jersey_numbers(raw[0])
    })

    if len(real_numbers) < 2:
        cursor.close()
        return {"error": "no eligible players found"}

    correct_answer = ", ".join(str(n) for n in real_numbers)

    # Pull other players' real jersey-number sets as decoys, so every
    # choice is a genuinely plausible combination, not a mutated one.
    cursor.execute("""
        SELECT player_id, jersey_number FROM rosters
        WHERE player_id != %s AND jersey_number IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 200
    """, (player_id,))
    other_rows = cursor.fetchall()
    cursor.close()

    other_by_player: dict[int, set[int]] = {}
    for pid, jersey in other_rows:
        for n in parse_jersey_numbers(jersey):
            other_by_player.setdefault(pid, set()).add(n)

    wrong_options = set()
    for numbers in other_by_player.values():
        if not numbers:
            continue
        variant_str = ", ".join(str(n) for n in sorted(numbers))
        if variant_str and variant_str != correct_answer:
            wrong_options.add(variant_str)
        if len(wrong_options) >= 3:
            break

    # Fallback in the rare case fewer than 3 distinct decoys were found
    while len(wrong_options) < 3:
        filler = ", ".join(str(n) for n in sorted({random.randint(0, 55) for _ in range(len(real_numbers))}))
        if filler != correct_answer:
            wrong_options.add(filler)

    question = f"Which jersey number(s) did {player_name} wear throughout his career?"

    choices = [correct_answer] + list(wrong_options)[:3]
    random.shuffle(choices)

    question_id = register_answer(correct_answer)

    return CareerJerseysQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )