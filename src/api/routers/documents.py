"""
Documents API Router

Day 38 scaffold.
"""

from fastapi import APIRouter


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


@router.get(
    "",
    summary="Documents module",
)
def documents_root():
    """
    Documents API scaffold endpoint.
    """

    return {
        "module": "documents",
        "status": "ready",
        "message": "Documents API router is available.",
    }