import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer

router = APIRouter()

QUESTION_TYPE = "Draft"


class DraftPlayerQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


class OverallPickQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


class OrganizationQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


class PlayerFromOrgQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]


def fetch_random_draft_row(cursor):
    """Returns (player_id, player_name, season, round_number, round_pick,
    overall_pick, organization) for a random draft pick, or None."""
    cursor.execute("""
        SELECT d.player_id, p.player_name, d.season, d.round_number,
               d.round_pick, d.overall_pick, d.organization
        FROM draft_history d
        JOIN players p ON p.player_id = d.player_id
        WHERE d.organization IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1
    """)
    return cursor.fetchone()


def build_numeric_choices(correct_value: int, spread: int = 5, min_value: int = 1) -> list[str]:
    """Generate 3 plausible-but-wrong integer decoys near the correct value."""
    wrong_values = set()
    while len(wrong_values) < 3:
        offset = random.randint(-spread, spread)
        candidate = correct_value + offset
        if candidate != correct_value and candidate >= min_value:
            wrong_values.add(candidate)

    choices = [str(correct_value)] + [str(v) for v in wrong_values]
    random.shuffle(choices)
    return choices


@router.get("/trivia/draft_player", response_model=DraftPlayerQuestion)
def guess_drafted_player():
    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_draft_row(cursor)
    cursor.close()

    if row is None:
        return {"error": "no draft history found"}

    player_id, player_name, season, round_number, round_pick, overall_pick, organization = row

    question = (
        f"Who was drafted with the #{round_pick} pick of round {round_number} "
        f"in the {season} draft?"
    )

    question_id, choices = build_question_base(player_name)

    return DraftPlayerQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )


@router.get("/trivia/overall_pick", response_model=OverallPickQuestion)
def guess_overall_pick():
    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_draft_row(cursor)
    cursor.close()

    if row is None:
        return {"error": "no draft history found"}

    player_id, player_name, season, round_number, round_pick, overall_pick, organization = row

    question = f"What overall pick was {player_name} selected with in the {season} draft?"

    choices = build_numeric_choices(overall_pick, spread=6, min_value=1)
    question_id = register_answer(str(overall_pick))

    return OverallPickQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )


@router.get("/trivia/draft_organization", response_model=OrganizationQuestion)
def guess_organization():
    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_draft_row(cursor)
    if row is None:
        cursor.close()
        return {"error": "no draft history found"}

    player_id, player_name, season, round_number, round_pick, overall_pick, organization = row

    cursor.execute("""
        SELECT organization FROM (
            SELECT DISTINCT organization FROM draft_history
            WHERE organization != %s AND organization IS NOT NULL
        ) AS distinct_orgs
        ORDER BY RANDOM()
        LIMIT 3
    """, (organization,))
    wrong_orgs = [r[0] for r in cursor.fetchall()]
    cursor.close()

    question = f"What organization was {player_name} selected from in the {season} draft?"

    choices = [organization] + wrong_orgs
    random.shuffle(choices)

    question_id = register_answer(organization)

    return OrganizationQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )


@router.get("/trivia/player_from_organization", response_model=PlayerFromOrgQuestion)
def guess_player_from_organization():
    db.ensure_connected()
    cursor = db.connection.cursor()

    row = fetch_random_draft_row(cursor)
    if row is None:
        cursor.close()
        return {"error": "no draft history found"}

    player_id, player_name, season, round_number, round_pick, overall_pick, organization = row
    cursor.close()

    question = f"Which player was selected from {organization} in the {season} draft?"

    question_id, choices = build_question_base(player_name)

    return PlayerFromOrgQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
    )