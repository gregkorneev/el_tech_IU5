import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select

from .db import Base, engine, session_scope
from .models import Course, MaterialSummary, SourceFile, TranscriptSegment
from .sync import sync


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Электротехника knowledge API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["GET", "POST"], allow_headers=["*"])


def category(item: SourceFile) -> str:
    text = f"{item.path} {item.name}".lower()
    if any(word in text for word in ("лекц", "lecture")): return "lectures"
    if any(word in text for word in ("лаб", "laboratory", "lab")): return "labs"
    if any(word in text for word in ("запис", "recording", "record")): return "recordings"
    return "materials"


def serialize(item: SourceFile):
    return {"id": item.id, "name": item.name, "path": item.path, "type": (item.name.rsplit(".", 1)[-1] if "." in item.name else "file").upper(), "status": item.status, "category": category(item), "modifiedAt": item.modified_at, "originalUrl": item.original_url, "excerpt": (item.extracted_text or "").replace("\n", " ")[:180]}


@app.get("/health")
def health(): return {"ok": True}


@app.get("/materials")
def materials(q: str = "", status: str | None = None, category: str | None = None):
    with session_scope() as db:
        stmt = select(SourceFile).order_by(SourceFile.modified_at.desc())
        if q: stmt = stmt.where(or_(SourceFile.name.ilike(f"%{q}%"), SourceFile.extracted_text.ilike(f"%{q}%")))
        if status: stmt = stmt.where(SourceFile.status == status)
        rows = (serialize(row) for row in db.scalars(stmt))
        return [row for row in rows if category is None or row["category"] == category]


@app.get("/materials/{file_id}")
def material(file_id: int):
    with session_scope() as db:
        item = db.get(SourceFile, file_id)
        if not item: raise HTTPException(404, "Материал не найден")
        summary = db.scalar(select(MaterialSummary).where(MaterialSummary.source_file_id == item.id))
        segments = list(db.scalars(select(TranscriptSegment).where(TranscriptSegment.source_file_id == item.id).order_by(TranscriptSegment.ordinal)))
        return serialize(item) | {"text": item.extracted_text, "summary": None if not summary else {"short": summary.short_summary, "detail": summary.detail, "topics": json.loads(summary.topics_json), "formulas": json.loads(summary.formulas_json)}, "transcript": [{"start": segment.start_seconds, "end": segment.end_seconds, "text": segment.text} for segment in segments]}


@app.post("/admin/sync")
def run_sync(full: bool = False):
    return sync(full)
