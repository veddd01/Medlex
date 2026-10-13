from src.emergency import check_emergency

def test_emergency_patterns():
    assert check_emergency("I am having a heart attack") is not None
    assert check_emergency("I feel suicidal") is not None
    assert check_emergency("Cannot breathe") is not None
    assert check_emergency("Chest pain is severe") is not None

def test_non_emergency():
    assert check_emergency("What are the symptoms of a cold?") is None
    assert check_emergency("How to lower blood pressure") is None

def test_case_insensitivity():
    assert check_emergency("HEART ATTACK") is not None
    assert check_emergency("Suicide") is not None
