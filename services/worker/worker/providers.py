"""Provider boundary: external LLMs can replace LocalSummaryProvider without changing processing."""
from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel, Field


class SummaryResult(BaseModel):
    title: str
    short_summary: str
    detail: str
    topics: list[str] = Field(default_factory=list)
    definitions: list[str] = Field(default_factory=list)
    formulas: list[str] = Field(default_factory=list)


class LLMProvider(Protocol):
    def summarize(self, title: str, chunks: list[str]) -> SummaryResult: ...


class LocalSummaryProvider:
    """Deterministic offline summary so a missing API key never blocks ingestion."""
    def summarize(self, title: str, chunks: list[str]) -> SummaryResult:
        text = " ".join(chunks).strip()
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if len(sentence.strip()) > 20]
        if not sentences:
            sentences = [text]
        sentences = [sentence[:240].rsplit(" ", 1)[0] or sentence[:240] for sentence in sentences]
        summary = " ".join(sentences[:3]) or "Текст извлечён; автоматическое краткое описание пока недоступно."
        headings = re.findall(r"(?:^|\n)\s*(?:\d+[.)]|#{1,3})\s*([^\n]{3,90})", text)
        topics = list(dict.fromkeys(item.strip(" .") for item in headings))[:12]
        formulas = re.findall(r"[^\n]{0,50}(?:=|≈|∑|Ω)[^\n]{0,50}", text)[:12]
        return SummaryResult(title=title, short_summary=summary, detail="\n\n".join(sentences[:20]) or summary, topics=topics, formulas=formulas)
