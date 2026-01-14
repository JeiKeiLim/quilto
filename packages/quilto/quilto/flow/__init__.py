"""Flow module for Quilto framework.

This module provides orchestration functions for complex multi-agent flows,
including correction processing that coordinates Parser and Storage operations.
"""

from quilto.flow.correction import process_correction
from quilto.flow.models import CorrectionResult

__all__ = [
    "CorrectionResult",
    "process_correction",
]
