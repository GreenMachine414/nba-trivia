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
        SELECT c.team_id, c.season, c.coach_name, c.coach_type, t.abbreviation
        FROM coaches c
        JOIN teams t ON t.team_id = c.team_id
        WHERE (c.team_id, c.season) IN (
            SELECT team_id, season FROM coaches GROUP BY team_id, season HAVING COUNT(*) >= 2
        )
    """)
    all_rows = cursor.fetchall()

    if not all_rows:
        cursor.close()
        return {"error": "no eligible coaching staffs found"}

    grouped: dict[tuple, list[tuple]] = {}
    team_abbrev_for_group: dict[tuple, str] = {}
    for team_id, season, coach_name, coach_type, abbreviation in all_rows:
        key = (team_id, season)
        grouped.setdefault(key, []).append((coach_name, coach_type))
        team_abbrev_for_group[key] = abbreviation

    chosen_key = random.choice(list(grouped.keys()))
    team_id, season = chosen_key
    staff_rows = grouped[chosen_key]
    correct_team = team_abbrev_for_group[chosen_key]

    cursor.execute("""
        SELECT abbreviation FROM teams
        WHERE team_id != %s
        ORDER BY RANDOM()
        LIMIT 3
    """, (team_id,))
    wrong_teams = [r[0] for r in cursor.fetchall()]
    cursor.close()

    staff = [CoachEntry(coach_name=name, coach_type=ctype) for name, ctype in staff_rows]

    question = f"Which team had this coaching staff in the {season} season?"

    choices = [correct_team] + wrong_teams
    random.shuffle(choices)

    question_id = register_answer(correct_team)

    return CoachingStaffQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        staff=staff,
        choices=choices,
        answer_hash=hash_answer(correct_team),
    )


@router.get("/trivia/head_coach", response_model=HeadCoachQuestion)
def guess_head_coach():
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("""
        SELECT c.coach_name, c.season, t.abbreviation
        FROM coaches c
        JOIN teams t ON t.team_id = c.team_id
        WHERE c.coach_type = 'Head Coach'
        ORDER BY RANDOM()
        LIMIT 1
    """)
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        return {"error": "no head coach data found"}

    coach_name, season, team = row

    question = f"Who was the head coach for the {team} in the {season} season?"

    question_id, choices = build_question_base(coach_name)

    return HeadCoachQuestion(
        question_id=question_id,
        question_type=QUESTION_TYPE,
        question=question,
        choices=choices,
        answer_hash=hash_answer(coach_name),
    )