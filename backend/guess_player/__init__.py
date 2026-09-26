from fastapi import APIRouter

from . import game, results

router = APIRouter()
router.include_router(game.router)
router.include_router(results.router)