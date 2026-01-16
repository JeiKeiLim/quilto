# Story 8.2: Implement FastAPI Endpoints

Status: done

## Story

As a **Swealog user**,
I want **FastAPI endpoints for /input and /query**,
So that **I can interact with my fitness logs via HTTP API**.

## Acceptance Criteria

1. **AC1: FastAPI Application Setup**
   - Given the swealog.api module
   - When imported and used
   - Then a FastAPI application instance is available
   - And the app has CORS middleware configured for development
   - And the app has a `/health` endpoint returning `{"status": "ok"}`

2. **AC2: POST /input Endpoint**
   - Given a POST request to `/input` with body `{"text": "Bench 185x5 today"}`
   - When the request is processed
   - Then the input is routed through the Router agent
   - And LOG inputs are processed through the Parser agent
   - And the response includes `{"status": "accepted", "input_type": "LOG", "entry_id": "2026-01-16T14:30:00"}`
   - And parsing happens asynchronously (response returns before parsing completes)

3. **AC3: POST /query Endpoint**
   - Given a POST request to `/query` with body `{"text": "How's my bench progress?"}`
   - When the request is processed
   - Then the query flows through Router -> Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator
   - And the response includes `{"response": "...", "sources": [...], "confidence": 0.85}`
   - And partial responses are returned if max retries are exhausted

4. **AC4: Error Handling**
   - Given an error during processing
   - When the error occurs
   - Then appropriate HTTP status codes are returned (400 for validation, 500 for server errors)
   - And error responses include `{"error": "...", "detail": "..."}`
   - And errors are logged appropriately

5. **AC5: Async Processing Support**
   - Given async endpoints
   - When multiple requests are received concurrently
   - Then requests are processed concurrently using asyncio
   - And LLM calls use async patterns (acompletion)

## Tasks / Subtasks

- [x] Task 1: Add FastAPI dependencies to swealog (AC: 1)
  - [x] Add `fastapi>=0.115.0` to swealog/pyproject.toml dependencies
  - [x] Add `uvicorn[standard]>=0.32.0` to swealog/pyproject.toml dependencies
  - [x] Add `httpx>=0.28.0` to swealog/pyproject.toml dev-dependencies (for testing)
  - [x] Run `uv sync` to update lockfile

- [x] Task 2: Create swealog.api module structure (AC: 1)
  - [x] Create `packages/swealog/swealog/api/` directory
  - [x] Create `__init__.py` with exports
  - [x] Create `app.py` with base FastAPI application
  - [x] Configure CORS middleware with permissive settings for development
  - [x] Add `/health` endpoint returning `{"status": "ok"}`

- [x] Task 3: Define request/response models (AC: 2, 3, 4)
  - [x] Create `models.py` with Pydantic models
  - [x] `InputRequest`: text field (required, min_length=1)
  - [x] `InputResponse`: status, input_type, entry_id, message (optional)
  - [x] `QueryRequest`: text field (required, min_length=1)
  - [x] `QueryResponse`: response, sources, confidence, partial (optional)
  - [x] `ErrorResponse`: error, detail

- [x] Task 4: Implement POST /input endpoint (AC: 2, 5)
  - [x] Create `routes/input.py` with APIRouter
  - [x] Create endpoint handler accepting InputRequest
  - [x] Initialize Router agent with LLM client
  - [x] Route input through Router to determine input_type
  - [x] For LOG/BOTH: Create background task for Parser processing
  - [x] Return InputResponse with entry_id (timestamp-based)
  - [x] Handle CORRECTION input type appropriately

- [x] Task 5: Implement POST /query endpoint (AC: 3, 5)
  - [x] Create `routes/query.py` with APIRouter
  - [x] Create endpoint handler accepting QueryRequest
  - [x] Import all query pipeline agents from quilto.agents:
    - RouterAgent, PlannerAgent, RetrieverAgent, AnalyzerAgent, SynthesizerAgent, EvaluatorAgent
  - [x] Load domains from swealog.domains
  - [x] Initialize full agent pipeline (Router -> Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator)
  - [x] Execute query flow with retry logic
  - [x] Return QueryResponse with response, sources, confidence
  - [x] Handle partial responses when is_partial=True

- [x] Task 6: Implement dependency injection (AC: 2, 3)
  - [x] Create `dependencies.py` with FastAPI dependencies
  - [x] `get_llm_client()`: Returns configured LLMClient
  - [x] `get_storage()`: Returns configured StorageRepository
  - [x] `get_domains()`: Returns list of domain modules (GeneralFitness, Strength, Nutrition, Running, Swimming)
  - [x] Use lifespan context manager for startup/shutdown

