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


@router.post("/trivia/answer", response_model=TriviaResult)
def check_answer(guess: TriviaGuess):
    correct_answer = pop_answer(guess.question_id)

    if correct_answer is None:
        return {"error": "unknown or already-answered question_id"}

    return TriviaResult(
        correct=guess.guess == correct_answer,
        answer=correct_answer,
    )