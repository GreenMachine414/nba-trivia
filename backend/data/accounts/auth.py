import secrets

import bcrypt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from data.database import db

router = APIRouter()


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    token: str
    username: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    db.ensure_connected()
    cursor = db.connection.cursor()
    cursor.execute(
        "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
        (token, user_id),
    )
    db.connection.commit()
    cursor.close()
    return token


def delete_session(token: str) -> None:
    db.ensure_connected()
    cursor = db.connection.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = %s", (token,))
    db.connection.commit()
    cursor.close()


def get_current_user(authorization: str = Header(default="")) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.removeprefix("Bearer ")

    db.ensure_connected()
    cursor = db.connection.cursor()
    cursor.execute("""
        SELECT user_id FROM sessions
        WHERE token = %s AND created_at > NOW() - INTERVAL '30 days'
    """, (token,))
    row = cursor.fetchone()
    cursor.close()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return row[0]


@router.post("/auth/signup", response_model=AuthResponse)
def signup(body: SignupRequest):
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute("SELECT id FROM users WHERE username = %s", (body.username,))
    if cursor.fetchone() is not None:
        cursor.close()
        raise HTTPException(status_code=400, detail="Username already taken")

    password_hash = hash_password(body.password)

    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
        (body.username, password_hash),
    )
    user_id = cursor.fetchone()[0]
    db.connection.commit()
    cursor.close()

    token = create_session(user_id)

    return AuthResponse(token=token, username=body.username)


@router.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    db.ensure_connected()
    cursor = db.connection.cursor()

    cursor.execute(
        "SELECT id, password_hash FROM users WHERE username = %s",
        (body.username,),
    )
    row = cursor.fetchone()
    cursor.close()

    if row is None or not verify_password(body.password, row[1]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_id, _ = row
    token = create_session(user_id)

    return AuthResponse(token=token, username=body.username)


@router.post("/auth/logout")
def logout(authorization: str = Header(default="")):
    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        delete_session(token)
    return {"status": "logged out"}