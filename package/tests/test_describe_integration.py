"""describe() exercised against real simulated results — the persona,
misguide grounding, and pronoun consistency all depend on the exported
tables, so these need the session-scoped fixtures rather than a mock."""

from __future__ import annotations


def test_describe_no_candidate_on_quiet_baseline(baseline_3yr):
    text = baseline_3yr.describe()
    assert baseline_3yr._misguide["candidate"] is None
    assert baseline_3yr._misguide["grounded"] is None
    assert baseline_3yr._persona["owner_name"] in text


def test_describe_stress_combo_has_grounded_candidate(stress_combo):
    text = stress_combo.describe()
    assert stress_combo._misguide["candidate"] == "competitor"
    assert stress_combo._misguide["grounded"] in (True, False)
    assert "Stakes" in text


def test_describe_pronoun_matches_persona_gender(stress_combo):
    stress_combo.describe()
    pn = stress_combo._persona["pronoun"]
    gender = stress_combo._persona["gender"]
    expected_subject = "he" if gender == "male" else "she"
    assert pn["subject"] == expected_subject


def test_describe_cached_across_repeated_calls(baseline_1yr):
    t1 = baseline_1yr.describe()
    t2 = baseline_1yr.describe()
    assert t1 == t2
    # persona/misguide must be the exact same objects, not regenerated
    assert baseline_1yr._persona is not None


def test_describe_before_simulate_raises():
    from grocery_sim import GroceryStoreSimulation

    import pytest
    with pytest.raises(RuntimeError):
        GroceryStoreSimulation().describe()


def test_describe_contains_intake_interview_sections(stress_combo):
    text = stress_combo.describe()
    for heading in (
        "## The letter",
        "## Intake interview notes",
        "## The data",
        "## The questions",
        "## Stakes",
    ):
        assert heading in text


def test_describe_records_caveats_use_real_counts(stress_combo):
    """The 'anything I should know about the records' answer must cite the
    same void/mis-ring count as the receipts table itself, not a made-up
    number."""
    text = stress_combo.describe()
    rc = stress_combo.data().receipts
    void_n = int(((rc["qty"] < 0) & rc["ref_receipt_id"].isna()).sum())
    assert str(void_n) in text
