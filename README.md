# PBL-MOT

YOLO-based Multi-Object Tracking pipeline with Itti Saliency Evaluation.

## Features

- **Multi-Object Tracking** — Ultralytics YOLO `model.track()` with persistent IDs across frames
- **MOTChallenge Output** — Standard 10-column format (frame, id, bbox, conf, class)
- **Itti Saliency Evaluation** — GPU-accelerated per-bbox mean saliency (appended as column 11)
- **Multi-GPU Parallel** — Round-robin video distribution across GPUs
- **Visualization** — `--save-vid` (bounding boxes) / `--plot-tracks` (trajectory lines)
- **Tracker Config** — BoT-SORT / ByteTrack, ReID, CLI parameter overrides

## Quick Start

```bash
conda activate py310
pip install ultralytics

# Track all videos
python -m MOT.run --input data/pbl/ --output outputs/

# With ReID + visualization + saliency
python -m MOT.run --input data/pbl/ --output outputs/ --with-reid --save-vid --eval-saliency
```

## Output Structure

```
outputs/
├── class_mapping.txt              # COCO class ID → name
├── tracking_summary.log           # Batch summary
├── Sub140/
│   └── Task7_AV_Trial1~/
│       ├── tracking_results.txt   # MOTChallenge format (+ saliency col 11)
│       ├── tracking.log           # Per-video log (MOT + saliency timing)
│       ├── tracked_video.avi      # (--save-vid)
│       └── tracked_trajectories.avi  # (--plot-tracks)
```

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | Video file or directory (recursive) |
| `--output` | `outputs` | Output root (mirrors input structure) |
| `--model` | `yolo26l.pt` | YOLO model (n/s/m/l/x) |
| `--tracker` | `botsort.yaml` | Tracker config or custom YAML path |
| `--conf` | `0.4` | Detection confidence threshold |
| `--iou` | `0.7` | IoU threshold |
| `--with-reid` | off | Enable Re-Identification |
| `--save-vid` | off | Save annotated video |
| `--plot-tracks` | off | Save trajectory video |
| `--eval-saliency` | off | Compute Itti saliency per bbox |
| `--workers` | `0` (auto) | Parallel workers (one per GPU) |

## Standalone Saliency Evaluation

Re-run saliency without re-tracking:

```bash
python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/
```

## Documentation

- **English**: [MOT/docs/en/](MOT/docs/en/README.md)
- **中文**: [MOT/docs/zh/](MOT/docs/zh/README.md)
