"""Queue consumer for textual documents: `python -m worker.process`."""
import logging

import requests
from sqlalchemy import delete, select

from .db import Base, engine, session_scope
from .extract import chunks, extract
from .models import DocumentChunk, ProcessingStatus, SourceFile

log = logging.getLogger("elteh.process")


def process_one(source: SourceFile, db) -> None:
    if not source.download_url:
        raise ValueError("Yandex Disk did not provide a download URL")
    content = requests.get(source.download_url, timeout=120).content
    parts = chunks(extract(source.name, content))
    db.execute(delete(DocumentChunk).where(DocumentChunk.source_file_id == source.id))
    db.add_all(DocumentChunk(source_file_id=source.id, ordinal=index, text=part.text, page=part.page, slide=part.slide) for index, part in enumerate(parts))
    source.extracted_text = "\n\n".join(part.text for part in parts)
    source.status = ProcessingStatus.READY


def process_queue(limit: int = 10) -> dict[str, int]:
    Base.metadata.create_all(engine); results = {"ready": 0, "failed": 0, "skipped": 0}
    with session_scope() as db:
        sources = list(db.scalars(select(SourceFile).where(SourceFile.status == ProcessingStatus.QUEUED).limit(limit)))
        for source in sources:
            extension = source.name.rsplit(".", 1)[-1].lower()
            if extension in {"mp4", "mov", "m4a", "mp3", "wav"}:
                results["skipped"] += 1; continue
            try:
                process_one(source, db); results["ready"] += 1
            except Exception:
                log.exception("failed to process %s", source.path); source.status = ProcessingStatus.FAILED; results["failed"] += 1
        db.commit()
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
    print(process_queue())
