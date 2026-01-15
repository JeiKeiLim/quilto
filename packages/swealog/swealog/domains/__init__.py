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
from swealog.domains.running import (
    Running,
    RunningEntry,
    RunningInterval,
    RunningSplit,
    running,
)
from swealog.domains.strength import (
    Strength,
    StrengthEntry,
    StrengthExercise,
    StrengthSet,
    strength,
)
from swealog.domains.swimming import (
    Swimming,
    SwimmingEntry,
    SwimmingInterval,
    SwimmingLap,
    swimming,
)

__all__ = [
    "ExerciseRecord",
    "FoodItem",
    "GeneralFitness",
    "GeneralFitnessEntry",
    "Macros",
    "Nutrition",
    "NutritionEntry",
    "Running",
    "RunningEntry",
    "RunningInterval",
    "RunningSplit",
    "Strength",
    "StrengthEntry",
    "StrengthExercise",
    "StrengthSet",
    "Swimming",
    "SwimmingEntry",
    "SwimmingInterval",
    "SwimmingLap",
    "general_fitness",
    "nutrition",
    "running",
    "strength",
    "swimming",
]
