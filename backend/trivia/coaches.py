import random

from fastapi import APIRouter
from pydantic import BaseModel

from data.database import db

from .engine import build_question_base, register_answer, hash_answer

router = APIRouter()

QUESTION_TYPE = "Coaching Staff"


class CoachEntry(BaseModel):
    coach_name: str
    coach_type: str


class CoachingStaffQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    staff: list[CoachEntry]
    choices: list[str]
    answer_hash: str


class HeadCoachQuestion(BaseModel):
    question_id: str
    question_type: str
    question: str
    choices: list[str]
    answer_hash: str


@router.get("/trivia/coaching_staff", response_model=CoachingStaffQuestion)
def guess_coaching_staff():

    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT
            tc.team_id,
            tc.season_id,
            s.season_name,
            f.abbreviation
        FROM team_coach tc
        JOIN season s
            ON s.season_id = tc.season_id
        JOIN franchise f
            ON f.team_id = tc.team_id
        GROUP BY
            tc.team_id,
            tc.season_id,
            s.season_name,
            f.abbreviation
        HAVING COUNT(*) >= 2
        ORDER BY RANDOM()
        LIMIT 1
    """)

    row = cursor.fetchone()

    if row is None:
        cursor.close()
        return {
            "error":
                "no eligible coaching staffs found"
        }

    (
        team_id,
        season_id,
        season_name,
        correct_team
    ) = row

    cursor.execute("""
        SELECT
            c.full_name,
            tc.coach_type
        FROM team_coach tc
        JOIN coach c
            ON c.coach_id = tc.coach_id
        WHERE
            tc.team_id = %s
            AND tc.season_id = %s
        ORDER BY tc.sort_sequence
    """, (
        team_id,
        season_id
    ))

    staff_rows = cursor.fetchall()

    cursor.execute("""
        SELECT abbreviation
        FROM franchise
        WHERE team_id != %s
        ORDER BY RANDOM()
        LIMIT 3
    """, (team_id,))

    wrong_teams = [r[0] for r in cursor.fetchall()]

    cursor.close()

    if len(wrong_teams) < 3:
        return {
            "error":
                "not enough teams for choices"
        }

    staff = [
        CoachEntry(
            coach_name=name,
            coach_type=coach_type
        )
        for name, coach_type in staff_rows
    ]

    question = (
        f"Which team had this coaching staff "
        f"in the {season_name} season?"
    )

    choices = [
        correct_team
    ] + wrong_teams

    question_id = register_answer(
        correct_team
    )

    return CoachingStaffQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        staff=staff,
        choices=choices,
        answer_hash=hash_answer(
            correct_team
        ),
    )


@router.get("/trivia/head_coach", response_model=HeadCoachQuestion)
def guess_head_coach():

    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT
            c.full_name,
            s.season_name,
            f.abbreviation
        FROM team_coach tc
        JOIN coach c
            ON c.coach_id = tc.coach_id
        JOIN season s
            ON s.season_id = tc.season_id
        JOIN franchise f
            ON f.team_id = tc.team_id
        WHERE tc.coach_type = 'Head Coach'
        ORDER BY RANDOM()
        LIMIT 1
    """)

    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no head coach data found"}

    coach_name, season, team = row

    question = (
        f"Who was the head coach for the {team} "
        f"in the {season} season?"
    )

    question_id, choices = build_question_base(coach_name)

    return HeadCoachQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(coach_name),
    )