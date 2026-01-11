"""Domain modules for Swealog fitness application."""

from swealog.domains.general_fitness import (
    ExerciseRecord,
    GeneralFitness,
    GeneralFitnessEntry,
    general_fitness,
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
    "GeneralFitness",
    "GeneralFitnessEntry",
    "general_fitness",
    "Strength",
    "StrengthEntry",
    "StrengthExercise",
    "StrengthSet",
    "strength",
]
