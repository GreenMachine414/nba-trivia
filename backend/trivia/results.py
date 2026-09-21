from fastapi import APIRouter, Depends
from pydantic import BaseModel

from data.database import db
from data.accounts.auth import get_current_user

router = APIRouter()


class UserStats(BaseModel):
    games_played: int
    average_score: float | None


class GameResult(BaseModel):
    score: int
    total_questions: int


class LeaderboardByGames(BaseModel):
    username: str
    games_played: int


class LeaderboardByScore(BaseModel):
    username: str
    average_score: float


class Leaderboard(BaseModel):
    by_games_played: list[LeaderboardByGames]
    by_average_score: list[LeaderboardByScore]


@router.get("/users/me/stats", response_model=UserStats)
def get_my_stats(user_id: int = Depends(get_current_user)):
    with db.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*), AVG(score)
            FROM trivia_game_results
            WHERE user_id = %s
            """,
            (user_id,),
        )

        games_played, average_score = cursor.fetchone()

    return UserStats(
        games_played=games_played,
        average_score=(
            round(float(average_score), 1)
            if average_score is not None
            else None
        ),
    )


@router.post("/games/record")
def record_game(
    body: GameResult,
    user_id: int = Depends(get_current_user)
):
    with db.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO trivia_game_results (
                user_id,
                score,
                total_questions
            )
            VALUES (%s, %s, %s)
            """,
            (user_id, body.score, body.total_questions),
        )

    return {"status": "recorded"}


@router.get("/leaderboard/nba_trivia", response_model=Leaderboard)
def get_nba_trivia_leaderboard():
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT
                u.username,
                COUNT(*) AS games_played
            FROM trivia_game_results gr
            JOIN users u
                ON u.id = gr.user_id
            GROUP BY u.username
            ORDER BY games_played DESC
            LIMIT 10
        """)

        by_games_played = [
            LeaderboardByGames(
                username=row[0],
                games_played=row[1]
            )
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                u.username,
                AVG(gr.score) AS average_score
            FROM trivia_game_results gr
            JOIN users u
                ON u.id = gr.user_id
            GROUP BY u.username
            ORDER BY average_score DESC
            LIMIT 10
        """)

        by_average_score = [
            LeaderboardByScore(
                username=row[0],
                average_score=round(float(row[1]), 1)
            )
            for row in cursor.fetchall()
        ]

    return Leaderboard(
        by_games_played=by_games_played,
        by_average_score=by_average_score,
    )