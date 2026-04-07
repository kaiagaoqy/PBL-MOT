# YOLO Multi-Object Tracking Pipeline

## Overview

This pipeline provides a complete multi-object tracking (MOT) solution built on top of the [Ultralytics YOLO](https://docs.ultralytics.com/) `model.track()` API. It processes video files (or entire directory trees of videos), detects objects frame by frame, assigns persistent track IDs across frames, and outputs results in the standard MOTChallenge format.

### Key Capabilities

- **Persistent identity tracking** -- Each detected object receives a unique ID that is maintained across consecutive frames, even through brief occlusions (especially when ReID is enabled).
- **MOTChallenge-format output** -- Results are written in the standard 10-column text format used by the MOT community, making them compatible with standard evaluation tools.
- **Batch processing** -- Point the pipeline at a directory tree and it will recursively discover and process every video, mirroring the input directory structure in the output.
- **Visualization** -- Two complementary visualization modes: Ultralytics built-in bounding-box annotation (`--save-vid`) and custom trajectory rendering with movement history lines (`--plot-tracks`).
- **Configurable tracker** -- Choose between BoT-SORT (with optional ReID) and ByteTrack, and fine-tune every tracker parameter via CLI flags or a custom YAML file.
- **Saliency evaluation** -- Optionally compute per-bbox Itti saliency scores after tracking (`--eval-saliency`). The GPU-accelerated Itti visual attention model computes a mean saliency value for each bounding box, appended as column 11 to `tracking_results.txt`.

### Relationship to BoostTrack and TrackTrack

This pipeline uses the same underlying tracker algorithms (BoT-SORT and ByteTrack) that power state-of-the-art results on the MOT17 and MOT20 benchmarks. BoT-SORT, in particular, is the foundation behind **BoostTrack** (a top-performing method on MOT17/MOT20). The tracker configuration options exposed here -- ReID, global motion compensation, association thresholds -- are the same levers used to achieve competitive benchmark results.

**TrackTrack** (CVPR 2025) builds on these ideas with additional tracking refinements. While this pipeline does not implement TrackTrack directly, the modular design means that advances from TrackTrack or similar methods can be integrated by swapping in a custom tracker configuration YAML.

---

## Quick Start

### 1. Activate the environment

```bash
conda activate py310
```

### 2. Run tracking on a directory of videos

```bash
python -m MOT.run --input data/pbl/ --output outputs/
```

Or on a single video file:

```bash
python -m MOT.run --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 --output outputs/
```

### 3. Run with visualization

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --save-vid --plot-tracks
```

### 4. Run with saliency evaluation

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --eval-saliency
```

This appends a mean Itti saliency score (column 11) to each detection in `tracking_results.txt`. See [Tracking Configuration -- Saliency Evaluation](tracking.md#saliency-evaluation) for details.

### 5. Run with a larger model and ReID

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --model yolo26x.pt --with-reid
```

### What to Expect

After a successful run, the output directory will contain:

| File | Description |
|------|-------------|
| `tracking_results.txt` | Per-video MOTChallenge format tracking results (one per video subdirectory). 10 columns by default; 11 columns when `--eval-saliency` is used (column 11 = mean Itti saliency). |
| `tracking.log` | Per-video log with run configuration, video metadata, and results summary |
| `class_mapping.txt` | COCO class ID to name mapping (one file in the output root) |
| `tracking_summary.log` | Batch-level summary covering all processed videos (in the output root) |
| `tracked_video.mp4` | (Optional, `--save-vid`) Annotated video with bounding boxes and track IDs |
| `tracked_trajectories.mp4` | (Optional, `--plot-tracks`) Video with trajectory lines showing movement paths |
| `tracker_config.yaml` | (When CLI overrides are used) Merged tracker configuration for reproducibility |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](installation.md) | Environment setup, dependencies, and verification |
| [Input Data Format](dataset.md) | Supported video formats, directory structure, and how output paths are computed |
| [Tracking Configuration](tracking.md) | **Complete reference** for CLI arguments, model selection, tracker selection, YAML configuration, CLI overrides, ReID, and saliency evaluation |
| [Visualization Options](visualization.md) | Detailed comparison of `--save-vid` vs `--plot-tracks`, combining both, and `--trail-length` |
| [Output Format](output.md) | Output directory structure, MOTChallenge format specification, log files, and auxiliary outputs |
| [COCO Class Reference](coco_classes.md) | Full table of all 80 COCO classes grouped by category with IDs |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions: GPU OOM, no detections, track ID jumps, codec errors, and more |
