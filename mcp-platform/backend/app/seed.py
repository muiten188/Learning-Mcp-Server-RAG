"""Import the Phase 1 text files into pgvector after migrations are applied."""

import asyncio
from pathlib import Path

from sqlalchemy import select

from app.core.db import SessionLocal, engine
from app.models import Document
from app.workers.tasks import ingest


async def main():
    data_dir = Path(__file__).resolve().parents[2] / "data"
    for path in sorted(data_dir.glob("*.txt")):
        async with SessionLocal() as db:
            existing = await db.scalar(
                select(Document.id).where(Document.filename == path.name).limit(1)
            )
            if existing is not None:
                print(f"Skipping {path.name}: already present")
                continue
            document = Document(filename=path.name, storage_path=str(path))
            db.add(document)
            await db.commit()
            print(f"Indexing {path.name}")
            await ingest(document.id)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
