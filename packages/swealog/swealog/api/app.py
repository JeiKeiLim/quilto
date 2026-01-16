"""FastAPI application with middleware and health endpoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from swealog.api.dependencies import ConfigNotFoundError
from swealog.api.models import ErrorResponse
from swealog.api.routes import input_router, query_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup/shutdown.

    Args:
        app: FastAPI application instance.

    Yields:
        Nothing. Context manager for startup/shutdown lifecycle.
    """
    # Startup: resources can be initialized here
    yield
    # Shutdown: cleanup can be done here


app = FastAPI(
    title="Swealog API",
    description="Fitness logging API powered by Quilto",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError exceptions.

    Args:
        request: The incoming request.
        exc: The ValueError exception.

    Returns:
        JSON response with error details and 400 status.
    """
    logger.warning("Validation error: %s", exc)
    error = ErrorResponse(error="validation_error", detail=str(exc))
    return JSONResponse(status_code=400, content=error.model_dump())


@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError exceptions.

    Args:
        request: The incoming request.
        exc: The ValidationError exception.

    Returns:
        JSON response with error details and 400 status.
    """
    logger.warning("Pydantic validation error: %s", exc)
    error = ErrorResponse(error="validation_error", detail=str(exc))
    return JSONResponse(status_code=400, content=error.model_dump())


@app.exception_handler(ConfigNotFoundError)
async def config_not_found_handler(request: Request, exc: ConfigNotFoundError) -> JSONResponse:
    """Handle ConfigNotFoundError exceptions.

    Args:
        request: The incoming request.
        exc: The ConfigNotFoundError exception.

    Returns:
        JSON response with error details and 500 status.
    """
    logger.error("Configuration error: %s", exc)
    error = ErrorResponse(error="configuration_error", detail=str(exc))
    return JSONResponse(status_code=500, content=error.model_dump())


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions.

    Args:
        request: The incoming request.
        exc: The exception.

    Returns:
        JSON response with error details and 500 status.
    """
    logger.exception("Unhandled exception: %s", exc)
    error = ErrorResponse(error="internal_error", detail=f"An unexpected error occurred: {type(exc).__name__}")
    return JSONResponse(status_code=500, content=error.model_dump())


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status dict indicating API is healthy.
    """
    return {"status": "ok"}


# Include routers - endpoints define their own paths (/input, /query)
app.include_router(input_router, tags=["input"])
app.include_router(query_router, tags=["query"])
