import random

from fastapi import APIRouter, HTTPException
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
    if not raw:
        return []

    numbers = []

    for part in raw.split("-"):
        part = part.strip()

        if part.isdigit():
            numbers.append(int(part))

    return numbers


def build_numeric_choices(
    correct_value: int,
    spread: int = 20,
    min_value: int = 1,
    max_value: int = 99
) -> list[str]:
    wrong_values = set()

    while len(wrong_values) < 3:
        offset = random.randint(-spread, spread)
        candidate = correct_value + offset

        if (
            candidate != correct_value
            and min_value <= candidate <= max_value
        ):
            wrong_values.add(candidate)

    choices = [str(correct_value)] + [
        str(value) for value in wrong_values
    ]

    return choices


@router.get("/trivia/jersey_player", response_model=JerseyPlayerQuestion)
def guess_jersey_player():
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.name,
                s.season_name,
                r.jersey_number,
                f.abbreviation
            FROM roster r
            JOIN player p
                ON p.player_id = r.player_id
            JOIN franchise f
                ON f.team_id = r.team_id
            JOIN season s
                ON s.season_id = r.season_id
            WHERE
                r.jersey_number IS NOT NULL
                AND p.notice_flag = TRUE
            ORDER BY RANDOM()
            LIMIT 1
        """)

        row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No roster data found"
        )

    player_name, season, jersey_number, team = row

    numbers = parse_jersey_numbers(jersey_number)

    if not numbers:
        raise HTTPException(
            status_code=404,
            detail="No valid jersey number found"
        )

    jersey_number_display = random.choice(numbers)

    question = (
        f"Who wore #{jersey_number_display} for the "
        f"{team} in the {season} season?"
    )

    question_id, choices = build_question_base(player_name)

    return JerseyPlayerQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )


@router.get("/trivia/jersey_number", response_model=JerseyNumberQuestion)
def guess_jersey_number():
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.name,
                s.season_name,
                r.jersey_number,
                f.abbreviation
            FROM roster r
            JOIN player p
                ON p.player_id = r.player_id
            JOIN franchise f
                ON f.team_id = r.team_id
            JOIN season s
                ON s.season_id = r.season_id
            WHERE
                r.jersey_number IS NOT NULL
                AND p.notice_flag = TRUE
            ORDER BY RANDOM()
            LIMIT 1
        """)

        row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No roster data found"
        )

    player_name, season, jersey_number, team = row

    numbers = parse_jersey_numbers(jersey_number)

    if not numbers:
        raise HTTPException(
            status_code=404,
            detail="No valid jersey number found"
        )

    jersey_number_int = random.choice(numbers)

    question = (
        f"What jersey number did {player_name} wear for the "
        f"{team} in the {season} season?"
    )

    choices = build_numeric_choices(jersey_number_int)

    question_id = register_answer(str(jersey_number_int))

    return JerseyNumberQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(str(jersey_number_int)),
    )


@router.get("/trivia/career_jerseys", response_model=CareerJerseysQuestion)
def guess_career_jerseys():
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.player_id,
                p.name,
                ARRAY_AGG(DISTINCT r.jersey_number) AS jersey_numbers
            FROM player p
            JOIN roster r
                ON r.player_id = p.player_id
            WHERE
                p.notice_flag = TRUE
                AND r.jersey_number IS NOT NULL
            GROUP BY
                p.player_id,
                p.name
            ORDER BY RANDOM()
            LIMIT 1
        """)

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="No eligible players found"
            )

        player_id, player_name, raw_numbers = row

        career_numbers = set()

        for jersey_number in raw_numbers:
            career_numbers.update(
                parse_jersey_numbers(jersey_number)
            )

        cursor.execute("""
            SELECT
                p.player_id,
                p.name,
                ARRAY_AGG(DISTINCT r.jersey_number) AS jersey_numbers
            FROM player p
            JOIN roster r
                ON r.player_id = p.player_id
            WHERE
                p.notice_flag = TRUE
                AND p.player_id != %s
                AND p.name != %s
                AND r.jersey_number IS NOT NULL
            GROUP BY
                p.player_id,
                p.name
        """, (player_id, player_name))

        candidates = cursor.fetchall()

    wrong_choices = []

    for _, candidate_name, raw_numbers in candidates:
        candidate_numbers = set()

        for jersey_number in raw_numbers:
            candidate_numbers.update(
                parse_jersey_numbers(jersey_number)
            )

        if candidate_numbers != career_numbers:
            wrong_choices.append(candidate_name)

    if len(wrong_choices) < 3:
        raise HTTPException(
            status_code=404,
            detail="Not enough valid choices found"
        )

    choices = [player_name] + wrong_choices[:3]

    jersey_numbers = ", ".join(
        f"#{number}"
        for number in sorted(career_numbers)
    )

    question = (
        f"What player wore the following jersey number(s) "
        f"throughout their career? {jersey_numbers}"
    )

    question_id, _ = build_question_base(player_name)

    return CareerJerseysQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )