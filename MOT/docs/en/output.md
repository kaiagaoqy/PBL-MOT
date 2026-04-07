# Output Format

This guide describes the directory structure and contents of every file produced by the tracking pipeline.

---

## Output Directory Structure

The output mirrors the input directory hierarchy. Each video gets its own subdirectory named after the video's stem (filename without extension). Batch-level files are placed in the output root.

### Example: Directory Input

```
outputs/                            <-- Output root (--output)
  class_mapping.txt                 <-- COCO class ID to name mapping
  tracking_summary.log              <-- Batch-level summary
  tracker_config.yaml               <-- (Only when CLI overrides are used)
  Sub140/
    Task7_AV_Trial1~/               <-- Per-video output directory
      tracking_results.txt          <-- MOTChallenge format results
      tracking.log                  <-- Per-video run log
      tracked_video.mp4             <-- (Only with --save-vid)
      tracked_trajectories.mp4      <-- (Only with --plot-tracks)
    Task7_AV_Trial2~/
      tracking_results.txt
      tracking.log
  Sub141/
    Task7_AV_Trial1~/
      tracking_results.txt
      tracking.log
```

### Example: Single File Input

```
outputs/
  class_mapping.txt
  tracking_summary.log
  Task7_AV_Trial1~/
    tracking_results.txt
    tracking.log
```

---

## tracking_results.txt -- MOTChallenge Format

This is the primary output file. It contains all tracking detections for one video in the standard MOTChallenge format, with one detection per line. By default, each line has 10 columns. When `--eval-saliency` is used, a mean saliency score is appended as column 11.

### Format

```
frame,id,bb_left,bb_top,bb_width,bb_height,conf,class,-1,-1[,mean_saliency]
```

### Column Specification

| Column | Name | Type | Description |
|--------|------|------|-------------|
| 1 | `frame` | `int` | Frame number, **1-indexed**. The first frame of the video is frame 1. |
| 2 | `id` | `int` | Unique track ID assigned to this object. Persistent across frames for the same object. |
| 3 | `bb_left` | `float` | X coordinate of the **top-left corner** of the bounding box, in pixels. Rounded to 1 decimal place. |
| 4 | `bb_top` | `float` | Y coordinate of the **top-left corner** of the bounding box, in pixels. Rounded to 1 decimal place. |
| 5 | `bb_width` | `float` | Width of the bounding box in pixels. Rounded to 1 decimal place. |
| 6 | `bb_height` | `float` | Height of the bounding box in pixels. Rounded to 1 decimal place. |
| 7 | `conf` | `float` | Detection confidence score (0.0--1.0). Rounded to 2 decimal places. |
| 8 | `class` | `int` | COCO class ID of the detected object. See [COCO Class Reference](coco_classes.md) for the mapping. Use `class_mapping.txt` for a quick lookup. |
| 9 | `visibility` | `int` | Not used. Always `-1`. |
| 10 | `unused` | `int` | Not used. Always `-1`. |
| 11 | `mean_saliency` | `float` | **(Only with `--eval-saliency`)** Mean Itti saliency within the bounding box (0.0--1.0). Higher values indicate more visually salient regions. |

### Coordinate System

All coordinates are in the **original video resolution** (not the inference resolution). The origin (0, 0) is the top-left corner of the frame. X increases to the right; Y increases downward.

```
(0,0) ---------> X (bb_left)
  |
  |    +-------+
  |    | bbox  |  bb_width
  |    +-------+
  |    bb_height
  v
  Y (bb_top)
```

### Example

Without saliency (default):
```
1,1,245.3,120.7,85.2,190.5,0.92,0,-1,-1
1,2,580.1,200.3,60.0,145.8,0.87,0,-1,-1
2,1,248.1,121.2,84.9,189.8,0.91,0,-1,-1
```

With `--eval-saliency` (column 11 appended):
```
1,1,245.3,120.7,85.2,190.5,0.92,0,-1,-1,0.2065
1,2,580.1,200.3,60.0,145.8,0.87,0,-1,-1,0.3150
2,1,248.1,121.2,84.9,189.8,0.91,0,-1,-1,0.2235
```

In this example:

- Frame 1 has three detections: two persons (class 0) with track IDs 1 and 2, and one car (class 2) with track ID 3.
- Frame 2 has two detections: the same two persons (track IDs 1 and 2) with slightly updated positions.
- Track ID 3 (the car) was not detected in frame 2 -- this is normal and means the object was either not visible or fell below the confidence threshold. If it reappears within `track_buffer` frames, it will retain ID 3.

### Notes

- Frames with no detections are omitted entirely (not represented as empty lines).
- The file contains no header row. It starts directly with data.
- Bounding box coordinates are computed from the YOLO `xyxy` format (x1, y1, x2, y2) and converted to `xywh` (left, top, width, height).

---

## tracking.log -- Per-Video Run Log

Written for **every** video, regardless of whether tracking succeeded or failed. Located in the per-video output directory.

### Successful Run

