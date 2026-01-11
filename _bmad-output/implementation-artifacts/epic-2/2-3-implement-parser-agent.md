# Story 2.3: Implement Parser Agent

Status: review

## Story

As a **Quilto developer**,
I want a **Parser agent that extracts structured data from raw input**,
So that **entries can be stored in both raw and parsed formats**.

## Acceptance Criteria

1. **Given** a LOG input and active domain context with one or more domain schemas
   **When** Parser processes it
   **Then** raw content is preserved exactly in the output
   **And** structured data is extracted using each domain's `log_schema`
   **And** `domain_data` contains parsed output for each relevant domain

2. **Given** raw input with a timestamp
   **When** Parser extracts structured data
   **Then** `date` is extracted from input or defaults to timestamp date
   **And** `timestamp` is set from the provided timestamp
   **And** `tags` are extracted from content when present

3. **Given** a domain vocabulary mapping
   **When** Parser encounters terms in the input
   **Then** terms are normalized using vocabulary (e.g., "bench" → "bench press")
   **And** normalization is applied before schema extraction

4. **Given** ambiguous or uncertain data in the input
   **When** Parser cannot confidently extract a field
   **Then** `uncertain_fields` lists the ambiguous field names
   **And** `extraction_notes` explains what was ambiguous
   **And** `confidence` score reflects overall extraction quality (0.0 to 1.0)

5. **Given** multiple domains are selected for parsing
   **When** Parser processes the input
   **Then** each domain's schema is applied independently
   **And** `domain_data` contains one entry per domain that successfully extracted data
   **And** domains with no matching data return empty or minimal structure

6. **Given** Parser is configured with model tier "medium"
   **When** an LLM call is made
   **Then** the correct medium-tier model is used via LLMClient

7. **Given** raw input that is empty or whitespace-only
   **When** Parser.parse() is called
   **Then** it raises `ValueError` with descriptive message
   **And** no LLM call is made

8. **Given** CORRECTION mode is enabled with a correction_target hint
   **When** Parser processes the input
   **Then** `is_correction` is set to True
   **And** `target_entry_id` identifies the entry being corrected (from recent_entries)
   **And** `correction_delta` contains only the fields that changed

9. **Given** a ParserOutput model
   **When** validating the output
   **Then** `confidence` must be between 0.0 and 1.0
   **And** `domain_data` must be a dict (can be empty)
   **And** `raw_content` must not be empty

## Tasks / Subtasks

