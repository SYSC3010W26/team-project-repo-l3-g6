import pytest
from motorctl.src.actuator import translate_singmaster_to_macro

def test_translation_cw():
    assert translate_singmaster_to_macro("U") == "MOVEM31"
    assert translate_singmaster_to_macro("R") == "MOVEM11"
    assert translate_singmaster_to_macro("B") == "MOVEM51"

def test_translation_ccw():
    assert translate_singmaster_to_macro("U'") == "MOVEM32"
    assert translate_singmaster_to_macro("L'") == "MOVEM22"

def test_translation_180():
    assert translate_singmaster_to_macro("F2") == "MOVEM43"
    assert translate_singmaster_to_macro("R2") == "MOVEM13"

def test_invalid_notation():
    assert translate_singmaster_to_macro("X") == ""
    assert translate_singmaster_to_macro("") == ""

def test_case_insensitivity():
    assert translate_singmaster_to_macro("u") == "MOVEM31"