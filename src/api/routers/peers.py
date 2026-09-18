"""
Peers API Router

Day 38 scaffold.
"""

from fastapi import APIRouter


router = APIRouter(
    prefix="/peers",
    tags=["Peers"],
)


@router.get(
    "",
    summary="Peers module",
)
def peers_root():
    """
    Peers API scaffold endpoint.
    """

    return {
        "module": "peers",
        "status": "ready",
        "message": "Peers API router is available.",
    }