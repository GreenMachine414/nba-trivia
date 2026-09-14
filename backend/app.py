from contextlib import asynccontextmanager
import time

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


@app.middleware("http")
async def log_request_time(request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = (time.monotonic() - start) * 1000
    print(f"TIMING: {request.method} {request.url.path} -> {elapsed:.0f}ms", flush=True)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://zippy-duckanoo-92b7f3.netlify.app"],
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

app.include_router(trivia.router)
app.include_router(auth.router)