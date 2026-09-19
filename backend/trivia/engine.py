import hashlib
import random
import uuid

from data.database import db


def hash_answer(answer: str) -> str:
    return hashlib.sha256(answer.strip().lower().encode()).hexdigest()


def build_question_base(player_name: str) -> tuple[str, list[str]]:
    """Builds a question_id (just a UUID for tracking/display) and the
    choices list. The actual answer is verified via hash client-side now,
    not looked up server-side, so callers must also call hash_answer(...)
    themselves and include it in their response."""
    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT player_name
        FROM (
            SELECT DISTINCT player_name
            FROM players
            WHERE player_name != %s
        ) AS distinct_names
        ORDER BY RANDOM()
        LIMIT 3
    """, (player_name,))
    wrong_answers = [r[0] for r in cursor.fetchall()]
    cursor.close()

    choices = [player_name] + wrong_answers
    random.shuffle(choices)

    question_id = str(uuid.uuid4())

    return question_id, choices


def register_answer(answer: str) -> str:
    """Generates a question_id for display/tracking purposes only. No
    longer persists anything server-side - the hash travels with the
    response instead, and correctness is checked client-side."""
    return str(uuid.uuid4())