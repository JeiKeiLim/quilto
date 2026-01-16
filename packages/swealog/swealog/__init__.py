"""Swealog - Fitness logging application powered by Quilto framework."""

from swealog.domains import (
    ExerciseRecord,
    GeneralFitness,
    GeneralFitnessEntry,
    general_fitness,
)
from swealog.observer import FitnessSignificantEntryDetector

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ExerciseRecord",
    "FitnessSignificantEntryDetector",
    "GeneralFitness",
    "GeneralFitnessEntry",
    "general_fitness",
]
