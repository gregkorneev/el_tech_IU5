from worker.sync import file_status, fingerprint, normalized_path
from worker.models import ProcessingStatus


def test_path_is_normalized():
    assert normalized_path(r"lectures\\week 1//intro.pdf") == "/lectures/week 1/intro.pdf"


def test_fingerprint_detects_change():
    old = {"path": "/a.pdf", "size": 10, "modified": "2026-09-01T00:00:00Z"}
    assert fingerprint(old) != fingerprint(old | {"size": 11})


def test_unsupported_does_not_fail():
    assert file_status("archive.zip") == ProcessingStatus.UNSUPPORTED
