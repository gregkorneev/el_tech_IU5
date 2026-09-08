"""Yandex public-folder sync: `python -m worker.sync [--full]`."""
import argparse
import hashlib
import logging
from datetime import datetime

import requests
from sqlalchemy import select

from .config import settings
from .db import Base, engine, session_scope
from .models import Course, ProcessingStatus, SourceFile

log = logging.getLogger("elteh.sync")
SUPPORTED = {"pdf", "docx", "pptx", "xlsx", "txt", "md", "mp4", "mov", "m4a", "mp3", "wav"}


def normalized_path(path: str) -> str:
    return "/" + "/".join(part for part in path.replace("\\", "/").split("/") if part)


def fingerprint(item: dict) -> str:
    value = f"{normalized_path(item['path'])}|{item.get('size', 0)}|{item.get('modified', '')}"
    return hashlib.sha256(value.encode()).hexdigest()


def walk_public_tree(public_key: str, path: str = ""):
    response = requests.get("https://cloud-api.yandex.net/v1/disk/public/resources", params={"public_key": public_key, "path": path, "limit": 1000}, timeout=30)
    response.raise_for_status()
    payload = response.json()
    for item in payload.get("_embedded", {}).get("items", []):
        if item.get("type") == "dir":
            yield from walk_public_tree(public_key, item["path"])
        else:
            yield item


def file_status(name: str) -> ProcessingStatus:
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ProcessingStatus.QUEUED if extension in SUPPORTED else ProcessingStatus.UNSUPPORTED


def sync(full: bool = False, items=None) -> dict[str, int]:
    Base.metadata.create_all(engine)
    discovered = list(items) if items is not None else list(walk_public_tree(settings.yandex_public_key))
    counts = {"new": 0, "modified": 0, "unchanged": 0, "removed": 0}
    with session_scope() as db:
        course = db.scalar(select(Course).where(Course.title == "Электротехника 2026/27"))
        if not course:
            course = Course(title="Электротехника 2026/27", public_key=settings.yandex_public_key)
            db.add(course); db.flush()
        seen = set()
        for item in discovered:
            path = normalized_path(item["path"]); seen.add(path); digest = fingerprint(item)
            source = db.scalar(select(SourceFile).where(SourceFile.course_id == course.id, SourceFile.path == path))
            if not source:
                db.add(SourceFile(course_id=course.id, path=path, name=item["name"], media_type=item.get("mime_type"), size=item.get("size", 0), modified_at=_date(item.get("modified")), original_url=item.get("public_url") or settings.yandex_public_key, download_url=item.get("file"), fingerprint=digest, status=file_status(item["name"])))
                counts["new"] += 1
            elif full or source.fingerprint != digest:
                source.name, source.media_type, source.size, source.modified_at, source.original_url, source.download_url, source.fingerprint = item["name"], item.get("mime_type"), item.get("size", 0), _date(item.get("modified")), item.get("public_url") or settings.yandex_public_key, item.get("file"), digest
                source.status = file_status(source.name); counts["modified"] += 1
            else:
                counts["unchanged"] += 1
        for source in db.scalars(select(SourceFile).where(SourceFile.course_id == course.id)):
            if source.path not in seen and source.status != ProcessingStatus.REMOVED:
                source.status = ProcessingStatus.REMOVED; counts["removed"] += 1
        db.commit()
    log.info("sync completed: %s", counts)
    return counts


def _date(value: str | None):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(message)s")
    parser = argparse.ArgumentParser(); parser.add_argument("--full", action="store_true")
    print(sync(parser.parse_args().full))
