"""
Detection pipeline for the Jetson Orin Nano.

This ties together:
  Camera (RTSP or USB) -> YOLO (TensorRT) -> ByteTrack -> CylinderCounter -> API

On the Jetson, YOLO runs through TensorRT for real-time speed (~30 fps on
Orin Nano with a YOLOv8n model at 640x640). The export script handles the
conversion.

This file imports ultralytics and supervision, which are installed on the
Jetson but not in this spike's test environment. The counter logic is tested
separately in pure Python.
"""

# -- Imports that need the ML stack (Jetson or dev machine with GPU) --
# from ultralytics import YOLO
# import supervision as sv
# import cv2
# import numpy as np

from counter import CylinderCounter, CountingLine, Direction


# Size labels matching the trained model's class indices.
SIZE_LABELS = ["20lb", "30lb", "100lb"]


def build_pipeline(
    model_path: str = "models/cylinders.engine",   # TensorRT engine
    camera_source: str | int = 0,                   # RTSP URL or USB index
    line_y: int = 360,                               # counting line position
    direction: str = "down",
    confidence: float = 0.45,
    iou: float = 0.5,
):
    """
    Returns a generator that yields (frame, count_result, new_events) per frame.

    In production:
      for frame, result, events in build_pipeline(camera_source="rtsp://..."):
          if events:
              send_to_ui(result)  # push via WebSocket
          display(frame)          # optional local preview
    """
    # -- The lines below run on Jetson with the ML stack installed. --
    # model = YOLO(model_path, task="detect")
    # tracker = sv.ByteTrack(minimum_matching_threshold=0.8)
    # counter = CylinderCounter(
    #     CountingLine(y=line_y, direction=Direction(direction)),
    #     size_labels=SIZE_LABELS,
    # )
    # cap = cv2.VideoCapture(camera_source)
    #
    # while cap.isOpened():
    #     ret, frame = cap.read()
    #     if not ret:
    #         break
    #
    #     # 1. Detect
    #     results = model(frame, conf=confidence, iou=iou, verbose=False)[0]
    #     detections = sv.Detections.from_ultralytics(results)
    #
    #     # 2. Track (stable IDs across frames)
    #     detections = tracker.update_with_detections(detections)
    #
    #     # 3. Count (line-crossing)
    #     tracked = []
    #     for i, (bbox, _, conf, class_id, track_id, _) in enumerate(detections):
    #         tracked.append({
    #             "track_id": int(track_id),
    #             "class_id": int(class_id),
    #             "class_name": SIZE_LABELS[int(class_id)] if int(class_id) < len(SIZE_LABELS) else "unknown",
    #             "confidence": float(conf),
    #             "bbox": bbox.tolist(),
    #         })
    #     events = counter.update(tracked)
    #
    #     # 4. Annotate the frame for the local preview
    #     annotated = frame.copy()
    #     # ... draw boxes, line, count text ...
    #
    #     yield annotated, counter.result, events

    # Placeholder for environments without the ML stack.
    raise NotImplementedError(
        "This pipeline needs ultralytics, supervision, and OpenCV. "
        "Install them on the Jetson or a dev machine with a GPU."
    )
