"""MOT: YOLO-based multi-object tracking pipeline.

Track all objects in video(s) using Ultralytics YOLO and output:
- MOTChallenge format tracking results (.txt per video)
- Per-video tracking log (.log per video)
- Class ID mapping file (class_mapping.txt)
- Overall summary log
- (Optional) Annotated tracking video

Usage:
    conda activate py310
    python -m MOT.run --input data/pbl/ --output outputs/
"""
