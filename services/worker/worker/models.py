from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class ProcessingStatus(StrEnum):
    DISCOVERED = "discovered"
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    TRANSCRIBING = "transcribing"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    REMOVED = "removed"


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), unique=True)
    public_key: Mapped[str] = mapped_column(String(1024))


class SourceFile(Base):
    __tablename__ = "source_files"
    __table_args__ = (UniqueConstraint("course_id", "path", name="uq_source_course_path"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    path: Mapped[str] = mapped_column(String(2048))
    name: Mapped[str] = mapped_column(String(512))
    media_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    original_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    download_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default=ProcessingStatus.DISCOVERED)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slide: Mapped[int | None] = mapped_column(Integer, nullable=True)


class MaterialSummary(Base):
    __tablename__ = "material_summaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(512))
    short_summary: Mapped[str] = mapped_column(Text)
    detail: Mapped[str] = mapped_column(Text)
    topics_json: Mapped[str] = mapped_column(Text, default="[]")
    definitions_json: Mapped[str] = mapped_column(Text, default="[]")
    formulas_json: Mapped[str] = mapped_column(Text, default="[]")


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_file_id: Mapped[int] = mapped_column(ForeignKey("source_files.id"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    start_seconds: Mapped[float] = mapped_column()
    end_seconds: Mapped[float] = mapped_column()
    text: Mapped[str] = mapped_column(Text)
