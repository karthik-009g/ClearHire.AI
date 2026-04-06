"""Cross-dialect embedding vector type.

Uses pgvector on PostgreSQL and JSON fallback on non-PostgreSQL dialects
to keep local/tests compatible.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - import guard for environments without pgvector
    Vector = None


class EmbeddingVector(TypeDecorator):
    """Vector column that gracefully degrades to JSON off PostgreSQL."""

    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int):
        self.dimensions = dimensions
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect):
        if value is None:
            return None
        return [float(component) for component in value]

    def process_result_value(self, value: Any, dialect):
        if value is None:
            return None
        return [float(component) for component in value]