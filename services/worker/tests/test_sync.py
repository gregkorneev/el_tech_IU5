from worker.sync import file_status, fingerprint, normalized_path
from worker.models import ProcessingStatus
from worker.extract import ExtractedPart, chunks
from worker.providers import LocalSummaryProvider


def test_path_is_normalized():
    assert normalized_path(r"lectures\\week 1//intro.pdf") == "/lectures/week 1/intro.pdf"


def test_fingerprint_detects_change():
    old = {"path": "/a.pdf", "size": 10, "modified": "2026-09-01T00:00:00Z"}
    assert fingerprint(old) != fingerprint(old | {"size": 11})


def test_unsupported_does_not_fail():
    assert file_status("archive.zip") == ProcessingStatus.UNSUPPORTED


def test_chunking_preserves_page():
    parts = chunks([ExtractedPart("one two three four", page=4)], max_chars=7)
    assert all(part.page == 4 for part in parts)
    assert " ".join(part.text for part in parts) == "one two three four"


def test_local_summary_returns_valid_structure():
    result = LocalSummaryProvider().summarize("Лекция", ["Первый закон Кирхгофа описывает токи в узле. Второй закон описывает контуры."])
    assert result.title == "Лекция"
    assert result.short_summary
