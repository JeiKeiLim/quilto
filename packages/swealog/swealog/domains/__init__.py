"""Domain modules for Swealog fitness application."""

from swealog.domains.general_fitness import (
    ExerciseRecord,
    GeneralFitness,
    GeneralFitnessEntry,
    general_fitness,
)
from swealog.domains.nutrition import (
    FoodItem,
    Macros,
    Nutrition,
    NutritionEntry,
    nutrition,
)
from swealog.domains.strength import (
    Strength,
    StrengthEntry,
    StrengthExercise,
    StrengthSet,
    strength,
)

__all__ = [
    "ExerciseRecord",
    "FoodItem",
    "GeneralFitness",
    "GeneralFitnessEntry",
    "Macros",
    "Nutrition",
    "NutritionEntry",
    "Strength",
    "StrengthEntry",
    "StrengthExercise",
    "StrengthSet",
    "general_fitness",
    "nutrition",
    "strength",
]
