import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.models.domain import EMBEDDING_DIMENSIONS, LegalChunk, LegalSanction, OfficialSource, SanctionStatus
from app.services.ingestion import sanction_store as store
from app.services.ingestion.sanctions import chunk_hash

CHUNKS = json.loads((Path(__file__).parent / "fixtures" / "sanctions" / "chunks.json").read_text(encoding="utf-8"))
SLUG = "reglamento-transito"


def _seed(db, *keys: str, current: bool = True) -> OfficialSource:
    source = OfficialSource(slug=SLUG, title="Reglamento", kind="reglamento", url="https://x.mx/r.pdf", sha256="c" * 64, is_current=current)
    db.add(source)
    db.flush()
    for key in keys:
        chunk = CHUNKS[key]
        db.add(LegalChunk(
            source_id=source.id, article=chunk["article"], fraction=chunk["fraction"], heading_path="x", text=chunk["text"],
            page_start=1, page_end=1, token_count=1, embedding=[0.0] * EMBEDDING_DIMENSIONS,
        ))
    db.flush()
    return source


def test_sync_creates_pending_rows_and_is_idempotent(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", "43")
        first = store.sync_pending(db, SLUG)
        assert (first.created, first.unchanged) == (12, 0)  # 5 incisos + 7 fractions
        assert {r.status for r in db.scalars(select(LegalSanction))} == {SanctionStatus.PENDING}
        second = store.sync_pending(db, SLUG)
        assert (second.created, second.unchanged, second.replaced) == (0, 12, 0)


def test_a_verified_row_stays_verified_when_nothing_changed(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II")
        store.sync_pending(db, SLUG)
        row = db.scalars(select(LegalSanction).where(LegalSanction.inciso == "b")).one()
        row.status, row.reviewed_by = SanctionStatus.VERIFIED, "Revisora"
        store.sync_pending(db, SLUG)
        db.refresh(row)
        assert row.status is SanctionStatus.VERIFIED and row.reviewed_by == "Revisora"


def test_manual_rows_capture_what_the_extractor_cannot_read(client):
    _, factory = client
    with factory() as db:
        _seed(db, "table")
        manual = [{
            "source_slug": SLUG, "article": "6", "chunk_fraction": "V", "fraction": "V", "conduct_text": "no respetar la preferencia",
            "clause_text": "Conductores de vehículos de uso particular. 10 a 20 veces 10 veces 15 veces 20 veces 3 puntos",
            "applies_to": "vehículos de uso particular", "uma_min": "10", "uma_mid": "15", "uma_max": "20", "points_license": 3,
        }]
        report = store.sync_pending(db, SLUG, manual)
        assert report.created == 1 and report.issues == []  # the "tabla" issue is resolved by hand
        row = db.scalars(select(LegalSanction)).one()
        assert row.extractor_version == "manual" and row.ordinal >= store.MANUAL_ORDINAL_BASE
        assert row.uma_mid == Decimal("15")


def test_review_sheet_orders_by_risk_and_apply_only_verifies_what_was_marked(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II", "conditional")
        store.sync_pending(db, SLUG)
        sheet, counts = store.render_review(db, SLUG)
        assert counts[1] == 5 and counts[2] == 2  # 37 II maps clauses to incisos; Art. 9 IV has a vehicle override
        assert sheet.index("Tanda 1") < sheet.index("Tanda 2")
        assert "⟦" in sheet and "cinturón" in sheet

        seat_belt = next(r for r in db.scalars(select(LegalSanction)) if r.inciso == "b")
        line = f"- [ ] `{store.row_id(SLUG, '37', 'II', seat_belt.ordinal, seat_belt.chunk_hash)}`"
        assert line in sheet
        marked = sheet.replace(line, line.replace("[ ]", "[x]"))

        report = store.apply_review(db, SLUG, marked, "Revisora", datetime(2026, 10, 16, tzinfo=timezone.utc))
        assert (report.approved, report.rejected) == (1, 0) and report.unmarked == 6
        statuses = {r.inciso or r.applies_to: r.status for r in db.scalars(select(LegalSanction))}
        assert statuses["b"] is SanctionStatus.VERIFIED
        assert sum(1 for s in statuses.values() if s is SanctionStatus.VERIFIED) == 1


def test_a_rejected_mark_wins_over_approving_a_whole_tanda(client):
    _, factory = client
    with factory() as db:
        _seed(db, "43")  # seven fractions, one clause each: tanda 4
        store.sync_pending(db, SLUG)
        rows = list(db.scalars(select(LegalSanction).order_by(LegalSanction.ordinal)))
        sheet = "- [x] **APROBAR TODA LA TANDA 4** (x)\n" + "\n".join(
            f"- [{'!' if r.fraction == 'IV' else ' '}] `{store.row_id(SLUG, '43', None, r.ordinal, r.chunk_hash)}`" for r in rows
        )
        report = store.apply_review(db, SLUG, sheet, "Revisora")
        assert (report.approved, report.rejected) == (6, 1)
        assert {r.fraction: r.status for r in rows}["IV"] is SanctionStatus.REJECTED


def test_approving_a_tanda_does_not_reach_the_risky_ones(client):
    """The master checkbox exists only for tanda 4: rows that map clauses to incisos must be marked one by one."""
    _, factory = client
    with factory() as db:
        _seed(db, "37_II")
        store.sync_pending(db, SLUG)
        rows = list(db.scalars(select(LegalSanction)))
        sheet = "- [x] **APROBAR TODA LA TANDA 4** (x)\n" + "\n".join(
            f"- [ ] `{store.row_id(SLUG, '37', 'II', r.ordinal, r.chunk_hash)}`" for r in rows
        )
        report = store.apply_review(db, SLUG, sheet, "Revisora")
        assert report.approved == 0 and report.unmarked == 5


def test_verified_rows_survive_a_rebuild_through_the_git_file_and_go_stale_when_the_text_changes(client, tmp_path):
    _, factory = client
    path = tmp_path / "verified.json"
    with factory() as db:
        _seed(db, "37_II")
        store.sync_pending(db, SLUG)
        for row in db.scalars(select(LegalSanction)):
            row.status, row.reviewed_by = SanctionStatus.VERIFIED, "Revisora"
            row.reviewed_at = datetime(2026, 10, 16, tzinfo=timezone.utc)
        assert store.export_verified(db, SLUG, path) == 5
        db.commit()

    # a rebuilt database: same text, new chunk ids -> rows come back verified from the file
    with factory() as db:
        db.query(LegalSanction).delete()
        db.query(LegalChunk).delete()
        db.query(OfficialSource).delete()
        _seed(db, "37_II")
        store.sync_pending(db, SLUG)  # the extractor proposes the rows again; the file says which ones were approved
        loaded = store.load_verified(db, SLUG, path)
        assert loaded.loaded == 5 and loaded.unmatched == [] and loaded.diverged == []
        assert {r.status for r in db.scalars(select(LegalSanction))} == {SanctionStatus.VERIFIED}
        db.commit()

    # a reform that changes the article: nothing from the old text is loaded, and a verified row turns stale
    with factory() as db:
        chunk = db.scalars(select(LegalChunk)).one()
        old_hash = chunk_hash(chunk.text)
        chunk.text = chunk.text.replace("5, 7 o 10", "6, 8 o 12")
        assert chunk_hash(chunk.text) != old_hash
        assert store.mark_stale(db) == 5
        assert {r.status for r in db.scalars(select(LegalSanction))} == {SanctionStatus.STALE}
        db.query(LegalSanction).delete()
        assert store.load_verified(db, SLUG, path).unmatched  # entries from the old text are reported, not applied


def test_refresh_after_a_reingest_restores_what_was_verified_and_reports_the_health(client, tmp_path):
    """The whole point of step 6: a re-ingest (new chunk ids) must not lose what a person verified, and a reform
    must leave the changed article waiting for review instead of serving the old numbers."""
    _, factory = client
    path = tmp_path / "verified.json"
    with factory() as db:
        _seed(db, "37_II", "43")
        store.sync_pending(db, SLUG)
        for row in db.scalars(select(LegalSanction).where(LegalSanction.article == "37")):
            row.status, row.reviewed_by = SanctionStatus.VERIFIED, "Revisora"
            row.reviewed_at = datetime(2026, 10, 16, tzinfo=timezone.utc)
        store.export_verified(db, SLUG, path)
        db.commit()

    with factory() as db:  # --force re-ingest: every chunk is new, art. 43 was reformed, art. 37 was not
        db.query(LegalSanction).delete()
        db.query(LegalChunk).delete()
        db.query(OfficialSource).delete()
        original = CHUNKS["43"]["text"]
        CHUNKS["43"]["text"] = original.replace("40, 45 o 50", "45, 50 o 55")
        try:
            _seed(db, "37_II", "43")
        finally:
            CHUNKS["43"]["text"] = original
        result = store.refresh_sanctions(db, SLUG, [], path)
        assert result.loaded.loaded == 5 and result.loaded.unmatched == []
        assert result.health["verified"] == 5 and result.health["pending"] == 7
        assert result.health["verified_pct"] == round(100 * 5 / 12, 1)
        by_article = {}
        for row in db.scalars(select(LegalSanction)):
            by_article.setdefault(row.article, set()).add(row.status)
        assert by_article == {"37": {SanctionStatus.VERIFIED}, "43": {SanctionStatus.PENDING}}


def test_verified_content_is_not_restored_when_the_extractor_now_proposes_something_else(client, tmp_path):
    """An approval is for the content a person saw. If the extractor changed its mind, the row waits for review."""
    _, factory = client
    path = tmp_path / "verified.json"
    with factory() as db:
        _seed(db, "37_II")
        store.sync_pending(db, SLUG)
        for row in db.scalars(select(LegalSanction)):
            row.status, row.reviewed_by = SanctionStatus.VERIFIED, "Revisora"
            row.reviewed_at = datetime(2026, 10, 16, tzinfo=timezone.utc)
        store.export_verified(db, SLUG, path)
        entries = json.loads(path.read_text(encoding="utf-8"))
        for entry in entries:
            if entry["inciso"] == "b":
                entry["uma_min"] = "10"  # what was verified is not what the extractor proposes now
        path.write_text(json.dumps(entries), encoding="utf-8")
        for row in db.scalars(select(LegalSanction)):
            row.status, row.reviewed_by, row.reviewed_at = SanctionStatus.PENDING, None, None
        loaded = store.load_verified(db, SLUG, path)
        assert loaded.loaded == 4 and len(loaded.diverged) == 1
        belt = db.scalars(select(LegalSanction).where(LegalSanction.inciso == "b")).one()
        assert belt.status is SanctionStatus.PENDING and belt.uma_min == Decimal("5")


def test_an_article_wide_clause_in_one_fraction_chunk_covers_the_sibling_fractions(client):
    """Art. 45: "el incumplimiento de las obligaciones señaladas en el presente artículo" sits in fraction V only."""
    _, factory = client
    articles = json.loads((Path(__file__).parent / "fixtures" / "sanctions" / "articles.json").read_text(encoding="utf-8"))
    with factory() as db:
        source = OfficialSource(slug=SLUG, title="Reglamento", kind="reglamento", url="https://x.mx/r.pdf", sha256="d" * 64)
        db.add(source)
        db.flush()
        for chunk in articles["45"]:
            db.add(LegalChunk(source_id=source.id, article="45", fraction=chunk["fraction"], heading_path="x", text=chunk["text"],
                              page_start=1, page_end=1, token_count=1, embedding=[0.0] * EMBEDDING_DIMENSIONS))
        db.flush()
        store.sync_pending(db, SLUG)
        rows = list(db.scalars(select(LegalSanction).order_by(LegalSanction.id)))
        assert sorted(r.fraction for r in rows) == ["I", "II", "III", "IV", "V"]
        assert {(r.uma_min, r.uma_max) for r in rows} == {(Decimal("20"), Decimal("30"))}
        assert "Placas de matrícula" in next(r for r in rows if r.fraction == "I").conduct_text


def test_a_repaired_conduct_text_does_not_send_a_verified_row_back_to_review(client):
    _, factory = client
    with factory() as db:
        _seed(db, "37_II")
        store.sync_pending(db, SLUG)
        row = db.scalars(select(LegalSanction).where(LegalSanction.inciso == "b")).one()
        complete = row.conduct_text
        row.conduct_text = complete[:-1]  # the old extractor dropped the last letter
        row.status, row.reviewed_by = SanctionStatus.VERIFIED, "Revisora"
        report = store.sync_pending(db, SLUG)
        db.refresh(row)
        assert report.replaced == 0 and row.status is SanctionStatus.VERIFIED and row.conduct_text == complete
