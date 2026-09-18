"""
Screener API Router

Day 38 scaffold.
"""

from fastapi import APIRouter


router = APIRouter(
    prefix="/screener",
    tags=["Screener"],
)


@router.get(
    "",
    summary="Screener module",
)
def screener_root():
    """
    Screener API scaffold endpoint.
    """

    return {
        "module": "screener",
        "status": "ready",
        "message": "Screener API router is available.",
    }