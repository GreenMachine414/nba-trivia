from fastapi import APIRouter

from . import career_path, stat_average, draft, identity, coaches, awards, results

router = APIRouter()
router.include_router(career_path.router)
router.include_router(stat_average.router)
router.include_router(draft.router)
router.include_router(identity.router)
router.include_router(coaches.router)
router.include_router(awards.router)
router.include_router(results.router)