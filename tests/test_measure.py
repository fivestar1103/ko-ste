from calibration.scripts.measure import docs_for_source, pct


def test_empty_percentile_is_unmeasured_instead_of_nan():
    assert pct([], 0.5) is None


def test_document_order_is_case_insensitive_across_platforms(tmp_path):
    root = tmp_path / "sample"
    (root / "alpha").mkdir(parents=True)
    for name in ("Zebra.md", "apple.md", "alpha/Notes.md"):
        (root / name).write_text(name, encoding="utf-8")

    documents = docs_for_source({"id": "sample", "paths": ["**/*.md"]}, tmp_path)

    assert [name for name, _ in documents] == [
        "alpha/Notes.md", "apple.md", "Zebra.md",
    ]