- [x] Task 7: Add error handling middleware (AC: 4)
  - [x] Create custom exception handlers for ValueError, ValidationError, ConfigNotFoundError
  - [x] Return appropriate HTTP status codes (400, 500)
  - [x] Format error responses as ErrorResponse model
  - [x] Log errors with appropriate context

- [x] Task 8: Add API entry point (AC: 1)
  - [x] App exports via `swealog.api:app`
  - [x] Add CLI command: `swealog serve` that runs uvicorn

- [x] Task 9: Write unit tests (AC: 1-5)
  - [x] Create `packages/swealog/tests/test_api_app.py` - app creation, health endpoint, CORS
  - [x] Create `packages/swealog/tests/test_api_models.py` - request/response validation
  - [x] Create `packages/swealog/tests/test_api_dependencies.py` - dependency injection
  - [x] Create `packages/swealog/tests/test_api_routes.py` - /input and /query endpoints with mocked agents
  - [x] Use `httpx.AsyncClient` with `ASGITransport` for async endpoint testing
  - [x] 36 tests passing

## Dev Notes

### Project Identity (CRITICAL)

This story adds API to **Swealog** (the application), NOT Quilto. Following the pattern established in Story 8.1 where CLI was moved to Swealog.

**Quilto provides:** Agents, LLM client, storage interface, DomainModule base class, SessionState
**Swealog provides:** CLI, API, fitness domains, user-facing features

### Architecture Compliance

**File Location:** `packages/swealog/swealog/api/`

**Module Structure:**
```
swealog/api/
├── __init__.py       # Exports: app, all models
├── app.py            # FastAPI app with middleware, lifespan
├── models.py         # Pydantic request/response models
├── dependencies.py   # FastAPI dependency injection
└── routes/
    ├── __init__.py   # Exports routers
    ├── input.py      # POST /input endpoint
    └── query.py      # POST /query endpoint
```

### Dependencies

Add to swealog pyproject.toml:
```toml
dependencies = [
    "quilto",
    "typer>=0.15.0",
    "rich>=13.9.0",
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
]

[dependency-groups]
dev = [
    "httpx>=0.28.0",  # For async API testing with ASGITransport
    # ... other dev dependencies
]
```

### Code Patterns

**FastAPI App (app.py):**
```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from swealog.api.routes import input_router, query_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup/shutdown."""
    # Startup: Load config, initialize resources
    yield
    # Shutdown: Cleanup resources


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


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Include routers - endpoints define their own paths (/input, /query)
app.include_router(input_router, tags=["input"])
app.include_router(query_router, tags=["query"])
```

**Request/Response Models (models.py):**
```python
from pydantic import BaseModel, Field


class InputRequest(BaseModel):
    """Request body for /input endpoint."""
    text: str = Field(..., min_length=1, description="Raw input text")


class InputResponse(BaseModel):
    """Response for /input endpoint."""
    status: str = Field(..., description="Processing status: accepted, error")
    input_type: str = Field(..., description="Classified input type: LOG, QUERY, BOTH, CORRECTION")
    entry_id: str | None = Field(None, description="Entry ID for LOG inputs")
    message: str | None = Field(None, description="Additional message")


class QueryRequest(BaseModel):
    """Request body for /query endpoint."""
    text: str = Field(..., min_length=1, description="Query text")


class QueryResponse(BaseModel):
    """Response for /query endpoint."""
    response: str = Field(..., description="Generated response")
    sources: list[str] = Field(default_factory=list, description="Source entry IDs used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence")
    partial: bool = Field(False, description="True if response is partial due to insufficient data")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
```

**Dependencies (dependencies.py):**
```python
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from quilto import DomainModule, LLMClient, LLMConfig, StorageRepository, load_llm_config
from swealog.domains import (
    general_fitness,
    nutrition,
    running,
    strength,
    swimming,
)


@lru_cache
def get_llm_config() -> LLMConfig:
    """Load LLM configuration (cached)."""
    config_path = Path("llm-config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"LLM config not found: {config_path}")
    return load_llm_config(config_path)


def get_llm_client(
    config: Annotated[LLMConfig, Depends(get_llm_config)]
) -> LLMClient:
    """Get LLM client instance."""
    return LLMClient(config)


def get_storage() -> StorageRepository:
    """Get storage repository instance."""
    storage_path = Path("logs")
    storage_path.mkdir(parents=True, exist_ok=True)
    return StorageRepository(base_path=storage_path)


def get_domains() -> list[DomainModule]:
    """Get all available domain modules."""
    return [
        general_fitness,
        strength,
        nutrition,
        running,
        swimming,
    ]
```

