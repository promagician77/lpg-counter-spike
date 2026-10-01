"""Tests for size classification by height ratio."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from classify_size import calibrate, classify_by_height, validate_classification


def test_calibration():
    # A 100lb cylinder (122cm) is 244 pixels tall -> 2.0 px/cm
    ppc = calibrate(122, 244)
    assert abs(ppc - 2.0) < 0.01


def test_classify_20lb():
    ppc = 2.0  # pixels per cm
    # 20lb is 46cm -> 92 pixels
    assert classify_by_height(92, ppc) == "20lb"


def test_classify_100lb():
    ppc = 2.0
    # 100lb is 122cm -> 244 pixels
    assert classify_by_height(244, ppc) == "100lb"


def test_ambiguous_height_returns_none():
    ppc = 2.0
    # 170cm -> doesn't match any size within 8cm tolerance
    assert classify_by_height(340, ppc, tolerance_cm=8.0) is None


def test_validation_agrees():
    ppc = 2.0
    r = validate_classification("20lb", 92, ppc)
    assert r["agree"] is True
    assert r["model_says"] == "20lb"
    assert r["height_says"] == "20lb"


def test_validation_disagrees():
    ppc = 2.0
    # Model says 20lb but height says 100lb
    r = validate_classification("20lb", 244, ppc)
    assert r["agree"] is False
    assert r["height_says"] == "100lb"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
    exit(0 if passed == len(tests) else 1)