- [x] Task 1: Extend agents/models.py with Parser types (AC: #1-5, #8-9)
  - [x] Define `ParserInput` model with fields: raw_input, timestamp, domain_schemas, vocabulary, global_context, recent_entries, correction_mode, correction_target
  - [x] Define full `ParserOutput` model with fields: date, timestamp, tags, domain_data, raw_content, confidence, extraction_notes, uncertain_fields, is_correction, target_entry_id, correction_delta
  - [x] Add `@model_validator` for ParserOutput to validate required fields (raw_content non-empty, confidence range)
  - [x] Keep `ParserOutput` stub in `storage/models.py` as-is (Option A: minimal disruption - stub is sufficient for StorageRepository's correction fields only)
  - [x] Add strict Pydantic validation with `ConfigDict(strict=True)` and `arbitrary_types_allowed=True` for domain_schemas field

- [x] Task 2: Create parser.py with ParserAgent class (AC: #1-7)
  - [x] Create `packages/quilto/quilto/agents/parser.py`
  - [x] Define `AGENT_NAME = "parser"` for tier resolution (medium tier)
  - [x] Accept `llm_client: LLMClient` in constructor
  - [x] Implement `async parse(input: ParserInput) -> ParserOutput`
  - [x] Add validation for empty/whitespace raw_input at start of parse() (AC: #7)
  - [x] Make `build_prompt()` method public (not `_build_prompt`) for testability - follows Story 2.2 pattern

- [x] Task 3: Implement parsing prompt template (AC: #1-5)
  - [x] Build system prompt with vocabulary normalization rules
  - [x] Include domain schema descriptions (JSON schema from Pydantic models)
  - [x] Add extraction rules from agent-system-design.md Section 12.9
  - [x] Handle multi-domain extraction instructions
  - [x] Include global_context and recent_entries for context

- [x] Task 4: Implement vocabulary normalization (AC: #3)
  - [x] Pass vocabulary to LLM prompt for term normalization
  - [x] Vocabulary is applied by LLM during extraction (not pre-processing)

- [x] Task 5: Implement correction mode logic (AC: #8)
  - [x] Detect correction_mode flag in ParserInput
  - [x] Include correction_target hint in prompt
  - [x] Include recent_entries for target identification
  - [x] Extract correction_delta (what changed vs target)
  - [x] Set target_entry_id from identified entry

- [x] Task 6: Add comprehensive tests (AC: #1-9)
  - [x] Test single domain parsing with schema extraction
  - [x] Test multi-domain parsing with independent extraction
  - [x] Test vocabulary normalization in extraction
  - [x] Test uncertain_fields and extraction_notes population
  - [x] Test confidence score is in valid range [0.0, 1.0]
  - [x] Test confidence below 0.0 raises ValidationError
  - [x] Test confidence above 1.0 raises ValidationError
  - [x] Test empty raw_input raises ValueError (AC: #7)
  - [x] Test whitespace-only raw_input raises ValueError (AC: #7)
  - [x] Test empty raw_content raises ValidationError (AC: #9)
  - [x] Test domain_data type validation (must be dict)
  - [x] Test correction mode with target identification
  - [x] Test correction mode with delta extraction
  - [x] Test ParserOutput validation: raw_content required (non-empty)
  - [x] Test ParserOutput validation: confidence range edge cases
  - [x] Use existing mock_llm fixture from `tests/conftest.py` for isolated testing
  - [x] Add integration test using existing `--use-real-ollama` pytest hook from conftest.py
  - [x] Use test corpus entries from `tests/corpus/fitness/` and `tests/corpus/multi_domain/` for realistic test data

- [x] Task 7: Export from quilto package (AC: all)
  - [x] Add ParserAgent to `quilto/agents/__init__.py`
  - [x] Add ParserInput, ParserOutput to exports
  - [x] Update `quilto/__init__.py` with parser exports
  - [x] Verify `__all__` is complete
  - [x] Verify `py.typed` marker exists in agents directory (already created in Story 2.2)

## Dev Notes

### Project Structure

**Location:** `packages/quilto/quilto/agents/`

```
packages/quilto/quilto/agents/
├── __init__.py       # Exports: RouterAgent, ParserAgent, InputType, etc.
├── models.py         # Shared agent types including ParserInput, ParserOutput
├── router.py         # RouterAgent (implemented in Story 2.2)
├── parser.py         # ParserAgent class (this story)
└── py.typed          # PEP 561 marker (created in Story 2.2 code review fix)
```

**Existing Test Infrastructure (from Story 2.2):**
- `packages/quilto/tests/conftest.py` - Contains pytest hooks including `--use-real-ollama`

**Test Location:** `packages/quilto/tests/test_parser.py`

### Model Definitions

**From agent-system-design.md Section 11.9:**

```python
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ParserInput(BaseModel):
    """Input to Parser agent.

    Attributes:
        raw_input: The raw user input text to parse.
        timestamp: Timestamp when the entry was created.
        domain_schemas: Map of domain names to their Pydantic schema classes.
        vocabulary: Term normalization mapping for extraction.
        global_context: Optional global context for inference.
        recent_entries: Recent entries for correction mode target identification.
        correction_mode: Whether this is a correction to existing entry.
        correction_target: Natural language hint about what's being corrected.
    """

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    raw_input: str
    timestamp: datetime

    domain_schemas: dict[str, type[BaseModel]]  # {"domain_name": SchemaClass}
    vocabulary: dict[str, str]

    global_context: str | None = None
    recent_entries: list[Any] = []  # List of Entry objects

    correction_mode: bool = False
    correction_target: str | None = None


class ParserOutput(BaseModel):
    """Output from Parser agent.

    Attributes:
        date: Date of the entry.
        timestamp: Full timestamp of the entry.
        tags: Extracted tags from content.
        domain_data: Domain-specific parsed data, one entry per domain.
        raw_content: Original raw input (preserved exactly).
        confidence: Overall extraction confidence (0.0 to 1.0).
        extraction_notes: Notes about ambiguities or assumptions made.
        uncertain_fields: List of field names with uncertain extraction.
        is_correction: Whether this is a correction output.
        target_entry_id: ID of entry being corrected (if correction).
        correction_delta: Fields that changed (if correction).
    """

    model_config = ConfigDict(strict=True)

    date: date
    timestamp: datetime
    tags: list[str] = []

    domain_data: dict[str, Any]  # {"domain_name": parsed_model_dict}

    raw_content: str

    confidence: float = Field(ge=0.0, le=1.0)
    extraction_notes: list[str] = []
    uncertain_fields: list[str] = []

    is_correction: bool = False
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "ParserOutput":
        """Validate that raw_content is not empty.

        Returns:
            The validated ParserOutput instance.

        Raises:
            ValueError: If raw_content is empty.
        """
        if not self.raw_content:
            raise ValueError("raw_content cannot be empty")
        return self
```

### Parser Prompt Template

**From agent-system-design.md Section 12.9:**

```
ROLE: You are a structured extraction agent that converts freeform logs into structured data.

TASK: Extract structured data from the user's input using the provided domain schemas.

=== VOCABULARY ===
Use this to normalize terms:
{vocabulary}

Example: If user writes "bp", normalize to "blood pressure" if vocabulary maps it.

=== DOMAIN SCHEMAS ===
Extract data according to these schemas:
{domain_schemas_description}

=== EXTRACTION RULES ===

1. PRESERVE raw input exactly in raw_content field
2. NORMALIZE terms using vocabulary
3. EXTRACT only what is explicitly stated or clearly implied
4. NEVER invent data that isn't in the input
5. Mark uncertain extractions in uncertain_fields
6. Set confidence based on extraction clarity
7. Add extraction_notes for ambiguities or assumptions

=== MULTI-DOMAIN EXTRACTION ===

If multiple domain schemas are provided, extract independently for each.
An input may match multiple domains (e.g., mentions both activity and meal).

=== INPUT ===

Raw input: {raw_input}
Timestamp: {timestamp}
Global context (for inference): {global_context}
Recent entries (for context): {recent_entries}

=== OUTPUT (JSON) ===
{ParserOutput.model_json_schema()}
```

### ParserAgent Class Structure

```python
class ParserAgent:
    """Parser agent for extracting structured data from raw input.

    Converts freeform user input into structured entries using domain
    schemas. Supports multi-domain parsing, vocabulary normalization,
    and correction mode for updating existing entries.

    Attributes:
        llm_client: The LLM client for making inference calls.
    """

    AGENT_NAME = "parser"  # Used for tier resolution (medium tier)

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Parser agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def build_prompt(self, input: ParserInput) -> str:
        """Build the system prompt with extraction rules.

        Args:
            input: ParserInput with schemas, vocabulary, and context.

        Returns:
            The formatted system prompt string.
        """
        ...

    async def parse(self, input: ParserInput) -> ParserOutput:
        """Parse raw input and extract structured data.

        Args:
            input: ParserInput with raw_input, domain_schemas, etc.

        Returns:
            ParserOutput with extracted data per domain.

        Raises:
            ValueError: If raw_input is empty or whitespace-only.
        """
        if not input.raw_input or not input.raw_input.strip():
            raise ValueError("raw_input cannot be empty or whitespace-only")
        ...
```

### Agent Tier Configuration

Parser uses **medium** tier (structured extraction requires moderate capability):

```yaml
# In llm-config.yaml
agents:
  parser:
    tier: medium
```

### Multi-Domain Parsing Example

```python
# Input: "Had coffee and toast for breakfast, then went for a 5k run"
# Selected domains: ["nutrition", "cardio"]

parser_input = ParserInput(
    raw_input="Had coffee and toast for breakfast, then went for a 5k run",
    timestamp=datetime.now(),
    domain_schemas={
        "nutrition": NutritionEntry,  # Pydantic model
        "cardio": CardioEntry,  # Pydantic model
    },
    vocabulary={
        "5k": "5 kilometers",
        "toast": "toast",
    },
)

parser_output = await parser.parse(parser_input)

# Expected output:
parser_output.domain_data = {
    "nutrition": {"meal_type": "breakfast", "items": ["coffee", "toast"]},
    "cardio": {"activity": "run", "distance_km": 5.0}
}
```

### Correction Mode Flow

When `correction_mode=True`:

1. Parser receives `correction_target` hint (from Router)
2. Parser receives `recent_entries` to find the target
3. LLM identifies which entry is being corrected
4. LLM extracts only the delta (what changed)
5. Output sets `is_correction=True`, `target_entry_id`, `correction_delta`

**Note on `recent_entries` type:**
- Type is `list[Any]` to allow flexibility
- In practice, these are `Entry` objects from `quilto.storage.models`
- For prompt formatting, serialize each entry as: `{id}, {date}, {raw_content summary}`
- Parser doesn't store - it just identifies the target. Orchestrator handles actual correction storage.

```python
# Example correction input
parser_input = ParserInput(
    raw_input="Actually that was 185 not 85",
    timestamp=datetime.now(),
    domain_schemas={"strength": StrengthEntry},
    vocabulary={"bench": "bench press"},
    correction_mode=True,
    correction_target="bench weight recorded as 85",
    recent_entries=[entry_from_this_morning],  # Contains "bench 85x5"
)

# Expected output
parser_output.is_correction = True
parser_output.target_entry_id = "2026-01-11_08-30-00"
parser_output.correction_delta = {"weight_kg": 185}  # Only the changed field
```

### Testing Requirements

**Test Class Organization:**
```python
class TestParserBasicExtraction:
    """Tests for basic structured data extraction."""

    async def test_single_domain_extraction(self, mock_llm): ...
    async def test_multi_domain_extraction(self, mock_llm): ...
    async def test_raw_content_preserved(self, mock_llm): ...
    async def test_date_extracted_from_input(self, mock_llm): ...
    async def test_timestamp_set_from_input(self, mock_llm): ...
    async def test_tags_extracted(self, mock_llm): ...


class TestVocabularyNormalization:
    """Tests for vocabulary term normalization."""

    async def test_vocabulary_terms_normalized(self, mock_llm): ...
    async def test_vocabulary_empty_still_works(self, mock_llm): ...


class TestUncertaintyHandling:
    """Tests for uncertain field and confidence handling."""

    async def test_uncertain_fields_populated(self, mock_llm): ...
    async def test_extraction_notes_for_ambiguity(self, mock_llm): ...
    async def test_confidence_reflects_clarity(self, mock_llm): ...
    async def test_confidence_in_valid_range(self, mock_llm): ...


class TestCorrectionMode:
    """Tests for correction mode parsing."""

    async def test_correction_mode_identifies_target(self, mock_llm): ...
    async def test_correction_delta_extracted(self, mock_llm): ...
    async def test_is_correction_flag_set(self, mock_llm): ...


class TestParserInputValidation:
    """Tests for ParserInput validation."""

    async def test_empty_raw_input_raises_value_error(self): ...
    async def test_whitespace_only_raw_input_raises_value_error(self): ...


class TestParserOutputValidation:
    """Tests for ParserOutput validation."""

    def test_confidence_below_zero_raises_validation_error(self): ...
    def test_confidence_above_one_raises_validation_error(self): ...
    def test_confidence_boundary_zero_succeeds(self): ...
    def test_confidence_boundary_one_succeeds(self): ...
    def test_empty_raw_content_raises_validation_error(self): ...
    def test_whitespace_only_raw_content_raises_validation_error(self): ...
    def test_domain_data_is_dict(self): ...
    def test_domain_data_can_be_empty_dict(self): ...


class TestParserIntegration:
    """Integration tests with real LLM (skipped by default).

    Run with: pytest --use-real-ollama -k TestParserIntegration

    Note: Uses pytest marker from conftest.py, NOT pytest.config.getoption()
    which is deprecated. The conftest.py already has the proper hook.
    """

    @pytest.mark.ollama_integration
    async def test_real_fitness_extraction(self, real_llm_client): ...

    @pytest.mark.ollama_integration
    async def test_real_multi_domain_extraction(self, real_llm_client): ...
```

### Integration with StorageRepository

Parser output integrates with StorageRepository from Story 2.1.

**Important:** Parser itself does NOT call StorageRepository. The orchestration layer (state machine in Epic 3+) handles storage. Parser only returns structured output.

```python
from quilto.storage import Entry, StorageRepository

# After parsing (in orchestrator, not in Parser)
parser_output = await parser.parse(parser_input)

# Orchestrator creates Entry for storage
entry = Entry(
    id=f"{parser_output.date}_{parser_output.timestamp.strftime('%H-%M-%S')}",
    date=parser_output.date,
    timestamp=parser_output.timestamp,
    raw_content=parser_output.raw_content,
    parsed_data=parser_output.domain_data,
)

# Orchestrator saves via StorageRepository
await storage.save_entry(entry)
```

### ParserOutput Stub Migration

**Current stub in storage/models.py:**
```python
class ParserOutput(BaseModel):
    """Stub for Parser agent output - full definition in Epic 2 Story 3."""
    is_correction: bool = False
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None
```

**Migration Options:**
1. **Option A (Recommended):** Keep stub for now, StorageRepository only uses correction fields
2. **Option B:** Import full ParserOutput from agents/models.py in storage/models.py
3. **Option C:** Move ParserOutput entirely to agents/models.py, update storage imports

Choose Option A for minimal disruption. The stub is sufficient for StorageRepository's `save_entry` method which only uses correction fields.

### Validation Commands

Run frequently during development:
```bash
# Quick validation
uv run ruff check . --fix && uv run pyright

# Full validation (before commits)
uv run ruff check . && uv run ruff format . && uv run pyright && uv run pytest
```

### Previous Story Learnings (Story 2.2)

**Patterns to Follow:**
- Use `ConfigDict(strict=True)` for all Pydantic models
- Add `arbitrary_types_allowed=True` for models with type[BaseModel] fields
- Google-style docstrings for all public classes/methods (required for ruff pydocstyle)
- Comprehensive test coverage with edge cases
- Export all public classes in `__all__`
- Make prompt builder method public (`build_prompt`) for testability
- Use `@model_validator` for cross-field validation
- Use `Field(ge=0.0, le=1.0)` for confidence score validation

**Code Review Fixes Applied in 2.2 (Apply These Proactively):**
- py.typed marker added to agents directory (already exists - just verify)
- Proper conftest.py with pytest hooks for integration tests (already exists - reuse it)
- Empty string validation tests (not just None) - test both "" and "   "
- Edge case tests for all scenarios (domain selection, missing fields, boundary values)
- Test class organization by functionality (e.g., TestParserBasicExtraction, TestVocabularyNormalization)

**Code Review Common Issues to Avoid:**
- Missing tests for empty string vs None distinction
- Forgetting edge case tests (boundary values, empty collections)
- Not testing validation error messages
- Missing Google-style docstrings on any public method

### Architecture Compliance

**From architecture.md:**
- Parser is medium-tier agent (structured extraction)
- Uses LiteLLM via LLMClient abstraction
- Returns structured Pydantic output
- Part of LOG flow: PARSE state → STORE state

**State Machine Position (from state-machine-diagram.md):**
```
BUILD_CONTEXT → PARSE (if LOG or BOTH)
PARSE → STORE
STORE → OBSERVE
```

Parser operates in the LOG path, converting raw input to structured entries before storage.

### Error Handling

| Error Case | Handling |
|------------|----------|
| LLM returns invalid JSON | LLMClient raises ValueError with details |
| Empty raw_input | Raise ValueError immediately (in ParserAgent.parse) |
| Whitespace-only raw_input | Raise ValueError immediately (treated same as empty) |
| No domains match input | Return empty domain_data (valid case) |
| Correction target not found | Set target_entry_id to None, extraction_notes explains |
| Schema validation fails | LLMClient handles schema validation errors |

### Test Corpus Usage

The test corpus created in Epic 1.5 provides expected parser outputs. Use these for realistic test data:

```
tests/corpus/
├── fitness/
│   ├── entries/from_csv/        # 93 entries from Strong CSV (ground truth)
│   ├── entries/human/           # 15 human-curated entries (Story 1.5-7)
│   └── expected/parser/         # Expected parser outputs
├── multi_domain/
│   ├── entries/                 # 30+ non-fitness entries (Journal, Cooking, Study)
│   └── expected/parser/         # Expected outputs per domain
├── generic/
│   ├── edge_cases/              # 20+ edge case entries (empty, unicode, injection)
│   └── multilingual/            # 15+ multilingual entries
└── schemas/                     # Test domain schemas (JournalEntry, CookingEntry, etc.)
```

**Recommended Test Data Usage:**
- **Unit tests:** Use mock_llm fixture with canned responses
- **Accuracy tests:** Load entries from `tests/corpus/fitness/entries/`
- **Multi-domain tests:** Use entries from `tests/corpus/multi_domain/entries/`
- **Edge case tests:** Use entries from `tests/corpus/generic/edge_cases/`
- **Integration tests:** Run with `--use-real-ollama` against corpus entries

### Domain Schema Access

Parser receives domain schemas as `dict[str, type[BaseModel]]`. To generate JSON schema for the LLM prompt:

```python
def _format_domain_schemas(self, schemas: dict[str, type[BaseModel]]) -> str:
    """Format domain schemas for LLM prompt."""
    descriptions = []
    for name, schema_class in schemas.items():
        json_schema = schema_class.model_json_schema()
        descriptions.append(f"### {name}\n{json.dumps(json_schema, indent=2)}")
    return "\n\n".join(descriptions)
```

### References

- [Source: agent-system-design.md#11.9] Parser Agent Interface
- [Source: agent-system-design.md#12.9] Parser Prompt
- [Source: agent-system-design.md#5.5] CORRECTION handling (append strategy)
- [Source: architecture.md#Key-Architectural-Decisions] Raw/Parsed separation
- [Source: project-context.md] Quilto vs Swealog separation
- [Source: 2-2-implement-router-agent-log-classification.md] Previous story patterns

---

## SM Validation Notes (2026-01-11)

**Validator:** Bob (SM Agent) via Claude Opus 4.5

**Validation Result:** APPROVED with improvements applied

**Improvements Applied:**
1. **H1** - Clarified py.typed marker verification (already exists from Story 2.2)
2. **H4** - Made `build_prompt()` public method explicit in Task 2
3. **H5** - Added existing conftest.py reference and test infrastructure notes
4. **M1** - Fixed deprecated `pytest.config.getoption()` pattern to use `@pytest.mark.ollama_integration`
5. **M2** - Added explicit domain_data type validation tests
6. **M3** - Clarified Parser doesn't call storage (orchestrator's responsibility)
7. **M4** - Added note about recent_entries type and serialization for prompts
8. **M5** - Clarified stub migration decision (Option A: keep stub)
9. **L1** - Added docstring requirement to patterns
10. **L2** - Expanded test corpus usage section with specific file references

**Additional Tests Added:**
- Confidence boundary tests (0.0 and 1.0)
- Whitespace-only raw_content validation
- domain_data type and empty dict tests
- Multi-domain integration test with real LLM

**Task Subtask Additions:**
- Explicit `arbitrary_types_allowed=True` for ParserInput
- Verify py.typed marker exists
- Use test corpus for realistic test data

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None required - implementation proceeded without issues.

### Completion Notes List

1. **ParserInput model** - Implemented with all required fields including domain_schemas (type[BaseModel] dict), vocabulary mapping, correction mode support. Uses `ConfigDict(strict=True, arbitrary_types_allowed=True)`.

2. **ParserOutput model** - Full model with date, timestamp, tags, domain_data, raw_content, confidence (0.0-1.0 range validation), extraction_notes, uncertain_fields, and correction fields. Uses `@model_validator` to ensure raw_content is non-empty.

3. **ParserAgent class** - Created with AGENT_NAME = "parser" (medium tier), public `build_prompt()` method, and async `parse()` method with empty/whitespace input validation.

4. **Prompt template** - Comprehensive system prompt including vocabulary normalization, domain schema JSON descriptions, extraction rules, multi-domain instructions, and correction mode section when enabled.

5. **Comprehensive tests** - 36 tests covering:
   - ParserOutput validation (confidence range, raw_content non-empty)
   - ParserInput validation (required fields, optional defaults)
   - Basic extraction (single/multi domain, raw content preservation, tags)
   - Vocabulary normalization
   - Uncertainty handling (uncertain_fields, extraction_notes, confidence)
   - Correction mode (target identification, delta extraction)
   - Input validation (empty/whitespace raises ValueError)
   - Prompt building
   - Integration tests (skipped by default, require --use-real-ollama)

6. **Exports** - ParserAgent, ParserInput, ParserOutput exported from quilto.agents and quilto.__init__. py.typed marker verified.

### File List

**Created:**
- packages/quilto/quilto/agents/parser.py

**Modified:**
- packages/quilto/quilto/agents/models.py (added ParserInput, ParserOutput)
- packages/quilto/quilto/agents/__init__.py (added exports)
- packages/quilto/quilto/__init__.py (added exports, switched ParserOutput to agents version)
- packages/quilto/tests/test_parser.py (created comprehensive test suite)

**Unchanged:**
- packages/quilto/quilto/storage/models.py (stub kept as Option A per story)
- packages/quilto/quilto/agents/py.typed (already exists from Story 2.2)

