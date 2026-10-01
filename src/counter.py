"""
Line-crossing counter for LPG cylinders.

Why line-crossing instead of per-frame counting:
  Per-frame counting says "I see 5 cylinders right now" and hopes the number
  is stable. It isn't -- occlusion, camera jitter, and new arrivals make it
  jump. Line-crossing says "3 cylinders have crossed this line so far" and
  only increments, so the count is monotonic and auditable.

How it works:
  1. YOLO detects cylinders in each frame -> bounding boxes + class (size).
  2. ByteTrack assigns a stable ID to each detection across frames.
  3. When a tracked object's center crosses the counting line, it's counted
     once and its size is recorded.
  4. The count only goes up. If the cashier disagrees, they correct it in
     the UI, and both numbers are saved.

This module is pure Python with no ML dependencies, so it can be tested
without a GPU. The pipeline (pipeline.py) connects it to YOLO and the camera.
"""

from dataclasses import dataclass, field
from enum import Enum


class Direction(Enum):
    DOWN = "down"   # objects moving top -> bottom
    UP = "up"       # objects moving bottom -> top


@dataclass
class CountingLine:
    """A horizontal line across the frame. Objects are counted when their
    center crosses it in the configured direction."""
    y: int                           # pixel row
    direction: Direction = Direction.DOWN
    margin: int = 10                 # hysteresis band to avoid flicker


@dataclass
class TrackedObject:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    center_y: int
    prev_center_y: int | None = None
    counted: bool = False
    armed: bool = False   # True once the object has been on the "before" side


@dataclass
class CountResult:
    total: int = 0
    by_size: dict = field(default_factory=dict)    # {"20lb": 5, "30lb": 2}
    confidences: list = field(default_factory=list)
    events: list = field(default_factory=list)     # for the audit log

    @property
    def avg_confidence(self):
        return sum(self.confidences) / len(self.confidences) if self.confidences else 0.0

    def to_dict(self):
        return {
            "total": self.total,
            "by_size": dict(self.by_size),
            "avg_confidence": round(self.avg_confidence, 3),
        }


class CylinderCounter:
    """Stateful counter. Feed it tracked detections frame by frame."""

    def __init__(self, line: CountingLine, size_labels: list[str] | None = None):
        self.line = line
        self.size_labels = size_labels or ["20lb", "30lb", "100lb"]
        self.result = CountResult()
        self._tracks: dict[int, TrackedObject] = {}

    def update(self, detections: list[dict]) -> list[dict]:
        """Process one frame of tracked detections.

        Each detection is a dict with:
          track_id, class_id, class_name, confidence, bbox (x1,y1,x2,y2)

        Returns a list of newly counted objects (those that just crossed).
        """
        newly_counted = []
        current_ids = set()

        for det in detections:
            tid = det["track_id"]
            cx = (det["bbox"][0] + det["bbox"][2]) / 2
            cy = (det["bbox"][1] + det["bbox"][3]) / 2
            current_ids.add(tid)

            if tid in self._tracks:
                obj = self._tracks[tid]
                obj.prev_center_y = obj.center_y
                obj.center_y = int(cy)
                obj.confidence = det["confidence"]
            else:
                obj = TrackedObject(
                    track_id=tid,
                    class_id=det["class_id"],
                    class_name=det.get("class_name", "unknown"),
                    confidence=det["confidence"],
                    center_y=int(cy),
                )
                self._tracks[tid] = obj

            # Arm the object as soon as it's clearly on the "before" side.
            self._check_arm(obj)

            if not obj.counted:
                crossed = self._crossed_line(obj)
                if crossed:
                    obj.counted = True
                    size = obj.class_name
                    self.result.total += 1
                    self.result.by_size[size] = self.result.by_size.get(size, 0) + 1
                    self.result.confidences.append(obj.confidence)
                    event = {
                        "track_id": tid,
                        "size": size,
                        "confidence": round(obj.confidence, 3),
                        "count_at": self.result.total,
                    }
                    self.result.events.append(event)
                    newly_counted.append(event)

        # Prune tracks that disappeared (left frame or occluded too long).
        gone = set(self._tracks) - current_ids
        for tid in gone:
            del self._tracks[tid]

        return newly_counted

    def _check_arm(self, obj: TrackedObject):
        """Mark the object as armed once it's clearly on the 'before' side."""
        y = self.line.y
        margin = self.line.margin
        if self.line.direction == Direction.DOWN:
            if obj.center_y < y - margin:
                obj.armed = True
        else:
            if obj.center_y > y + margin:
                obj.armed = True

    def _crossed_line(self, obj: TrackedObject) -> bool:
        """Has the armed object reached the 'after' side?"""
        y = self.line.y
        margin = self.line.margin
        if not obj.armed:
            return False
        if self.line.direction == Direction.DOWN:
            return obj.center_y >= y + margin
        else:
            return obj.center_y <= y - margin

    def reset(self):
        self.result = CountResult()
        self._tracks.clear()
