"""Tests for the database schema and audit trail."""
import sqlite3, json, os

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'db')


def get_db():
    db = sqlite3.connect(":memory:")
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(open(os.path.join(SCHEMA_DIR, "001_schema.sql")).read())
    return db


def test_transaction_stores_ai_and_final():
    db = get_db()
    ai = json.dumps({"20lb": 10, "30lb": 3})
    final = json.dumps({"20lb": 11, "30lb": 3})  # cashier corrected
    db.execute(
        "INSERT INTO transactions (lane_id, ai_total, ai_breakdown, final_total, final_breakdown, cashier_name, status)"
        " VALUES (1, 13, ?, 14, ?, 'Maria', 'confirmed')", (ai, final))
    row = db.execute("SELECT ai_total, final_total, status FROM transactions").fetchone()
    assert row == (13, 14, "confirmed")


def test_correction_audit_trail():
    db = get_db()
    db.execute("INSERT INTO transactions (lane_id, ai_total) VALUES (1, 10)")
    tid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.execute(
        "INSERT INTO corrections (transaction_id, size_label, ai_count, corrected_count, reason, cashier_name)"
        " VALUES (?, '20lb', 5, 6, 'One was hidden behind another', 'Maria')", (tid,))
    corr = db.execute("SELECT size_label, ai_count, corrected_count, reason FROM corrections WHERE transaction_id = ?", (tid,)).fetchone()
    assert corr == ("20lb", 5, 6, "One was hidden behind another")


def test_cylinder_sizes_seeded():
    db = get_db()
    sizes = db.execute("SELECT label FROM cylinder_sizes ORDER BY label").fetchall()
    assert [s[0] for s in sizes] == ["100lb", "20lb", "30lb"]


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
