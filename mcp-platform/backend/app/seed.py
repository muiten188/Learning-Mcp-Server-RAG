"""Import the Phase 1 text files into pgvector after migrations are applied."""

import asyncio
from pathlib import Path

from app.core.db import SessionLocal, engine
from app.features.documents.ingestion import ingest
from app.features.documents.models import Document
from app.features.documents.repository import DocumentRepository


async def main() -> None:
    """Import new seed text files and index their contents."""
    data_dir = Path(__file__).resolve().parents[2] / "data"
    for path in sorted(data_dir.glob("*.txt")):
        async with SessionLocal() as db:
            repository = DocumentRepository(db)
            existing = await repository.get_by_filename(path.name)
            if existing is not None:
                print(f"Skipping {path.name}: already present")
                continue
            document = Document(filename=path.name, storage_path=str(path))
            repository.add(document)
            await db.commit()
            print(f"Indexing {path.name}")
            await ingest(document.id)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
