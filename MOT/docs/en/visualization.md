# Visualization Options

The pipeline provides two independent visualization modes that can be used separately or together. Each produces a separate output video file.

---

## `--save-vid`: Ultralytics Built-in Annotation

### What It Does

Enables Ultralytics' built-in `save=True` mode during tracking. Each frame is annotated with:

- **Bounding boxes** around each detected object.
- **Track IDs** displayed on each bounding box.
- **Class labels** (e.g., "person", "car") alongside the track ID.

This mode does **not** include trajectory lines or any movement history.

### Usage

```bash
python -m MOT.run --input video.mp4 --output outputs/ --save-vid
```

### Output

The annotated video is saved as `tracked_video.mp4` in the per-video output directory.

```
outputs/
  video_name/
    tracking_results.txt
    tracking.log
    tracked_video.mp4        <-- Ultralytics annotated video
```

### Implementation Details

- Ultralytics renders the annotations internally and saves the video to its default `runs/` directory.
- The pipeline automatically locates the saved video and moves it to the correct output directory, renaming it to `tracked_video.mp4`.
- The rendering is handled entirely by Ultralytics, so the visual style (colors, font, box thickness) follows Ultralytics defaults.
- Overhead is minimal since the annotation happens as part of the tracking loop.

---

## `--plot-tracks`: Trajectory Visualization

### What It Does

Enables custom trajectory rendering that draws, on each frame:

- **Bounding boxes** around each detected object (via Ultralytics' `result.plot()`).
- **Track IDs** displayed on each bounding box.
- **Class labels** alongside the track ID.
- **Trajectory lines** showing each object's movement path over past frames.

Each tracked object gets a color-coded polyline connecting its center-of-bounding-box positions across recent frames. The polyline color is deterministic based on the track ID, so the same object always has the same trajectory color.

### Usage

```bash
python -m MOT.run --input video.mp4 --output outputs/ --plot-tracks
```

### Output

The trajectory video is saved as `tracked_trajectories.mp4` in the per-video output directory.

```
outputs/
  video_name/
    tracking_results.txt
    tracking.log
    tracked_trajectories.mp4  <-- Trajectory visualization
```

### `--trail-length` Parameter

Controls how many past frames of trajectory to display for each tracked object.

```bash
python -m MOT.run --input video.mp4 --output outputs/ --plot-tracks --trail-length 50
```

| Value | Behavior |
|-------|----------|
| `30` (default) | Shows the last 30 frames of movement. At 30 FPS, this is approximately 1 second of trajectory history. |
| `1` | Effectively disables trajectory lines (no history to draw). |
| `50`--`100` | Shows longer movement paths. Useful for slow-moving objects or when you want to see broader movement patterns. |
| `300`+ | Very long trails. Useful for visualizing entire movement trajectories across the video, but may clutter the frame in busy scenes. |

### Implementation Details

- The `TrackPlotter` class maintains a per-track deque of center-point coordinates, limited to `trail_length` entries.
- On each frame, the plotter calls `result.plot()` to get the Ultralytics-annotated frame (bounding boxes + IDs + labels), then overlays trajectory polylines using OpenCV's `cv2.polylines()`.
- The output video uses the `mp4v` codec and matches the original video's resolution and frame rate.
- Even frames with no detections are written to the output video to keep it synchronized with the input.
- There is slightly more overhead compared to `--save-vid` due to per-frame custom rendering and polyline drawing.

---

## Comparison Table

| Feature | `--save-vid` | `--plot-tracks` |
|---------|-------------|----------------|
| Bounding boxes | Yes | Yes |
| Track IDs | Yes | Yes |
| Class labels | Yes | Yes |
| Trajectory lines | No | Yes |
| Movement history | No | Yes (controlled by `--trail-length`) |
| Output file | `tracked_video.mp4` | `tracked_trajectories.mp4` |
| Rendering engine | Ultralytics built-in | Custom (OpenCV + Ultralytics `result.plot()`) |
| Overhead | Minimal | Slightly higher (per-frame polyline rendering) |
| Codec | Ultralytics default | `mp4v` |

---

## Combining Both Modes

The two visualization modes are fully independent. You can enable both to produce two separate output videos:

```bash
python -m MOT.run --input video.mp4 --output outputs/ --save-vid --plot-tracks --trail-length 50
```

This produces:

```
outputs/
  video_name/
    tracking_results.txt
    tracking.log
    tracked_video.mp4            <-- Bounding boxes + IDs only
    tracked_trajectories.mp4     <-- Bounding boxes + IDs + trajectory lines
```

This is useful when you want a clean annotated video for presentations (`tracked_video.mp4`) alongside a trajectory visualization for analysis (`tracked_trajectories.mp4`).

---

## Examples

### Person Tracking with Trajectory Visualization

```bash
python -m MOT.run \
    --input data/pbl/ \
    --output outputs/ \
    --classes 0 \
    --plot-tracks \
    --trail-length 100
```

Tracks only persons (class 0) and visualizes their movement paths with a 100-frame trail.

### Quick Preview with Built-in Annotation

```bash
python -m MOT.run \
    --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 \
    --output outputs/ \
    --save-vid
```

Produces a quick annotated video to verify tracking is working correctly.

### Full Visualization Suite

```bash
python -m MOT.run \
    --input data/pbl/ \
    --output outputs/ \
    --model yolo26m.pt \
    --save-vid \
    --plot-tracks \
    --trail-length 60 \
    --with-reid
```

Uses a medium model with ReID for robust tracking, and generates both visualization outputs.

---

## Related Documentation

- [Tracking Configuration](tracking.md) -- Full reference for all tracking parameters.
- [Output Format](output.md) -- Detailed description of all output files.
