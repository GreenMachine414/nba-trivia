import random
import uuid

from data.database import db


def register_answer(answer: str) -> str:
    question_id = str(uuid.uuid4())
    db.ensure_connected()
    cursor = db.connection.cursor()
    cursor.execute(
        "INSERT INTO pending_answers (question_id, answer) VALUES (%s, %s)",
        (question_id, answer),
    )
    db.connection.commit()
    cursor.close()
    return question_id


def pop_answer(question_id: str) -> str | None:
    db.ensure_connected()
    cursor = db.connection.cursor()
    cursor.execute(
        "DELETE FROM pending_answers WHERE question_id = %s RETURNING answer",
        (question_id,),
    )
    row = cursor.fetchone()
    db.connection.commit()
    cursor.close()
    return row[0] if row else None


def build_question_base(player_name: str) -> tuple[str, list[str]]:
    db.ensure_connected()
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

    question_id = register_answer(player_name)

    return question_id, choices