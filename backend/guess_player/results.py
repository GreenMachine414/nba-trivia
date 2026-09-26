from fastapi import APIRouter, Depends
from pydantic import BaseModel

from data.database import db
from data.accounts.auth import get_current_user

router = APIRouter()


class GuessPlayerResult(BaseModel):
    correct: bool
    rounds_used: int


class LeaderboardEntry(BaseModel):
    username: str
    games_played: int
    win_pct: float


class Leaderboard(BaseModel):
    by_win_pct: list[LeaderboardEntry]


@router.post("/guess-player/record")
def record_result(body: GuessPlayerResult, user_id: int = Depends(get_current_user)):
    with db.cursor() as cursor:
        cursor.execute(
            "INSERT INTO guess_player_results (user_id, correct, rounds_used) VALUES (%s, %s, %s)",
            (user_id, body.correct, body.rounds_used),
        )
    return {"status": "recorded"}


@router.get("/leaderboard/guess_player", response_model=Leaderboard)
def get_leaderboard():
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT u.username,
                   COUNT(*) AS games_played,
                   ROUND(100.0 * SUM(CASE WHEN gr.correct THEN 1 ELSE 0 END) / COUNT(*), 1) AS win_pct
            FROM guess_player_results gr
            JOIN users u ON u.id = gr.user_id
            GROUP BY u.username
            HAVING COUNT(*) >= 3
            ORDER BY win_pct DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()

    return Leaderboard(
        by_win_pct=[LeaderboardEntry(username=r[0], games_played=r[1], win_pct=r[2]) for r in rows]
    )