import json

from sqlalchemy import select

from .models import DocumentChunk, MaterialSummary, SourceFile
from .providers import LLMProvider, LocalSummaryProvider


def analyze(source: SourceFile, db, provider: LLMProvider | None = None) -> MaterialSummary:
    provider = provider or LocalSummaryProvider()
    chunks = list(db.scalars(select(DocumentChunk).where(DocumentChunk.source_file_id == source.id).order_by(DocumentChunk.ordinal)))
    result = provider.summarize(source.name, [chunk.text for chunk in chunks])
    summary = db.scalar(select(MaterialSummary).where(MaterialSummary.source_file_id == source.id))
    if not summary:
        summary = MaterialSummary(source_file_id=source.id, title=result.title, short_summary=result.short_summary, detail=result.detail)
        db.add(summary)
    summary.title, summary.short_summary, summary.detail = result.title, result.short_summary, result.detail
    summary.topics_json = json.dumps(result.topics, ensure_ascii=False)
    summary.definitions_json = json.dumps(result.definitions, ensure_ascii=False)
    summary.formulas_json = json.dumps(result.formulas, ensure_ascii=False)
    return summary
