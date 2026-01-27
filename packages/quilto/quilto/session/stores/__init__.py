"""Session storage backends for Quilto.

This module exports the SessionStore protocol and implementations:
- SessionStore: Protocol defining storage interface
- SQLiteSessionStore: SQLite-backed implementation (default)
"""

from quilto.session.stores.base import SessionStore
from quilto.session.stores.sqlite import SQLiteSessionStore

__all__ = [
    "SessionStore",
    "SQLiteSessionStore",
]