**Input Endpoint (routes/input.py):**
```python
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends

from quilto import DomainModule, LLMClient, ParserAgent, RouterAgent, RouterInput, StorageRepository
from quilto.agents import DomainInfo

from swealog.api.dependencies import get_domains, get_llm_client, get_storage
from swealog.api.models import InputRequest, InputResponse

router = APIRouter()


async def parse_log_background(
    raw_input: str,
    entry_id: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
) -> None:
    """Background task to parse and store log entry."""
    # Save raw entry first
    await storage.save_entry(entry_id, raw_input, entry_type="raw")

    # Parse and save structured data
    parser = ParserAgent(llm_client)
    # ... parsing logic (use domains to select appropriate schema)


@router.post("/input", response_model=InputResponse)
async def process_input(
    request: InputRequest,
    background_tasks: BackgroundTasks,
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    storage: Annotated[StorageRepository, Depends(get_storage)],
    domains: Annotated[list[DomainModule], Depends(get_domains)],
) -> InputResponse:
    """Process user input (log, query, both, or correction)."""
    # Route input
    router_agent = RouterAgent(llm_client)
    domain_infos = [DomainInfo(name=d.name, description=d.description) for d in domains]
    router_input = RouterInput(raw_input=request.text, available_domains=domain_infos)

    router_output = await router_agent.classify(router_input)
    entry_id = datetime.now().isoformat()

    if router_output.input_type in ("LOG", "BOTH"):
        # Schedule background parsing
        background_tasks.add_task(
            parse_log_background,
            request.text,
            entry_id,
            llm_client,
            storage,
            domains,
        )

    return InputResponse(
        status="accepted",
        input_type=router_output.input_type,
        entry_id=entry_id if router_output.input_type in ("LOG", "BOTH") else None,
    )
```

**Query Endpoint (routes/query.py):**
```python
from typing import Annotated

from fastapi import APIRouter, Depends

from quilto import (
    DomainModule,
    LLMClient,
    SessionState,
    StorageRepository,
)
from quilto.agents import (
    AnalyzerAgent,
    DomainInfo,
    EvaluatorAgent,
    PlannerAgent,
    RetrieverAgent,
    RouterAgent,
    RouterInput,
    SynthesizerAgent,
)

from swealog.api.dependencies import get_domains, get_llm_client, get_storage
from swealog.api.models import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    storage: Annotated[StorageRepository, Depends(get_storage)],
    domains: Annotated[list[DomainModule], Depends(get_domains)],
) -> QueryResponse:
    """Process a user query through the full agent pipeline."""
    # Initialize agents
    router_agent = RouterAgent(llm_client)
    planner = PlannerAgent(llm_client)
    retriever = RetrieverAgent(llm_client, storage)
    analyzer = AnalyzerAgent(llm_client)
    synthesizer = SynthesizerAgent(llm_client)
    evaluator = EvaluatorAgent(llm_client)

    # Route query
    domain_infos = [DomainInfo(name=d.name, description=d.description) for d in domains]
    router_input = RouterInput(raw_input=request.text, available_domains=domain_infos)
    router_output = await router_agent.classify(router_input)

    # Initialize session state
    state: SessionState = {
        "raw_input": request.text,
        "input_type": router_output.input_type,
        "query": request.text,
        "retry_count": 0,
        "max_retries": 2,
        "is_partial": False,
        # ... additional state fields
    }

    # Execute query pipeline (simplified - actual implementation uses LangGraph)
    # planner_output = await planner.plan(...)
    # retrieved = await retriever.retrieve(...)
    # analysis = await analyzer.analyze(...)
    # response = await synthesizer.synthesize(...)
    # evaluation = await evaluator.evaluate(...)

    return QueryResponse(
        response=state.get("final_response", ""),
        sources=[],  # Extract from retrieved entries
        confidence=0.85,  # From evaluation
        partial=state.get("is_partial", False),
    )
```

### Testing with httpx

