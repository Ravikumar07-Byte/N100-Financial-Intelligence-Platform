"""
Sectors API Router

Day 38 scaffold.
"""

from fastapi import APIRouter


router = APIRouter(
    prefix="/sectors",
    tags=["Sectors"],
)


@router.get(
    "",
    summary="Sectors module",
)
def sectors_root():
    """
    Sectors API scaffold endpoint.
    """

    return {
        "module": "sectors",
        "status": "ready",
        "message": "Sectors API router is available.",
    }