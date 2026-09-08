from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select

from .db import Base, engine, session_scope
from .models import Course, SourceFile
from .sync import sync


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Электротехника knowledge API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["GET", "POST"], allow_headers=["*"])


def serialize(item: SourceFile):
    return {"id": item.id, "name": item.name, "path": item.path, "type": (item.name.rsplit(".", 1)[-1] if "." in item.name else "file").upper(), "status": item.status, "modifiedAt": item.modified_at, "originalUrl": item.original_url, "excerpt": (item.extracted_text or "").replace("\n", " ")[:180]}


@app.get("/health")
def health(): return {"ok": True}


@app.get("/materials")
def materials(q: str = "", status: str | None = None):
    with session_scope() as db:
        stmt = select(SourceFile).order_by(SourceFile.modified_at.desc())
        if q: stmt = stmt.where(or_(SourceFile.name.ilike(f"%{q}%"), SourceFile.extracted_text.ilike(f"%{q}%")))
        if status: stmt = stmt.where(SourceFile.status == status)
        return [serialize(row) for row in db.scalars(stmt)]


@app.get("/materials/{file_id}")
def material(file_id: int):
    with session_scope() as db:
        item = db.get(SourceFile, file_id)
        if not item: raise HTTPException(404, "Материал не найден")
        return serialize(item) | {"text": item.extracted_text}


@app.post("/admin/sync")
def run_sync(full: bool = False):
    return sync(full)