**Test Pattern (test_api_input.py):**
```python
import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from quilto.agents import RouterOutput
from swealog.api import app


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mock LLM client for testing."""
    client = AsyncMock()
    # Configure mock responses
    return client


@pytest.mark.asyncio
async def test_input_log_entry() -> None:
    """Test processing a LOG input."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        with patch("swealog.api.routes.input.get_llm_client") as mock_get:
            # Configure mock
            mock_client = AsyncMock()
            mock_client.complete_structured.return_value = RouterOutput(
                input_type="LOG",
                confidence=0.9,
                selected_domains=["strength"],
                domain_selection_reasoning="Fitness log",
            )
            mock_get.return_value = mock_client

            response = await client.post(
                "/input",
                json={"text": "Bench 185x5 today"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "accepted"
            assert data["input_type"] == "LOG"
            assert data["entry_id"] is not None
```

### CLI Integration

Add `serve` command to existing CLI (cli/commands.py or app.py):
```python
import typer

# In app.py or new commands.py
@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
) -> None:
    """Start the Swealog API server."""
    import uvicorn
    uvicorn.run(
        "swealog.api:app",
        host=host,
        port=port,
        reload=reload,
    )
```

### Previous Story Intelligence (Story 8.1)

From Story 8.1 implementation:
- CLI module is at `swealog/cli/` with modular structure (app.py, output.py, utils.py)
- Uses `importlib.metadata` for version retrieval
- `run_async` decorator pattern for async in sync context
- `load_cli_config()` wraps `quilto.llm.load_llm_config()`
- Entry point pattern: `[project.scripts]` in pyproject.toml
- 31 comprehensive tests covering all functionality

### Key Quilto Components to Use

From quilto package (already implemented):
- `RouterAgent`: Input classification (router.py)
- `ParserAgent`: Structured data extraction
- `PlannerAgent`: Query decomposition
- `RetrieverAgent`: Entry fetching
- `AnalyzerAgent`: Pattern analysis
- `SynthesizerAgent`: Response generation
- `EvaluatorAgent`: Quality checking
- `SessionState`: State management for query flow
- `StorageRepository`: File-based storage

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Before completion
make validate     # lint + format + typecheck + test

# Integration testing (requires Ollama)
make test-ollama
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.2] - Story requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#CLI-Future-Web] - FastAPI decision
- [Source: packages/quilto/quilto/agents/router.py] - RouterAgent pattern
- [Source: packages/quilto/quilto/state/session.py] - SessionState definition
- [Source: packages/swealog/swealog/cli/] - CLI module structure pattern

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented FastAPI application with CORS middleware and health endpoint
- Created Pydantic request/response models with proper validation
- POST /input endpoint routes through RouterAgent and schedules background parsing via BackgroundTasks
- POST /query endpoint implements full pipeline: Router -> Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator with retry logic
- Dependency injection for LLMClient, StorageRepository, and domains
- Custom exception handlers for ValueError, ValidationError, ConfigNotFoundError, and generic exceptions
- Added `swealog serve` CLI command using uvicorn
- 36 unit tests covering app, models, dependencies, and routes
- All 1614 workspace tests passing with `make validate`

### Code Review Fixes (2026-01-16)

- **H2 Fixed:** Corrected timestamp parsing bug in `parse_log_background` - changed from fragile string replacement to explicit `datetime.strptime` with format `%Y-%m-%d_%H-%M-%S` (routes/input.py:68)
- **M3 Fixed:** Added named constants `_CONFIDENCE_SUFFICIENT`, `_CONFIDENCE_PARTIAL`, `_CONFIDENCE_INSUFFICIENT`, `_CONFIDENCE_ADJUSTMENT` to replace magic numbers in confidence calculation (routes/query.py:40-44)

### File List

**New Files:**
- `packages/swealog/swealog/api/__init__.py`
- `packages/swealog/swealog/api/app.py`
- `packages/swealog/swealog/api/models.py`
- `packages/swealog/swealog/api/dependencies.py`
- `packages/swealog/swealog/api/routes/__init__.py`
- `packages/swealog/swealog/api/routes/input.py`
- `packages/swealog/swealog/api/routes/query.py`
- `packages/swealog/tests/test_api_app.py`
- `packages/swealog/tests/test_api_models.py`
- `packages/swealog/tests/test_api_dependencies.py`
- `packages/swealog/tests/test_api_routes.py`

**Modified Files:**
- `packages/swealog/pyproject.toml` - Added FastAPI, uvicorn dependencies
- `pyproject.toml` - Added httpx to dev dependencies
- `packages/swealog/swealog/cli/app.py` - Added `swealog serve` command
- `uv.lock` - Updated with new dependencies

