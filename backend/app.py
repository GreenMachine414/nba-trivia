from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from data.database import db
import data.accounts.auth as auth
import trivia


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    yield
    db.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zippy-duckanoo-92b7f3.netlify.app/"],  # replace with your real frontend URL once deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trivia.router)
app.include_router(auth.router)