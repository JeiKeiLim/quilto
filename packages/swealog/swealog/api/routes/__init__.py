"""API route handlers for Swealog."""

from swealog.api.routes.input import router as input_router
from swealog.api.routes.query import router as query_router

__all__ = [
    "input_router",
    "query_router",
]
