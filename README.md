# lpg-counter-spike

Architecture spike for an LPG cylinder counting system on the Jetson Orin Nano.

## What's here
- **Line-crossing counter** (`src/counter.py`): counts cylinders as they cross a line, not per-frame. Handles jitter, occlusion recovery, and wrong-direction movement.
- **Size classifier** (`src/classify_size.py`): height-ratio estimation as a backup and sanity check for the YOLO classifier.
- **Pipeline** (`src/pipeline.py`): YOLO → ByteTrack → counter, structured for TensorRT on Jetson. Commented out (needs ultralytics on device).
- **Audit trail** (`db/001_schema.sql`): stores both AI and cashier-confirmed counts, with a correction log.
- **18 tests** across three files. Pure Python, no GPU needed.

```
python3 tests/test_counter.py    # 9 counting tests
python3 tests/test_classify.py   # 6 classification tests
python3 tests/test_db.py         # 3 database tests
```

No trained model — that needs your actual cylinder images under your lighting.
