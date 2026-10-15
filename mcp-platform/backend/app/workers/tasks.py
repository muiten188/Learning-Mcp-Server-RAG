"""Compatibility imports for document ingestion tasks."""

from app.features.documents.ingestion import ingest
from app.features.documents.tasks import ingest_document

__all__ = ["ingest", "ingest_document"]
