"""Steps 1-3: extraction, reproduction of the reference papers' own numbers, audit of BASE's transcription."""
import step2_reproduce as s2
import step3_audit_base as s3
import verify_pdf_text
from common import load_extracted, T5


def test_extracted_has_citations_and_constants():
    d = load_extracted()
    tc = d["time_constants_ms"]
    assert tc["BASE"]["T_C"] == 0.32 and tc["BASE"]["T_ECM"] == 17.1 and tc["BASE"]["T_SE_D"] == 5.6
    assert tc["JIANG"] == {"cite": tc["JIANG"]["cite"], "status": "VERIFIED", "note": tc["JIANG"]["note"], "T_H": 0.20, "T_C": 32.40}
    assert tc["CHANGLE"]["t_mul"] == 63.075 and tc["CHANGLE"]["t_h"] == 0.5
    for k in ("BASE", "JIANG", "CHANGLE", "DHILLON"):
        assert "cite" in tc[k]


def test_pdf_strings_present_on_cited_pages():
    ok, rows = verify_pdf_text.run()
    assert ok, [r for r in rows if r[3] != "FOUND"]


def test_jiang_totals_match_table2():
    rows = s2.jiang(load_extracted())
    ov = [r for r in rows if r[1].startswith("overall")]
    assert len(ov) == 6 and all(r[4] == "MATCH" for r in ov)
    t = {(r[0], r[1]): r[3] for r in rows}
    assert t[("Jiang_ours", "time overall (ms)")] == 198.6 and t[("Jiang_ours", "time P3 (ms)")] == 131.0


def test_changle_only_p2_user_mismatches():
    rows = s2.changle(load_extracted())
    bad = [r for r in rows if r[4].startswith("MISMATCH")]
    assert len(bad) == 1 and bad[0][0] == "TIII P2 user"
    assert bad[0][2] == 0.12765 and bad[0][3] == 0.12965
    assert sum(r[4] == "MATCH" for r in rows if r[0].startswith("T")) == 17
    assert any("CONTRADICTED" in r[4] for r in rows)


def test_changle_14x_claim():
    rows = [r for r in s2.changle(load_extracted()) if "14x" in r[0]]
    assert all(14.4 < r[3] < 14.6 for r in rows)


def test_dhillon_has_no_constants_and_totals():
    rows = s2.dhillon(load_extracted())
    tot = {r[0]: r[3] for r in rows if r[1].startswith("sum")}
    assert tot["Proposed"] == 22 and tot["Turkanovic_26"] == 19


def test_audit_findings_tags():
    F = {f[0]: f for f in s3.build()}
    assert F["F1"][2] == "CONTRADICTED"            # Turkanovic device/server swapped in BASE
    assert T5["Turkanovic [12]"]["device"]["H"] == 7 and T5["Turkanovic [12]"]["server"]["H"] == 5
    assert F["F2"][2] == "CONFIRMED"
    assert F["F4"][2].startswith("CONTRADICTED")
    assert F["F7"][2] == "CONTRADICTED" and F["F8"][2] == "UNVERIFIED" and F["F13"][2] == "CONTRADICTED"
    assert F["F12"][2] == "CONFIRMED"
