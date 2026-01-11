# Story 2.5: Create Nutrition Domain Module

Status: done

## Story

As a **Swealog developer**,
I want a **Nutrition subdomain with schema and vocabulary**,
So that **food and meal logs are parsed correctly**.

## Acceptance Criteria

1. **Given** input like "lunch: chicken salad ~500cal, protein shake 30g protein"
   **When** parsed with Nutrition domain
   **Then** schema extracts meal_type, food_items, calories, and macros (protein, carbs, fat)
   **And** vocabulary normalizes common terms ("cal" → "calories", "g protein" → "grams protein")
   **And** parsed JSON includes all structured fields

2. **Given** the Nutrition domain module is defined
   **When** I instantiate it
   **Then** all DomainModule fields are populated (description, log_schema, vocabulary, expertise)
   **And** `name` defaults to "Nutrition" (class name)
   **And** `response_evaluation_rules` provides nutrition-specific guidance
   **And** `context_management_guidance` tracks nutrition-relevant patterns

3. **Given** a nutrition log with meal timing
   **When** parsed with NutritionEntry schema
   **Then** common meal types are handled: "breakfast", "lunch", "dinner", "snack"
   **And** time formats are handled: "8am", "12:30", "around noon"
   **And** date context is captured if provided

4. **Given** input with calorie/macro variations
   **When** vocabulary normalization is applied
   **Then** calorie abbreviations normalize correctly (e.g., "cal" → "calories", "kcal" → "calories")
   **And** macro abbreviations normalize correctly (e.g., "p" → "protein", "c" → "carbs", "f" → "fat")
   **And** unit variations handled (e.g., "g protein" → "grams protein", "30g" → "30 grams")

5. **Given** Korean nutrition terms
   **When** vocabulary normalization is applied
   **Then** Korean meal names normalize correctly (e.g., "점심" → "lunch", "저녁" → "dinner")
   **And** Korean food descriptions are handled gracefully

6. **Given** the Nutrition domain is registered with the framework
   **When** Router selects domains for nutrition-related input
   **Then** Nutrition domain is selected alongside GeneralFitness (base domain)
   **And** vocabulary from both domains is available to Parser

7. **Given** NutritionEntry Pydantic model
   **When** validating the schema
   **Then** `food_items` list is optional (empty list default)
   **And** `calories` is optional (can be estimated or exact)
   **And** `macros` (protein, carbs, fat) are optional
   **And** each macro uses `Field(ge=0.0)` for non-negative validation

8. **Given** a nutrition log with multiple food items
   **When** parsed with Nutrition domain
   **Then** each food item is extracted as a separate item in `food_items` list
   **And** item order from input is preserved
   **And** each item can have its own calorie/macro estimate

## Tasks / Subtasks

