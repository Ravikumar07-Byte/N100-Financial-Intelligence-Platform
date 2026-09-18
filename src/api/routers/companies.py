"""
Companies API Router

Day 38 scaffold.
"""

from fastapi import APIRouter


router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
)


@router.get(
    "",
    summary="Companies module",
)
def companies_root():
    """
    Companies API scaffold endpoint.
    """

    return {
        "module": "companies",
        "status": "ready",
        "message": "Companies API router is available.",
    }