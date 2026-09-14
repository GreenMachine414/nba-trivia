from fastapi import APIRouter
from pydantic import BaseModel

from .engine import pop_answer

router = APIRouter()


class TriviaGuess(BaseModel):
    question_id: str
    guess: str


class TriviaResult(BaseModel):
    correct: bool
    answer: str


import time

@router.post("/trivia/answer", response_model=TriviaResult)
def check_answer(guess: TriviaGuess):
    t0 = time.monotonic()
    correct_answer = pop_answer(guess.question_id)
    t1 = time.monotonic()
    print(f"DB CALL TOOK: {(t1 - t0) * 1000:.0f}ms", flush=True)

    if correct_answer is None:
        return {"error": "unknown or already-answered question_id"}

    return TriviaResult(
        correct=guess.guess == correct_answer,
        answer=correct_answer,
    )