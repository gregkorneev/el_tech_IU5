"""Video/audio ingestion with a replaceable timestamp-aware STT provider."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import requests
from sqlalchemy import delete, select

from .analyze import analyze
from .db import Base, engine, session_scope
from .models import DocumentChunk, ProcessingStatus, SourceFile, TranscriptSegment

AUDIO_EXTENSIONS = {"mp4", "mov", "m4a", "mp3", "wav"}


@dataclass(frozen=True)
class TranscriptPart:
    start: float
    end: float
    text: str


class TranscriptionProvider(Protocol):
    def transcribe(self, audio_path: Path) -> list[TranscriptPart]: ...


class UnconfiguredTranscriptionProvider:
    def transcribe(self, audio_path: Path) -> list[TranscriptPart]:
        raise RuntimeError("No STT provider configured. Set one before transcribing recordings.")


def extract_audio(source_path: Path, target_path: Path) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed")
    subprocess.run(["ffmpeg", "-y", "-i", str(source_path), "-vn", "-ac", "1", "-ar", "16000", str(target_path)], check=True, capture_output=True)


def transcribe_one(source: SourceFile, db, provider: TranscriptionProvider | None = None) -> None:
    if not source.download_url:
        raise ValueError("Yandex Disk did not provide a download URL")
    provider = provider or UnconfiguredTranscriptionProvider()
    with tempfile.TemporaryDirectory(prefix="elteh-") as temporary:
        input_path = Path(temporary) / source.name
        input_path.write_bytes(requests.get(source.download_url, timeout=300).content)
        audio_path = Path(temporary) / "audio.wav"
        source.status = ProcessingStatus.EXTRACTING; db.flush()
        extension = source.name.rsplit(".", 1)[-1].lower()
        if extension in {"mp4", "mov"}: extract_audio(input_path, audio_path)
        else: audio_path = input_path
        source.status = ProcessingStatus.TRANSCRIBING; db.flush()
        segments = provider.transcribe(audio_path)
    db.execute(delete(TranscriptSegment).where(TranscriptSegment.source_file_id == source.id))
    db.execute(delete(DocumentChunk).where(DocumentChunk.source_file_id == source.id))
    db.add_all(TranscriptSegment(source_file_id=source.id, ordinal=index, start_seconds=part.start, end_seconds=part.end, text=part.text) for index, part in enumerate(segments))
    db.add_all(DocumentChunk(source_file_id=source.id, ordinal=index, text=part.text) for index, part in enumerate(segments))
    source.extracted_text = "\n".join(part.text for part in segments)
    source.status = ProcessingStatus.PROCESSING; db.flush()
    analyze(source, db)
    source.status = ProcessingStatus.READY


def transcribe_queue(limit: int = 3) -> dict[str, int]:
    Base.metadata.create_all(engine); results = {"ready": 0, "failed": 0}
    with session_scope() as db:
        sources = list(db.scalars(select(SourceFile).where(SourceFile.status == ProcessingStatus.QUEUED).limit(limit)))
        for source in sources:
            extension = source.name.rsplit(".", 1)[-1].lower()
            if extension not in AUDIO_EXTENSIONS: continue
            try:
                transcribe_one(source, db); results["ready"] += 1
            except Exception:
                source.status = ProcessingStatus.FAILED; results["failed"] += 1
        db.commit()
    return results


if __name__ == "__main__":
    print(transcribe_queue())