- [x] Task 1: Define NutritionEntry Pydantic schema (AC: #1, #3, #7, #8)
  - [x] Create `packages/swealog/swealog/domains/nutrition.py`
  - [x] Define `Macros` model for macro nutrients (protein, carbs, fat - all optional, ge=0.0)
  - [x] Define `FoodItem` model for individual food items (name required, calories, macros optional)
  - [x] Define `NutritionEntry` model as log_schema (meal_type, food_items list, totals, notes, date, time)
  - [x] Use `Field(ge=0.0)` for calorie and macro validation (NOT redundant `@field_validator`)
  - [x] Use optional string for meal_type (NOT Literal) to handle variations like "pre-workout", "post-workout"
  - [x] Use `ConfigDict(strict=True)` for all models
  - [x] Add Google-style docstrings for all classes and fields
  - [x] Follow exact pattern from `strength.py` (see reference file below)

- [x] Task 2: Define Nutrition vocabulary (AC: #4, #5)
  - [x] Include calorie abbreviations (cal → calories, kcal → calories, cals → calories)
  - [x] Include macro abbreviations (p → protein, c → carbs, f → fat, carb → carbs)
  - [x] Include Korean meal names (아침 → breakfast, 점심 → lunch, 저녁 → dinner, 간식 → snack)
  - [x] Include Korean food terms as needed (단백질 → protein, 탄수화물 → carbs, 지방 → fat)
  - [x] Include unit normalizations (g → grams, oz → ounces, ml → milliliters)
  - [x] Include common food abbreviations and casual terms

- [x] Task 3: Create Nutrition DomainModule class (AC: #2)
  - [x] Create `Nutrition(DomainModule)` class in nutrition.py
  - [x] Define comprehensive `description` for Router matching (meals, calories, macros, food tracking)
  - [x] Set `log_schema = NutritionEntry`
  - [x] Define `vocabulary` dict with all normalizations (single canonical location)
  - [x] Define `expertise` with nutrition knowledge (TDEE, macros, meal timing, hydration)
  - [x] Define `response_evaluation_rules` for nutrition-specific advice safety
  - [x] Define `context_management_guidance` for Observer patterns

- [x] Task 4: Create singleton instance (AC: #2, #6)
  - [x] Create `nutrition` singleton instance at module level (follow `strength` pattern)
  - [x] Ensure instance is importable from `swealog.domains`

- [x] Task 5: Export from swealog.domains (AC: #6)
  - [x] Add `Nutrition`, `NutritionEntry`, `FoodItem`, `Macros` to `domains/__init__.py`
  - [x] Add `nutrition` singleton to exports
  - [x] Update `__all__` list
  - [x] **Follow exact import pattern:** `from swealog.domains.nutrition import (...)`

- [x] Task 6: Add comprehensive tests (AC: #1-8)
  - [x] Test Macros model instantiation with valid data
  - [x] Test Macros validation (protein, carbs, fat all ge=0.0)
  - [x] Test Macros boundary values (exactly 0.0 succeeds)
  - [x] Test Macros negative values raise ValidationError
  - [x] Test FoodItem name is required (min_length=1)
  - [x] Test FoodItem missing name raises ValidationError
  - [x] Test FoodItem empty name raises ValidationError
  - [x] Test FoodItem with optional calories and macros
  - [x] Test NutritionEntry instantiation with valid data
  - [x] Test NutritionEntry food_items list populated correctly
  - [x] Test NutritionEntry with empty food_items list (default)
  - [x] Test Nutrition domain instantiation
  - [x] Test vocabulary contains expected mappings (sample check)
  - [x] Test vocabulary contains Korean meal terms
  - [x] Test vocabulary contains calorie/macro abbreviations
  - [x] Test expertise is non-empty
  - [x] Test response_evaluation_rules populated
  - [x] Test context_management_guidance populated
  - [x] Test domain name defaults to "Nutrition"
  - [x] Test integration with GeneralFitness and Strength (all can coexist)

- [x] Task 7: Validation and cleanup (AC: all)
  - [x] Run `make check` (lint + typecheck)
  - [x] Run `make validate` (full validation)
  - [x] Run `make test-ollama` (integration tests with real Ollama)
  - [x] Verify all exports work correctly
  - [x] Verify imports: `from swealog.domains import Nutrition, NutritionEntry, nutrition`

## Dev Notes

### Project Structure

**Location:** `packages/swealog/swealog/domains/`

```
packages/swealog/swealog/domains/
├── __init__.py       # Exports: GeneralFitness, Strength, Nutrition, schemas, instances
├── general_fitness.py # GeneralFitness domain (implemented in Story 1.4)
├── strength.py       # Strength domain (implemented in Story 2.4)
└── nutrition.py      # Nutrition domain (this story)
```

**Test Location:** `packages/swealog/tests/test_nutrition_domain.py`

### Schema Design

**From epics.md FR-A4:**

> FR-A4: Provide Nutrition subdomain (meals, calories, macros) [MVP]

The Nutrition domain captures food and meal tracking with:
- Meal type (breakfast, lunch, dinner, snack)
- Food items list (each with name, optional calories/macros)
- Total calories for meal
- Total macros (protein, carbs, fat)
- Meal notes
- Time/date context

**Schema Hierarchy:**

```python
from pydantic import BaseModel, ConfigDict, Field


class Macros(BaseModel):
    """Macronutrient breakdown for a food item or meal.

    Attributes:
        protein: Protein in grams.
        carbs: Carbohydrates in grams.
        fat: Fat in grams.
    """

    model_config = ConfigDict(strict=True)

    protein: float | None = Field(default=None, ge=0.0)
    carbs: float | None = Field(default=None, ge=0.0)
    fat: float | None = Field(default=None, ge=0.0)


class FoodItem(BaseModel):
    """A single food item within a meal.

    Attributes:
        name: Food item name (required). E.g., "chicken salad", "protein shake".
        quantity: Quantity description. E.g., "1 cup", "200g", "large".
        calories: Estimated or exact calories for this item.
        macros: Macronutrient breakdown for this item.
        notes: Additional notes about this food item.
    """

    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=1)
    quantity: str | None = None
    calories: float | None = Field(default=None, ge=0.0)
    macros: Macros | None = None
    notes: str | None = None


class NutritionEntry(BaseModel):
    """Parsed structure for a nutrition log entry.

    Attributes:
        meal_type: Type of meal (breakfast, lunch, dinner, snack, other).
        food_items: List of food items consumed in this entry.
        total_calories: Total calories for the entire entry.
        total_macros: Combined macros for the entire entry.
        notes: General notes about this meal/entry.
        date: ISO date string if provided in the log.
        time: Time of meal if provided (e.g., "12:30", "noon").
        hunger_level: Pre-meal hunger level (1-10).
        satisfaction_level: Post-meal satisfaction level (1-10).
    """

    model_config = ConfigDict(strict=True)

    meal_type: str | None = None  # Optional - might be "random snack" without type
    food_items: list[FoodItem] = []
    total_calories: float | None = Field(default=None, ge=0.0)
    total_macros: Macros | None = None
    notes: str | None = None
    date: str | None = None
    time: str | None = None
    hunger_level: int | None = Field(default=None, ge=1, le=10)
    satisfaction_level: int | None = Field(default=None, ge=1, le=10)
```

**Validation Notes:**
- All calorie and macro fields use `Field(ge=0.0)` - NO redundant `@field_validator`
- `hunger_level` and `satisfaction_level` use `Field(ge=1, le=10)` for 1-10 range
- `FoodItem.name` uses `Field(min_length=1)` to prevent empty strings
- `meal_type` is optional string (not Literal) to handle variations like "pre-workout", "post-workout"

### Vocabulary Design

**Nutrition-specific vocabulary normalizations:**

```python
vocabulary = {
    # ========================================
    # Calorie abbreviations
    # ========================================
    "cal": "calories",
    "cals": "calories",
    "kcal": "calories",
    "kcals": "calories",
    "calorie": "calories",

    # ========================================
    # Macro abbreviations
    # ========================================
    "p": "protein",
    "pro": "protein",
    "prot": "protein",
    "c": "carbs",
    "carb": "carbs",
    "carbohydrate": "carbs",
    "carbohydrates": "carbs",
    "f": "fat",
    "fats": "fat",
    "lipid": "fat",
    "lipids": "fat",
    "fiber": "fiber",
    "fibre": "fiber",

    # ========================================
    # Meal type variations
    # ========================================
    "bfast": "breakfast",
    "brekkie": "breakfast",
    "brunch": "brunch",
    "snx": "snack",
    "snacks": "snack",

    # ========================================
    # Korean meal names
    # ========================================
    "아침": "breakfast",
    "아침식사": "breakfast",
    "점심": "lunch",
    "점심식사": "lunch",
    "저녁": "dinner",
    "저녁식사": "dinner",
    "간식": "snack",
    "야식": "late-night snack",
    "브런치": "brunch",

    # ========================================
    # Korean nutrition terms
    # ========================================
    "단백질": "protein",
    "탄수화물": "carbs",
    "탄수": "carbs",
    "지방": "fat",
    "칼로리": "calories",
    "열량": "calories",
    "식이섬유": "fiber",

    # ========================================
    # Unit normalizations
    # ========================================
    "g": "grams",
    "gr": "grams",
    "gram": "grams",
    "oz": "ounces",
    "ounce": "ounces",
    "ml": "milliliters",
    "mL": "milliliters",
    "l": "liters",
    "L": "liters",
    "liter": "liters",
    "litre": "liters",
    "cup": "cups",
    "tbsp": "tablespoons",
    "tsp": "teaspoons",
    "tablespoon": "tablespoons",
    "teaspoon": "teaspoons",

    # ========================================
    # Common food terms
    # ========================================
    "shake": "protein shake",
    "smoothie": "smoothie",
    "salad": "salad",
    "water": "water",
    "coffee": "coffee",
    "tea": "tea",
}
```

### Domain Expertise

**Nutrition knowledge for agent prompts:**

```python
expertise = (
    "Nutrition fundamentals: calories in vs calories out, macronutrient balance, "
    "micronutrients, hydration. Macro ratios: typical ranges for protein (10-35%), "
    "carbs (45-65%), fat (20-35%) of total calories. Protein needs: 0.8-2.0g per kg "
    "body weight depending on activity level. Meal timing: breakfast metabolism boost, "
    "pre/post workout nutrition, evening eating considerations. Common tracking: "
    "food diary, calorie counting, macro tracking. Hydration: 8 glasses (2L) baseline, "
    "more for active individuals. Food quality: whole foods vs processed, nutrient density. "
    "Estimation skills: portion sizes, eyeballing servings, restaurant meal estimates."
)
```

### Response Evaluation Rules

**Safety guidelines for nutrition-related responses:**

```python
response_evaluation_rules = [
    "Never recommend extreme calorie restriction (<1200 for women, <1500 for men) without context",
    "Always consider user's stated goals when evaluating intake (cutting, maintenance, bulking)",
    "Flag potential disordered eating patterns with appropriate sensitivity",
    "Avoid specific macro targets without understanding individual needs and activity level",
    "Never shame or moralize about food choices - focus on patterns and data",
    "Consider cultural food preferences and dietary restrictions",
    "Recommend consulting dietitian/nutritionist for medical nutrition therapy",
]
```

### Context Management Guidance

**Observer patterns for nutrition tracking:**

```python
context_management_guidance = (
    "Track: average daily calories (7-day rolling), macro distribution patterns, "
    "meal timing consistency, protein intake relative to goals, hydration frequency. "
    "Flag: significant calorie variance (>500 from average), extended fasting periods, "
    "protein consistently under target, irregular meal patterns. "
    "Correlate: nutrition vs workout performance, meal timing vs energy levels, "
    "weekend vs weekday eating patterns, travel/social impact on nutrition."
)
```

### Relationship to Other Domains

Nutrition is a **subdomain** of GeneralFitness, parallel to Strength:
- GeneralFitness provides base activity tracking
- Strength provides weight training details
- Nutrition provides food/meal tracking
- All three can be selected for the same input (e.g., "post-workout shake 30g protein after bench")
- Vocabularies merge when multiple domains are active

**Domain Selection Example:**
```python
# Input: "post-workout shake 30g protein after heavy bench session"
# Router selects: ["general_fitness", "strength", "nutrition"]
# Parser extracts:
#   - Nutrition domain: {"food_items": [{"name": "protein shake", "macros": {"protein": 30}}]}
#   - Strength domain: {"session_notes": "heavy bench session"}
#   - GeneralFitness domain: {"activity_type": "workout", ...}
```

### Test Strategy

**Test Class Organization:**

```python
class TestMacrosValidation:
    """Tests for Macros model validation."""

    def test_valid_macros(self): ...
    def test_protein_boundary_zero_succeeds(self): ...
    def test_carbs_boundary_zero_succeeds(self): ...
    def test_fat_boundary_zero_succeeds(self): ...
    def test_protein_negative_raises(self): ...
    def test_carbs_negative_raises(self): ...
    def test_fat_negative_raises(self): ...
    def test_all_fields_optional(self): ...


class TestFoodItemModel:
    """Tests for FoodItem model."""

    def test_food_name_required(self): ...
    def test_food_missing_name_raises(self): ...
    def test_food_empty_name_raises(self): ...
    def test_food_valid_with_all_fields(self): ...
    def test_calories_optional(self): ...
    def test_calories_boundary_zero_succeeds(self): ...
    def test_calories_negative_raises(self): ...
    def test_macros_optional(self): ...
    def test_quantity_optional(self): ...
    def test_notes_optional(self): ...


class TestNutritionEntryModel:
    """Tests for NutritionEntry log schema."""

    def test_food_items_list_default_empty(self): ...
    def test_valid_entry_with_food_items(self): ...
    def test_total_calories_boundary_zero_succeeds(self): ...
    def test_total_calories_negative_raises(self): ...
    def test_hunger_level_range(self): ...
    def test_hunger_level_boundary_one_succeeds(self): ...
    def test_hunger_level_boundary_ten_succeeds(self): ...
    def test_satisfaction_level_range(self): ...


class TestNutritionDomainModule:
    """Tests for Nutrition DomainModule configuration."""

    def test_instantiation(self): ...
    def test_name_defaults_to_class_name(self): ...
    def test_description_non_empty(self): ...
    def test_vocabulary_contains_calorie_abbreviations(self): ...
    def test_vocabulary_contains_macro_abbreviations(self): ...
    def test_vocabulary_contains_korean_meal_terms(self): ...
    def test_vocabulary_contains_korean_nutrition_terms(self): ...
    def test_expertise_non_empty(self): ...
    def test_response_evaluation_rules_populated(self): ...
    def test_context_management_guidance_populated(self): ...


class TestNutritionSingleton:
    """Tests for nutrition singleton instance."""

    def test_singleton_importable(self): ...
    def test_singleton_is_nutrition_instance(self): ...


class TestNutritionIntegration:
    """Integration tests with other domains."""

    def test_nutrition_and_general_fitness_coexist(self): ...
    def test_nutrition_and_strength_coexist(self): ...
    def test_all_three_domains_coexist(self): ...
    def test_imports_from_swealog_domains(self): ...
    def test_log_schema_is_nutrition_entry(self): ...
```

### Previous Story Learnings (Story 2.4 - Strength Domain)

**Patterns to Follow (from code review):**
- Use `ConfigDict(strict=True)` for all Pydantic models
- Google-style docstrings for all public classes/methods (required for ruff pydocstyle)
- Export all public classes in `__all__`
- Use `Field(ge=0.0)` or `Field(ge=1, le=10)` for validation - do NOT add redundant `@field_validator`
- Use `Field(min_length=1)` for required string fields to prevent empty strings
- Comprehensive test coverage including boundary value tests
- Follow `strength.py` pattern exactly for domain module structure

**Code Review Common Issues to Avoid (from Story 2.4):**
- Missing `Field(min_length=1)` on required name fields → Fixed in Strength, apply to Nutrition
- Missing docstrings on any public method or field
- Forgetting boundary value tests (exactly 0.0 for calories/macros, exactly 1/10 for scales)
- Not testing validation error messages with `pytest.raises(ValidationError)`
- Using both `Field(ge=..., le=...)` AND `@field_validator` for same constraint (redundant)

**Git Intelligence (from recent commits):**
- Commit `b327b79`: Strength domain implementation shows exact pattern to follow
- Commit `6c22776`: Integration test fixes - ensure new domain doesn't break existing tests
- Pattern: Domain modules use singleton instance at module level

### Architecture Compliance

**From architecture.md and epics.md:**
- Nutrition domain is a Swealog (application) component, NOT Quilto (framework)
- Lives in `packages/swealog/swealog/domains/`
- Uses DomainModule interface from Quilto
- Will be used by Parser agent for structured extraction

**From FR-A4:**
> FR-A4: Provide Nutrition subdomain (meals, calories, macros) [MVP]

### Validation Commands

Run frequently during development:
```bash
# Quick validation
make check

# Full validation (before commits)
make validate

# Integration tests (REQUIRED before marking done)
make test-ollama
```

**Integration Test Requirements:**
- `make test-ollama` must pass before marking story complete
- Integration tests verify Nutrition schema works with real LLM parsing
- No new integration test file needed - existing test infrastructure covers domain modules

### File Skeleton

Copy this as starting point for `packages/swealog/swealog/domains/nutrition.py`:

```python
"""Nutrition domain module for Swealog.

This module provides the Nutrition subdomain for food and meal tracking,
including calories, macronutrients, meal timing, and food items.
"""

from pydantic import BaseModel, ConfigDict, Field
from quilto import DomainModule


class Macros(BaseModel):
    """Macronutrient breakdown for a food item or meal."""

    model_config = ConfigDict(strict=True)

    # TODO: Add fields with ge=0.0 validation


class FoodItem(BaseModel):
    """A single food item within a meal."""

    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=1)
    # TODO: Add remaining fields


class NutritionEntry(BaseModel):
    """Parsed structure for a nutrition log entry."""

    model_config = ConfigDict(strict=True)

    food_items: list[FoodItem] = []
    # TODO: Add remaining fields


class Nutrition(DomainModule):
    """Domain module for nutrition and meal tracking activities."""


# Singleton instance
nutrition = Nutrition(
    description="...",
    log_schema=NutritionEntry,
    vocabulary={
        # TODO: Add vocabulary from design section
    },
    expertise="...",
    response_evaluation_rules=[
        # TODO: Add rules from design section
    ],
    context_management_guidance="...",
)
```

### Export Pattern for __init__.py

Add to `packages/swealog/swealog/domains/__init__.py`:

```python
from swealog.domains.nutrition import (
    FoodItem,
    Macros,
    Nutrition,
    NutritionEntry,
    nutrition,
)

__all__ = [
    # ... existing exports ...
    "FoodItem",
    "Macros",
    "Nutrition",
    "NutritionEntry",
    "nutrition",
]
```

### References

- [Source: epics.md#Story-2.5] Story definition
- [Source: epics.md#FR-A4] Functional requirement
- [Source: architecture.md#Technical-Stack] Pydantic validation requirements
- [Source: project-context.md#Where-Code-Belongs] Swealog vs Quilto separation
- [Source: strength.py] Existing domain module pattern - **follow this exactly**
- [Source: 2-4-create-strength-domain-module.md] Previous story patterns and code review learnings

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created `packages/swealog/swealog/domains/nutrition.py` with:
  - `Macros` model: protein, carbs, fat fields (all optional, ge=0.0)
  - `FoodItem` model: name (required, min_length=1), quantity, calories, macros, notes
  - `NutritionEntry` model: meal_type, food_items list, total_calories, total_macros, notes, date, time, hunger_level, satisfaction_level
  - `Nutrition` DomainModule class
  - `nutrition` singleton instance with comprehensive vocabulary (61 terms), expertise, response_evaluation_rules, and context_management_guidance
- Updated `packages/swealog/swealog/domains/__init__.py` to export all new classes
- Created comprehensive test suite in `packages/swealog/tests/test_nutrition_domain.py` with 48+ tests covering:
  - Macros validation (boundary values, negative values)
  - FoodItem validation (required name, optional fields)
  - NutritionEntry validation (hunger/satisfaction 1-10 range)
  - Domain module configuration
  - Integration with GeneralFitness and Strength domains
- All validation commands passed:
  - `make check`: lint + typecheck passed
  - `make validate`: 505 passed, 7 skipped
  - `make test-ollama`: 508 passed, 4 skipped

### File List

- `packages/swealog/swealog/domains/nutrition.py` (created)
- `packages/swealog/swealog/domains/__init__.py` (modified)
- `packages/swealog/tests/test_nutrition_domain.py` (created)
- `tests/test_conftest_fixtures.py` (modified - minor typing updates during development)
