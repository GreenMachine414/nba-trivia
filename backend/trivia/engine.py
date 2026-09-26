import hashlib
import uuid

from data.database import db


def hash_answer(answer: str) -> str:
    return hashlib.sha256(answer.strip().lower().encode()).hexdigest()


def build_question_base(player_name: str) -> tuple[str, list[str]]:
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT name
            FROM (
                SELECT DISTINCT name
                FROM player
                WHERE name != %s
            ) AS distinct_names
            ORDER BY RANDOM()
            LIMIT 3
        """, (player_name,))
        wrong_answers = [r[0] for r in cursor.fetchall()]

    choices = [player_name] + wrong_answers
    question_id = str(uuid.uuid4())

    return question_id, choices


def register_answer(answer: str) -> str:
    return str(uuid.uuid4())