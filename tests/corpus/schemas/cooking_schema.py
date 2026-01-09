"""Test schema for expected cooking parser outputs.

This schema is for multi-domain testing infrastructure, NOT application code.
"""

from pydantic import BaseModel, ConfigDict


class CookingEntry(BaseModel):
    """Expected parser output for cooking/recipe entries.

    Attributes:
        dish_name: Name of the dish prepared.
        ingredients: List of ingredients with quantities (as strings).
        cooking_time_minutes: Total cooking time in minutes if specified.
        notes: Quality notes, tips, or observations about the cooking.
    """

    model_config = ConfigDict(strict=True)

    dish_name: str
    ingredients: list[str] = []
    cooking_time_minutes: int | None = None
    notes: str | None = None