```
==================================================
Tracking Log: Task7_AV_Trial1~.mp4
==================================================
Date:       2026-04-06 14:30:15
Model:      yolo26n.pt
Tracker:    botsort.yaml
Confidence: 0.25 | IoU: 0.7 | imgsz: 640
Device:     auto

Video Info:
  Path:       /data/pbl/Sub140/Task7_AV_Trial1~.mp4
  Resolution: 1920x1080
  Frames:     5400
  FPS:        30.0
  Duration:   180.0s

Results:
  Status:      SUCCESS
  Tracks:      12
  Detections:  45230
  Time:        85.3s
  Process FPS: 63.3
  Output:      tracking_results.txt
  Video:       tracked_video.mp4
==================================================

Saliency Evaluation:
  Status:      SUCCESS
  Frames:      103
  Detections:  198
  Time:        11.1s
==================================================
```

The "Saliency Evaluation" section is only appended when `--eval-saliency` is used.

### Failed Run

```
==================================================
Tracking Log: corrupted_video.mp4
==================================================
Date:       2026-04-06 14:32:00
Model:      yolo26n.pt
Tracker:    botsort.yaml
Confidence: 0.25 | IoU: 0.7 | imgsz: 640
Device:     auto

Video Info:
  Path:       /data/pbl/Sub140/corrupted_video.mp4

Results:
  Status:      FAILED
  Error:       Cannot open video file: /data/pbl/Sub140/corrupted_video.mp4
  Traceback:
    Traceback (most recent call last):
      File "MOT/tracker.py", line 111, in process_video
        ...
    RuntimeError: Cannot open video file: ...
==================================================
```

---

## class_mapping.txt -- COCO Class Mapping

A single file written to the output root. Maps numeric COCO class IDs to human-readable names. This file is useful for interpreting the `class` column (column 8) in `tracking_results.txt`.

### Format

```
# YOLO COCO Class ID Mapping
# Used to interpret the 'class' column (column 8) in tracking_results.txt
# Format: class_id: class_name

0: person
1: bicycle
2: car
3: motorcycle
...
79: toothbrush
```

The class mapping is obtained from `model.names` and reflects the COCO dataset's 80 object categories. See [COCO Class Reference](coco_classes.md) for the complete list.

---

## tracking_summary.log -- Batch Summary

Written to the output root after all videos have been processed. Provides a concise summary of the entire batch run.

### Format

```
==================================================
YOLO Tracking Run Summary
==================================================
Date:  2026-04-06 14:35:00
Model: yolo26n.pt | Tracker: botsort.yaml
Conf:  0.25 | IoU: 0.7 | imgsz: 640
Input: data/pbl/

--------------------------------------------------
[1/5] Task7_AV_Trial1~ -- SUCCESS -- 5400 frames, 12 tracks, 85.3s
[2/5] Task7_AV_Trial2~ -- SUCCESS -- 3600 frames, 8 tracks, 56.1s
[3/5] Task8_AV_Trial1~ -- SUCCESS -- 7200 frames, 15 tracks, 112.0s
[4/5] corrupted_video -- FAILED -- Cannot open video file: ...
[5/5] Task8_AV_Trial2~ -- SUCCESS -- 4800 frames, 10 tracks, 74.5s
--------------------------------------------------
Totals: 5 videos (4 success, 1 failed) | 21000 frames | 327.9s
==================================================
```

---

## tracked_video.mp4 -- Annotated Video (Optional)

Only produced when `--save-vid` is passed. Located in the per-video output directory.

Contains the original video frames annotated by Ultralytics with bounding boxes, track IDs, and class labels. No trajectory lines are included.

---

## tracked_trajectories.mp4 -- Trajectory Video (Optional)

Only produced when `--plot-tracks` is passed. Located in the per-video output directory.

Contains the original video frames annotated with bounding boxes, track IDs, class labels, and color-coded trajectory polylines showing each object's movement history. The trail length is controlled by `--trail-length`.

---

## tracker_config.yaml -- Merged Tracker Configuration (Conditional)

Only produced when CLI tracker override arguments are used (e.g., `--with-reid`, `--track-buffer 60`). Written to the output root.

Contains the complete, merged tracker configuration: the base YAML config with CLI overrides applied. This file serves as a reproducible record of the exact tracker settings used for the run.

### Example

```yaml
tracker_type: botsort
track_high_thresh: 0.5
track_low_thresh: 0.1
new_track_thresh: 0.25
track_buffer: 60
match_thresh: 0.8
fuse_score: true
gmc_method: sparseOptFlow
proximity_thresh: 0.5
appearance_thresh: 0.8
with_reid: true
model: auto
```

This file is not produced when no CLI overrides are specified, because the unmodified built-in config is used directly.

---

## Related Documentation

- [Input Data Format](dataset.md) -- How input paths map to output paths.
- [Tracking Configuration](tracking.md) -- Full parameter reference.
- [Visualization Options](visualization.md) -- Details on the two video output modes.
- [COCO Class Reference](coco_classes.md) -- Full class ID table.
