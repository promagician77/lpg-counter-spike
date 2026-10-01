"""Tests for the cylinder counting logic. No ML dependencies needed."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from counter import CylinderCounter, CountingLine, Direction


def make_det(track_id, y, class_name="20lb", conf=0.92):
    return {"track_id": track_id, "class_id": 0, "class_name": class_name,
            "confidence": conf, "bbox": [100, y - 20, 200, y + 20]}


def test_object_crossing_down_is_counted_once():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    # Object approaches from above
    c.update([make_det(1, 250)])
    c.update([make_det(1, 280)])
    c.update([make_det(1, 310)])  # crosses
    c.update([make_det(1, 340)])  # already counted
    c.update([make_det(1, 370)])
    assert c.result.total == 1, f"expected 1, got {c.result.total}"
    assert c.result.by_size["20lb"] == 1


def test_object_moving_wrong_direction_is_not_counted():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    # Object moves bottom to top
    c.update([make_det(1, 350)])
    c.update([make_det(1, 320)])
    c.update([make_det(1, 280)])
    c.update([make_det(1, 250)])
    assert c.result.total == 0


def test_multiple_objects_crossing():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    c.update([make_det(1, 250), make_det(2, 260, "30lb")])
    c.update([make_det(1, 310), make_det(2, 290)])       # 1 crosses, 2 hasn't yet
    assert c.result.total == 1
    c.update([make_det(1, 350), make_det(2, 310)])       # 2 crosses
    assert c.result.total == 2
    assert c.result.by_size == {"20lb": 1, "30lb": 1}


def test_object_hovering_near_line_is_not_double_counted():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=10))
    c.update([make_det(1, 280)])
    c.update([make_det(1, 295)])  # inside margin, not yet
    c.update([make_det(1, 305)])  # still inside margin
    c.update([make_det(1, 315)])  # crossed past margin
    c.update([make_det(1, 295)])  # bounces back (wind, jitter)
    c.update([make_det(1, 315)])  # comes back through
    assert c.result.total == 1, "jitter caused double count"


def test_disappeared_track_is_cleaned_up():
    c = CylinderCounter(CountingLine(y=300))
    c.update([make_det(1, 250)])
    c.update([make_det(1, 280)])
    c.update([])  # object disappeared (left frame or occluded)
    assert 1 not in c._tracks


def test_count_only_increases():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    counts = []
    for y in range(200, 400, 15):
        c.update([make_det(1, y)])
        counts.append(c.result.total)
    # The count should never decrease
    for i in range(1, len(counts)):
        assert counts[i] >= counts[i - 1], "count decreased"


def test_reset_clears_everything():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    c.update([make_det(1, 250)])
    c.update([make_det(1, 310)])
    assert c.result.total == 1
    c.reset()
    assert c.result.total == 0
    assert len(c._tracks) == 0


def test_confidence_is_recorded():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    c.update([make_det(1, 250, conf=0.87)])
    c.update([make_det(1, 310, conf=0.87)])
    assert abs(c.result.avg_confidence - 0.87) < 0.01


def test_result_to_dict():
    c = CylinderCounter(CountingLine(y=300, direction=Direction.DOWN, margin=5))
    c.update([make_det(1, 250, "100lb")])
    c.update([make_det(1, 310, "100lb")])
    d = c.result.to_dict()
    assert d["total"] == 1
    assert d["by_size"]["100lb"] == 1
    assert 0 < d["avg_confidence"] <= 1.0


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
