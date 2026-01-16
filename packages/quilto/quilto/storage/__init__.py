"""Storage module for Quilto - handles entry persistence and retrieval.

This module provides:
- Entry and DateRange models for log data
- StorageRepository for raw/parsed file operations
- GlobalContextManager for context persistence and size management
"""

from quilto.storage.context import (
    ContextEntry,
    GlobalContext,
    GlobalContextFrontmatter,
    GlobalContextManager,
)
from quilto.storage.models import DateRange, Entry
from quilto.storage.repository import StorageRepository

__all__ = [
    "ContextEntry",
    "DateRange",
    "Entry",
    "GlobalContext",
    "GlobalContextFrontmatter",
    "GlobalContextManager",
    "StorageRepository",
]
