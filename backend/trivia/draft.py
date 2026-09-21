import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db
from .engine import build_question_base, register_answer, hash_answer

router = APIRouter()

QUESTION_TYPE = "Draft Trivia"


class DraftPlayerQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


class OverallPickQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


class OrganizationQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


class PlayerFromOrgQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


def fetch_random_draft_row(cursor):
    cursor.execute("""
        SELECT
            d.player_id,
            p.name,
            s.season_name,
            d.round_number,
            d.pick_number,
            d.overall_pick,
            d.organization
        FROM draft d
        JOIN player p
            ON p.player_id = d.player_id
        JOIN season s
            ON s.season_id = d.season_id
        WHERE
            d.organization IS NOT NULL
            AND p.notice_flag = TRUE
        ORDER BY RANDOM()
        LIMIT 1
    """)

    return cursor.fetchone()


def build_numeric_choices(
    correct_value: int,
    spread: int = 5,
    min_value: int = 1
) -> list[str]:
    wrong_values = set()

    while len(wrong_values) < 3:
        offset = random.randint(-spread, spread)
        candidate = correct_value + offset

        if candidate != correct_value and candidate >= min_value:
            wrong_values.add(candidate)

    choices = [str(correct_value)] + [
        str(value) for value in wrong_values
    ]

    return choices


@router.get("/trivia/draft_player", response_model=DraftPlayerQuestion)
def guess_drafted_player():
    with db.cursor() as cursor:
        row = fetch_random_draft_row(cursor)

    if row is None:
        return {"error": "no draft history found"}

    (
        player_id,
        player_name,
        season,
        round_number,
        pick_number,
        overall_pick,
        organization
    ) = row

    question = (
        f"Who was drafted with the #{pick_number} pick of round "
        f"{round_number} in the {season} draft?"
    )

    question_id, choices = build_question_base(player_name)

    return DraftPlayerQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(player_name),
    )


@router.get("/trivia/overall_pick", response_model=OverallPickQuestion)
def guess_overall_pick():
    with db.cursor() as cursor:
        row = fetch_random_draft_row(cursor)

    if row is None:
        return {"error": "no draft history found"}

    (
        player_id,
        player_name,
        season,
        round_number,
        pick_number,
        overall_pick,
        organization
    ) = row

    question = (
        f"What overall pick was {player_name} selected with "
        f"in the {season} draft?"
    )

    choices = build_numeric_choices(
        overall_pick,
        spread=6,
        min_value=1
    )

    question_id = register_answer(str(overall_pick))

    return OverallPickQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(str(overall_pick)),
    )


@router.get("/trivia/draft_organization", response_model=OrganizationQuestion)
def guess_organization():
    with db.cursor() as cursor:
        row = fetch_random_draft_row(cursor)

        if row is None:
            return {"error": "no draft history found"}

        (
            player_id,
            player_name,
            season,
            round_number,
            pick_number,
            overall_pick,
            organization
        ) = row

        cursor.execute("""
            SELECT organization
            FROM draft
            WHERE
                organization IS NOT NULL
                AND organization != %s
            GROUP BY organization
            ORDER BY RANDOM()
            LIMIT 3
        """, (organization,))

        wrong_orgs = [r[0] for r in cursor.fetchall()]

    question = (
        f"What organization was {player_name} selected from "
        f"in the {season} draft?"
    )

    choices = [organization] + wrong_orgs

    question_id = register_answer(organization)

    return OrganizationQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(organization),
    )