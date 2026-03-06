"""Health check routes."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Basic health check."""
    return {"status": "ok", "service": "serhu-api"}
