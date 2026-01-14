"""Nutrition domain module for Swealog.

This module provides the Nutrition subdomain for food and meal tracking,
including calories, macronutrients, meal timing, and food items.
"""

from pydantic import BaseModel, ConfigDict, Field
from quilto import DomainModule


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

    meal_type: str | None = None
    food_items: list[FoodItem] = []
    total_calories: float | None = Field(default=None, ge=0.0)
    total_macros: Macros | None = None
    notes: str | None = None
    date: str | None = None
    time: str | None = None
    hunger_level: int | None = Field(default=None, ge=1, le=10)
    satisfaction_level: int | None = Field(default=None, ge=1, le=10)


class Nutrition(DomainModule):
    """Domain module for nutrition and meal tracking activities.

    This domain covers food and meal tracking including calorie counting,
    macronutrient tracking, meal timing, and hydration. It provides
    specialized parsing for nutrition logs.
    """


# Singleton instance
nutrition = Nutrition(
    description=(
        "Nutrition and meal tracking activities including food diary, calorie counting, "
        "and macronutrient tracking. Tracks meals (breakfast, lunch, dinner, snacks), "
        "food items, calories, and macros (protein, carbs, fat). Handles common "
        "abbreviations like 'cal', 'kcal', 'g protein'. Covers meal timing, portion "
        "sizes, and hydration tracking."
    ),
    log_schema=NutritionEntry,
    vocabulary={
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
    },
    expertise=(
        "Nutrition fundamentals: calories in vs calories out, macronutrient balance, "
        "micronutrients, hydration. Macro ratios: typical ranges for protein (10-35%), "
        "carbs (45-65%), fat (20-35%) of total calories. Protein needs: 0.8-2.0g per kg "
        "body weight depending on activity level. Meal timing: breakfast metabolism boost, "
        "pre/post workout nutrition, evening eating considerations. Common tracking: "
        "food diary, calorie counting, macro tracking. Hydration: 8 glasses (2L) baseline, "
        "more for active individuals. Food quality: whole foods vs processed, nutrient density. "
        "Estimation skills: portion sizes, eyeballing servings, restaurant meal estimates."
    ),
    response_evaluation_rules=[
        "Never recommend extreme calorie restriction (<1200 for women, <1500 for men) without context",
        "Always consider user's stated goals when evaluating intake (cutting, maintenance, bulking)",
        "Flag potential disordered eating patterns with appropriate sensitivity",
        "Avoid specific macro targets without understanding individual needs and activity level",
        "Never shame or moralize about food choices - focus on patterns and data",
        "Consider cultural food preferences and dietary restrictions",
        "Recommend consulting dietitian/nutritionist for medical nutrition therapy",
    ],
    context_management_guidance=(
        "Track: average daily calories (7-day rolling), macro distribution patterns, "
        "meal timing consistency, protein intake relative to goals, hydration frequency. "
        "Flag: significant calorie variance (>500 from average), extended fasting periods, "
        "protein consistently under target, irregular meal patterns. "
        "Correlate: nutrition vs workout performance, meal timing vs energy levels, "
        "weekend vs weekday eating patterns, travel/social impact on nutrition."
    ),
    clarification_patterns={
        "SUBJECTIVE": [
            "How hungry are you feeling right now?",
            "Are you experiencing any food cravings?",
            "How did your last meal make you feel - satisfied or still hungry?",
            "Any digestive issues or food sensitivities to consider?",
        ],
        "CLARIFICATION": [
            "Which meal are you asking about (breakfast, lunch, dinner, snack)?",
            "Are you tracking specific macros (protein, carbs, fat) or total calories?",
            "What's your current nutritional goal (muscle gain, fat loss, maintenance)?",
            "Should I focus on timing (pre/post workout) or just daily totals?",
        ],
    },
)
