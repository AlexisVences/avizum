import json
from datetime import date
from pathlib import Path

import pytest

from app.services.source_watch import (INDEX_HOST, Finding, IndexEntry, IndexStructureError, Watched, accept, compare,
                                       fetch_index, parse_index, parse_reform_date, render_report, snapshot)
from app.services.sources import SourceSpec

SAMPLE = (Path(__file__).parent / "fixtures" / "source_watch" / "index_sample.html").read_text(encoding="utf-8")
BASE = f"https://{INDEX_HOST}"


def spec(slug, url, reform=None):
    return SourceSpec(slug=slug, title=slug, kind="reglamento", url=url, last_reform_date=reform)


@pytest.fixture()
def entries():
    return parse_index(SAMPLE, "reglamentos")


def by_title(entries, start):
    return next(e for e in entries if e.title.startswith(start))


def test_parses_titles_pdf_paths_and_reform_dates_from_the_real_index(entries):
    transito = by_title(entries, "Reglamento de Tránsito")
    assert transito.pdf_path.endswith("REGLAMENTO_DE_TRNSITO_DE_LA_CIUDAD_DE_MXICO_6.4.pdf")
    assert transito.reform_date == "2026-06-30"
    assert by_title(entries, "Ley de Movilidad").reform_date == "2025-08-27"  # «publicada en la G.O. CDMX el …»
    assert by_title(entries, "Ley de Procedimiento").reform_date == "2019-06-12"  # «ÙLTIMA REFORMA» in capitals
    assert by_title(entries, "Reglamento de la Ley de Cultura").reform_date is None  # the index states none
    assert len(entries) == 11


@pytest.mark.parametrize("text,expected", [
    ("Última reforma 30 de junio de 2026 Dar click", "2026-06-30"),
    ("ÚLTIMA REFORMA 23 DE DICIEMBRE DEL 2019", "2019-12-23"),
    ("PUBLICADO EL 17 DE AGOSTO DE 2015", None),  # a publication date is not a reform
    ("Última reforma 31 de febrero de 2026", None),
])
def test_reform_dates(text, expected):
    assert parse_reform_date(text) == expected


def baseline(entries):
    transito = by_title(entries, "Reglamento de Tránsito")
    url = BASE + transito.pdf_path
    specs = [spec("reglamento-transito", url, date(2026, 6, 30)), spec("acuerdo", "https://www.ssc.cdmx.gob.mx/a.pdf")]
    state, problems = snapshot(specs, entries, {"acuerdo": "aaa"})
    return specs, state, problems


def test_snapshot_records_the_index_and_flags_a_manifest_that_disagrees(entries):
    specs, state, problems = baseline(entries)
    assert problems == []
    assert state["reglamento-transito"].mode == "index" and state["reglamento-transito"].reform_date == "2026-06-30"
    assert state["acuerdo"].sha256 == "aaa"
    stale_manifest = [spec("reglamento-transito", specs[0].url, date(2025, 1, 1))]
    assert "manifiesto" in snapshot(stale_manifest, entries, {})[1][0]


def test_no_findings_when_nothing_changed(entries):
    specs, state, _ = baseline(entries)
    assert compare(state, specs, entries, {"acuerdo": "aaa"}) == []


def test_a_new_pdf_version_is_found_even_though_the_path_changed(entries):
    specs, state, _ = baseline(entries)
    moved = [IndexEntry(e.section, e.title, e.pdf_path.replace("_6.4.pdf", "_6.5.pdf") if e.pdf_path.endswith("_6.4.pdf") else e.pdf_path,
                        "2026-09-01" if e.title.startswith("Reglamento de Tránsito") else e.reform_date, e.description) for e in entries]
    [finding] = compare(state, specs, moved, {"acuerdo": "aaa"})
    assert finding.kind == "nueva_version" and finding.new_url.endswith("_6.5.pdf") and "2026-09-01" in finding.detail


def test_a_changed_reform_date_with_the_same_pdf_is_a_finding(entries):
    specs, state, _ = baseline(entries)
    changed = [IndexEntry(e.section, e.title, e.pdf_path, "2026-12-01" if e.title.startswith("Reglamento de Tránsito") else e.reform_date, e.description) for e in entries]
    assert [f.kind for f in compare(state, specs, changed, {"acuerdo": "aaa"})] == ["reforma_nueva"]


def test_a_document_that_disappears_from_the_index_is_reported_not_ignored(entries):
    specs, state, _ = baseline(entries)
    gone = [e for e in entries if not e.title.startswith("Reglamento de Tránsito")]
    [finding] = compare(state, specs, gone, {"acuerdo": "aaa"})
    assert finding.kind == "no_encontrado"


def test_hash_sources_report_changes_and_download_errors(entries):
    specs, state, _ = baseline(entries)
    assert [f.kind for f in compare(state, specs, entries, {"acuerdo": "bbb"})] == ["contenido_cambio"]
    [finding] = compare(state, specs, entries, {}, errors={"acuerdo": "timeout"})
    assert finding.kind == "error" and "timeout" in finding.detail


def test_accept_moves_the_baseline_so_the_alert_does_not_repeat(entries):
    specs, state, _ = baseline(entries)
    moved = [IndexEntry(e.section, e.title, e.pdf_path, "2026-12-01" if e.title.startswith("Reglamento de Tránsito") else e.reform_date, e.description) for e in entries]
    accept(state, "reglamento-transito", moved, {})
    assert compare(state, specs, moved, {"acuerdo": "aaa"}) == []


def test_fingerprint_is_stable_for_the_same_finding_and_differs_for_another():
    a = Finding("x", "nueva_version", "d", new_url="u")
    assert a.fingerprint == Finding("x", "nueva_version", "d", new_url="u").fingerprint
    assert a.fingerprint != Finding("x", "nueva_version", "d", new_url="v").fingerprint


def test_report_lists_findings_and_the_next_step():
    assert "Sin cambios" in render_report([])
    text = render_report([Finding("ley-movilidad", "nueva_version", "cambió", new_url="https://x")])
    assert "ley-movilidad" in text and "https://x" in text and "accept" in text


def test_fetch_index_paginates_until_a_short_page_and_never_reads_an_empty_one_as_no_change():
    sample_items = parse_index(SAMPLE, "x")
    full_page = SAMPLE  # 11 items: shorter than a page, so each section stops after page 0
    calls = []

    def fetch(url):
        calls.append(url)
        return full_page

    got = fetch_index(fetch, pause=0)
    assert len(got) == 3 * len(sample_items) and len(calls) == 3
    with pytest.raises(IndexStructureError):
        fetch_index(lambda url: "<html>mantenimiento</html>", pause=0)
