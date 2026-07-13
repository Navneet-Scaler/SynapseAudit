from src.rules import RuleEngine

def test_modifier_25_missing():
    engine = RuleEngine()
    # E/M code (99213) and procedure (93451) both present, but no modifier
    result = engine.check_modifier_25(
        predicted_codes="99213,93451",
        predicted_modifiers="",
        note_text="Separate procedures were performed on the same day."
    )
    assert result["passed"] is False
    assert result["error_type"] == "wrong_modifier"

def test_modifier_25_passed():
    engine = RuleEngine()
    result = engine.check_modifier_25(
        predicted_codes="99213,93451",
        predicted_modifiers="99213:25",
        note_text="Separate procedures were performed on the same day."
    )
    assert result["passed"] is True

def test_hcc_gap_detected():
    engine = RuleEngine()
    result = engine.check_hcc_gaps(
        predicted_codes="M23.22",
        note_text="Patient has history of chronic diabetes mellitus type 2."
    )
    assert result["passed"] is False
    assert result["error_type"] == "hcc_miss"

def test_duplicate_codes():
    engine = RuleEngine()
    result = engine.check_duplicate_codes(predicted_codes="97110,97110")
    assert result["passed"] is False
    assert result["error_type"] == "ncci_conflict"
