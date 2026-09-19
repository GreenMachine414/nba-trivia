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
        SELECT d.player_id, p.player_name, d.season, d.round_number,
               d.round_pick, d.overall_pick, d.organization
        FROM draft_history d
        JOIN players p ON p.player_id = d.player_id
        WHERE d.organization IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 1
    """)