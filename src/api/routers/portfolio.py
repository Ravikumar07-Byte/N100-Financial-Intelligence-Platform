"""
Portfolio API Router

Day 38 scaffold.
"""

from fastapi import APIRouter


router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"],
)


@router.get(
    "",
    summary="Portfolio module",
)
def portfolio_root():
    """
    Portfolio API scaffold endpoint.
    """

    return {
        "module": "portfolio",
        "status": "ready",
        "message": "Portfolio API router is available.",
    }