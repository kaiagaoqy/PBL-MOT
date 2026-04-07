# Tracking Configuration

This is the primary reference for all tracking parameters, model options, tracker algorithms, and configuration methods. It covers the full CLI interface, model selection, tracker selection, YAML configuration, CLI overrides, custom configs, and ReID.

---

## CLI Arguments

The complete set of command-line arguments accepted by `python -m MOT.run`.

### Core Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--input` | `str` | **(required)** | Path to a single video file or a directory tree containing videos. When a directory is given, all videos are discovered recursively. |
| `--output` | `str` | `outputs` | Output root directory. The directory structure mirrors the input hierarchy, with each video getting its own subdirectory. |
| `--model` | `str` | `yolo26n.pt` | Ultralytics YOLO model name or path. Accepted values include any YOLO model identifier (e.g., `yolo26n.pt`, `yolo26s.pt`, `yolo26m.pt`, `yolo26l.pt`, `yolo26x.pt`) or a path to a custom-trained `.pt` file. Models are auto-downloaded on first use. |
| `--tracker` | `str` | `botsort.yaml` | Tracker configuration. Accepted values: `botsort.yaml` (BoT-SORT), `bytetrack.yaml` (ByteTrack), or a full path to a custom YAML config file. |
| `--conf` | `float` | `0.25` | Detection confidence threshold (0.0--1.0). Detections with confidence below this value are discarded before tracking. Lower values detect more objects but increase false positives. |
| `--iou` | `float` | `0.7` | IoU (Intersection over Union) threshold (0.0--1.0) used for non-maximum suppression (NMS) and tracker association. Higher values require more overlap to suppress duplicate detections. |
| `--device` | `str` | `""` (auto) | Device for inference. Examples: `""` (auto-detect GPU/CPU), `"cpu"`, `"0"` (GPU 0), `"cuda:0"`, `"cuda:1"`. When left empty, the pipeline auto-selects the best available device. |
| `--classes` | `int` (one or more) | `None` (all) | Filter detections by COCO class ID. Accepts one or more space-separated integers. Examples: `--classes 0` (person only), `--classes 0 2 7` (person + car + truck). When not specified, all 80 COCO classes are tracked. See [COCO Class Reference](coco_classes.md) for the full list. |
| `--imgsz` | `int` | `640` | Inference image size in pixels. The longer side of each frame is scaled to this value; aspect ratio is preserved with letterbox padding. Output coordinates are mapped back to the original resolution. Larger values improve detection accuracy (especially for small objects) but reduce speed and increase GPU memory usage. Common values: 640, 1280. |
| `--eval-saliency` | flag | `False` | After tracking completes, compute the mean Itti saliency for each bounding box and append it as column 11 to `tracking_results.txt`. The YOLO model is freed before saliency computation to avoid GPU memory conflicts. See [Saliency Evaluation](#saliency-evaluation) for details. |

### Visualization Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--save-vid` | flag | `False` | Save an annotated video with bounding boxes and track IDs using Ultralytics built-in rendering. Output: `tracked_video.mp4` in the per-video output directory. Does not include trajectory lines. |
| `--plot-tracks` | flag | `False` | Save a video with bounding boxes, track IDs, and trajectory lines showing each object's movement path over time. Output: `tracked_trajectories.mp4` in the per-video output directory. Can be combined with `--save-vid`. |
| `--trail-length` | `int` | `30` | Number of past frames to include in trajectory lines for each tracked object. Only used when `--plot-tracks` is enabled. Higher values draw longer trajectory tails; lower values show only recent movement. |

### Tracker Parameter Overrides

These arguments override individual parameters in the tracker YAML config file. They are optional; when omitted, the value from the base config file is used. See the [Tracker YAML Configuration](#tracker-yaml-configuration) section for detailed descriptions of each parameter.

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--with-reid` / `--no-with-reid` | `bool` | *(tracker config)* | Enable or disable Re-Identification. Uses `BooleanOptionalAction`, so `--with-reid` enables it and `--no-with-reid` explicitly disables it. Only effective with BoT-SORT. |
| `--track-high-thresh` | `float` | *(tracker config)* | First association confidence threshold. |
| `--track-low-thresh` | `float` | *(tracker config)* | Second association threshold (more lenient). |
| `--new-track-thresh` | `float` | *(tracker config)* | Minimum confidence to initialize a new track. |
| `--track-buffer` | `int` | *(tracker config)* | Frames to keep lost tracks alive before deletion. |
| `--match-thresh` | `float` | *(tracker config)* | Track matching threshold. |
| `--proximity-thresh` | `float` | *(tracker config)* | Minimum IoU for valid ReID match (ReID only). |
| `--appearance-thresh` | `float` | *(tracker config)* | Minimum appearance similarity for ReID (ReID only). |
| `--gmc-method` | `str` | *(tracker config)* | Global motion compensation method. Choices: `orb`, `sift`, `ecc`, `sparseOptFlow`, `none`. |

---

## Model Selection

The `--model` argument selects the YOLO model used for object detection. Larger models are more accurate but slower and require more GPU memory.

| Model | Parameters | Speed | Accuracy | Recommended Use Case |
|-------|-----------|-------|----------|---------------------|
| `yolo26n.pt` | ~2.7M | Fastest | Lowest | Quick experiments, real-time applications, low-resource devices |
| `yolo26s.pt` | ~9.5M | Fast | Good | Balanced speed/accuracy for development and testing |
| `yolo26m.pt` | ~22M | Moderate | Better | Production use when GPU is available |
| `yolo26l.pt` | ~50M | Slower | High | High-accuracy applications with adequate GPU |
| `yolo26x.pt` | ~97M | Slowest | Highest | Maximum accuracy when processing time is not critical |

### Recommendations

- **For initial testing and development**, start with `yolo26n.pt` (the default). It provides fast iteration.
- **For production or evaluation**, use `yolo26m.pt` or `yolo26l.pt` for a good accuracy/speed tradeoff.
- **For maximum accuracy** on benchmarks or when tracking small/distant objects, use `yolo26x.pt` and consider increasing `--imgsz` to 1280.
- **All models auto-download** on first use. No manual download is needed.

### Custom Models

You can also pass a path to a custom-trained YOLO model:

```bash
python -m MOT.run --input video.mp4 --output outputs/ --model /path/to/custom_model.pt
```

---

## Tracker Selection

The `--tracker` argument selects the tracking algorithm. Two built-in options are available.

### BoT-SORT (Default)

```bash
python -m MOT.run --input video.mp4 --output outputs/ --tracker botsort.yaml
```

- **Algorithm**: BoT-SORT (Bag of Tricks for SORT).
- **Strengths**: Supports Re-Identification (ReID) for better track persistence through occlusions. Includes global motion compensation (GMC) to handle camera movement. Best for crowded scenes with frequent occlusions.
- **When to use**: Default choice for most scenarios. Especially recommended when objects frequently overlap, disappear behind obstacles, or when the camera is moving.

### ByteTrack

```bash
python -m MOT.run --input video.mp4 --output outputs/ --tracker bytetrack.yaml
```

- **Algorithm**: ByteTrack.
- **Strengths**: Simpler and faster. No ReID overhead. Good for scenes with clear visibility and minimal occlusion.
- **When to use**: When processing speed is the priority and the scene has relatively uncluttered objects with minimal occlusion. Also useful as a baseline for comparison.

### Comparison

| Feature | BoT-SORT | ByteTrack |
|---------|----------|-----------|
| Re-Identification (ReID) | Supported (optional) | Not supported |
| Global Motion Compensation | Yes | No |
| Occlusion handling | Better (especially with ReID) | Basic |
| Speed | Moderate | Faster |
| Complexity | Higher | Lower |
| Best for | Crowded/occluded scenes, moving camera | Clear scenes, static camera |

---

## Tracker YAML Configuration

The `--tracker` argument accepts one of three values:

1. `"botsort.yaml"` -- Built-in BoT-SORT config (ships with Ultralytics).
2. `"bytetrack.yaml"` -- Built-in ByteTrack config (ships with Ultralytics).
3. A full path to a custom YAML file (e.g., `/path/to/my_tracker.yaml`).

The YAML file contains all tracker parameters. Below is the complete parameter reference.

### Complete Parameter Reference

| Parameter | Type | Default (BoT-SORT) | Description |
|-----------|------|---------------------|-------------|
| `tracker_type` | `str` | `botsort` | The tracking algorithm to use. Valid values: `"botsort"` or `"bytetrack"`. This determines which tracker implementation is instantiated. |
| `track_high_thresh` | `float` | `0.25` | **First association threshold.** Detections with confidence above this value are matched to existing tracks in the first round of association. If a detection's confidence falls below this threshold, the tracker will not use it to update an existing high-confidence track. This is the primary knob for controlling detection quality in tracking. |
| `track_low_thresh` | `float` | `0.1` | **Second association threshold (more lenient).** After the first round of association, detections with confidence between `track_low_thresh` and `track_high_thresh` get a second chance to be matched to unmatched tracks. This helps catch objects that are partially occluded or at unusual angles, where the detector is less confident. |
| `new_track_thresh` | `float` | `0.25` | **Minimum confidence to initialize a new track.** When a detection is not matched to any existing track, a new track is only created if the detection confidence exceeds this threshold. Setting this higher reduces spurious tracks from false positives; setting it lower allows the tracker to pick up objects sooner. |
| `track_buffer` | `int` | `30` | **Frames to keep lost tracks alive before deletion.** When a tracked object is no longer detected (e.g., it is occluded or leaves the frame), the tracker keeps its state alive for this many frames. If the object reappears within this window, it retains its original ID. Higher values provide more tolerance for temporary occlusion but also increase the risk of ID reassignment to a different object. At 30 FPS video, the default of 30 means a 1-second buffer. |
| `match_thresh` | `float` | `0.8` | **Track matching threshold.** Controls the maximum allowed distance (cost) for a detection-to-track assignment to be considered valid. Higher values make matching more lenient (accepting weaker matches), while lower values enforce stricter matching. |
| `fuse_score` | `bool` | `true` | **Fuse confidence scores with IoU distances before matching.** When enabled, the detection confidence score is incorporated into the association cost matrix, giving higher-confidence detections a slight advantage during matching. Generally improves tracking stability. |
| `gmc_method` | `str` | `sparseOptFlow` | **Global motion compensation method.** Compensates for camera movement so that bounding box positions from the previous frame can be accurately compared to the current frame. Available methods: `"sparseOptFlow"` (Lucas-Kanade optical flow, default and recommended), `"orb"` (ORB feature matching), `"sift"` (SIFT feature matching), `"ecc"` (Enhanced Correlation Coefficient, slow but accurate), `"none"` (disable GMC). Use `"none"` for static cameras. |
| `proximity_thresh` | `float` | `0.5` | **Minimum IoU required for a valid ReID match.** Even when appearance features suggest a match, the matched detection and track must have at least this much spatial overlap (IoU). This prevents the ReID module from incorrectly associating objects that look similar but are far apart in the frame. Only used when `with_reid` is `true`. |
| `appearance_thresh` | `float` | `0.8` | **Minimum appearance similarity for ReID.** The cosine similarity between the appearance embeddings of a detection and a lost track must exceed this value for a ReID match to be considered. Higher values require stronger visual similarity. Only used when `with_reid` is `true`. |
| `with_reid` | `bool` | `false` | **Enable Re-Identification.** When enabled, the tracker extracts appearance features (embeddings) for each detected object and uses them to re-identify objects after occlusion. This significantly improves track persistence in crowded scenes but adds computational overhead. See the [ReID](#reid-re-identification) section for details. |
| `model` | `str` | `auto` | **ReID model selection.** When `with_reid` is `true`, this specifies which model to use for appearance feature extraction. `"auto"` uses the native YOLO feature extraction with minimal overhead. Alternatively, specify an explicit classification model like `"yolo26n-cls.pt"` for dedicated appearance embeddings. Only relevant when `with_reid` is `true`. |

---

## CLI Tracker Overrides

Common tracker parameters can be overridden directly from the command line without editing a YAML file. This is the fastest way to experiment with different settings.

### How It Works

When you pass any tracker override argument (e.g., `--track-buffer 60`), the pipeline:

1. Loads the base tracker config (specified by `--tracker`).
2. Merges your CLI overrides into the loaded config, replacing the corresponding values.
3. Writes the merged config as `tracker_config.yaml` in the output root directory.
4. Passes the merged config to the YOLO tracker.

This ensures full reproducibility -- you can always check `tracker_config.yaml` to see the exact parameters that were used.

### Example

```bash
python -m MOT.run \
    --input video.mp4 \
    --output outputs/ \
    --with-reid \
    --track-buffer 60 \
    --track-high-thresh 0.5
```

This starts from the default `botsort.yaml`, enables ReID, sets the track buffer to 60 frames, and raises the high confidence threshold to 0.5. The merged config is saved to `outputs/tracker_config.yaml`.

### Available CLI Overrides

| CLI Flag | Tracker YAML Key | Type |
|----------|-----------------|------|
| `--with-reid` / `--no-with-reid` | `with_reid` | `bool` |
| `--track-high-thresh` | `track_high_thresh` | `float` |
| `--track-low-thresh` | `track_low_thresh` | `float` |
| `--new-track-thresh` | `new_track_thresh` | `float` |
| `--track-buffer` | `track_buffer` | `int` |
| `--match-thresh` | `match_thresh` | `float` |
| `--proximity-thresh` | `proximity_thresh` | `float` |
| `--appearance-thresh` | `appearance_thresh` | `float` |
| `--gmc-method` | `gmc_method` | `str` |

### Without Overrides

When no tracker override arguments are provided, the base config file is used directly and no `tracker_config.yaml` is written. The tracker config path is printed to the console either way, so you always know which config was used.

---

## Custom Tracker Configuration

For full control, you can create a custom YAML config file and pass it directly.

### Step 1: Obtain the Default Config

There are two ways to get a starting point:

**Option A**: Run the pipeline once with an override, then inspect the saved config:

```bash
python -m MOT.run --input video.mp4 --output outputs/ --track-buffer 30
# Now inspect the merged config:
cat outputs/tracker_config.yaml
```

**Option B**: Copy the built-in config from the Ultralytics package:

```bash
# Find the Ultralytics config directory
python -c "import ultralytics; import os; print(os.path.join(os.path.dirname(ultralytics.__file__), 'cfg', 'trackers'))"
# Copy the desired config
cp /path/to/ultralytics/cfg/trackers/botsort.yaml ./my_tracker.yaml
```

### Step 2: Edit the Parameters

Open the YAML file in a text editor and adjust the parameters as needed. For example:

```yaml
tracker_type: botsort
track_high_thresh: 0.4
track_low_thresh: 0.1
new_track_thresh: 0.4
track_buffer: 60
match_thresh: 0.75
fuse_score: true
gmc_method: sparseOptFlow
proximity_thresh: 0.5
appearance_thresh: 0.7
with_reid: true
model: auto
```

### Step 3: Use the Custom Config

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --tracker /path/to/my_tracker.yaml
```

Note: When using a custom YAML file, you can still apply CLI overrides on top of it. The overrides are merged into the custom config just as they would be with a built-in config.

---

## ReID (Re-Identification)

### What It Does

Re-Identification (ReID) uses appearance features -- visual embeddings extracted from each detected object -- to re-identify objects after they have been lost due to occlusion or temporary absence from the frame.

Without ReID, the tracker relies solely on motion prediction (Kalman filter) and spatial overlap (IoU) to maintain track identity. When an object disappears behind another object and reappears, the tracker may assign it a new ID.

With ReID enabled, the tracker compares the appearance of a newly detected object against the stored embeddings of recently lost tracks. If the appearance is sufficiently similar (above `appearance_thresh`) and the spatial location is plausible (above `proximity_thresh`), the object is re-identified and retains its original track ID.

### When to Enable ReID

- **Crowded scenes** where objects frequently overlap and occlude each other.
- **Frequent occlusions** where objects disappear behind obstacles and reappear.
- **Scenarios where ID persistence is critical** -- for example, when downstream analysis depends on tracking specific individuals across the entire video.
- **Moving camera** where objects may temporarily leave and re-enter the field of view.

### When to Skip ReID

- **Clear, uncrowded scenes** with minimal occlusion.
- **When processing speed is the top priority** -- ReID adds latency.
- **When using ByteTrack** -- ReID is only supported by BoT-SORT.

### Performance Impact

- On first use with `--with-reid`, the ReID model (`yolo26n-cls.pt` or the configured model) is automatically downloaded.
- ReID adds per-frame latency for feature extraction. The exact overhead depends on the number of detected objects per frame and the ReID model size.
- Using `model: auto` in the tracker config leverages the native YOLO features with minimal additional overhead.

### How to Enable ReID

**Via CLI flag:**

```bash
python -m MOT.run --input video.mp4 --output outputs/ --with-reid
```

**Via YAML config:**

```yaml
with_reid: true
model: auto
```

### ReID Model Options

| Value | Description |
|-------|-------------|
| `auto` | Uses native YOLO features for appearance matching. Minimal overhead since no separate model is loaded. Recommended starting point. |
| `yolo26n-cls.pt` | Dedicated YOLO classification model for appearance embeddings. Provides stronger appearance features at the cost of additional computation. Auto-downloaded on first use. |
| Custom path | Path to any compatible classification model (e.g., a fine-tuned ReID model). |

---

## Putting It All Together

### Example: Full-Featured Run

```bash
python -m MOT.run \
    --input data/pbl/ \
    --output outputs/ \
    --model yolo26l.pt \
    --tracker botsort.yaml \
    --conf 0.3 \
    --iou 0.7 \
    --imgsz 1280 \
    --classes 0 \
    --with-reid \
    --track-buffer 60 \
    --save-vid \
    --plot-tracks \
    --trail-length 50
```

This command:

1. Uses `yolo26l.pt` for high-accuracy detection.
2. Uses BoT-SORT with ReID enabled and a 60-frame track buffer.
3. Tracks only persons (class 0) at 1280px inference resolution.
4. Requires detection confidence of at least 0.3.
5. Produces both annotated video and trajectory visualization with 50-frame trails.

---

## Saliency Evaluation

### Overview

The pipeline can optionally compute **Itti saliency** scores for each tracked bounding box. The Itti model is a classical computational model of visual attention that combines color, intensity, and orientation feature channels to produce a saliency map highlighting visually conspicuous regions. The implementation is GPU-accelerated via PyTorch.

When enabled, a mean saliency value (0.0--1.0) is computed for each bounding box and appended as **column 11** in `tracking_results.txt`.

### Integrated Mode (Recommended)

Add `--eval-saliency` to your normal tracking command:

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --eval-saliency
```

The pipeline will:

1. Run tracking for all videos as usual.
2. Free the YOLO model from GPU memory.
3. Compute Itti saliency for every frame of every tracked video.
4. For each bounding box, extract the mean saliency from the saliency map.
5. Append the mean saliency as column 11 to `tracking_results.txt`.
6. Log saliency evaluation results in `tracking.log`.

### Standalone Mode

If you have already completed tracking and want to run (or re-run) saliency evaluation independently:

```bash
python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/
```

This is useful when you want to re-compute saliency without re-running tracking.

#### Standalone CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--video-root` | `str` | **(required)** | Root directory containing the original video files (same as `--input` during tracking). |
| `--results-root` | `str` | **(required)** | Root directory containing tracking outputs (same as `--output` during tracking). |
| `--workers` | `int` | `0` | Number of worker processes. `0` = auto-detect (uses all available GPUs). |

### How It Works

For each video with a `tracking_results.txt`:

1. The video is read frame by frame.
2. For each frame, the Itti saliency model computes a full-resolution saliency map on the GPU.
3. For each bounding box in that frame, the mean saliency value within the box region is extracted.
4. The saliency map is discarded immediately (memory efficient).
5. After all frames are processed, column 11 is appended to every line in `tracking_results.txt`.

### Performance

- **Speed**: ~107 ms per frame at 1920x1080 resolution on GPU.
- **GPU acceleration**: All saliency computation runs on GPU via PyTorch.
- **Multi-GPU**: When multiple GPUs are available, videos are distributed across GPUs using the same round-robin strategy as tracking.
- **Memory**: Saliency maps are computed and consumed per-frame; no full-video buffers are held in memory. In integrated mode, the YOLO model is freed before saliency computation begins, so GPU memory is not contested.

### Output

When saliency evaluation completes, `tracking.log` includes an additional section:

```
Saliency Evaluation:
  Status:      SUCCESS
  Frames:      103
  Detections:  198
  Time:        11.1s
```

See [Output Format](output.md) for the updated `tracking_results.txt` column specification.

---

## Related Documentation

- [Visualization Options](visualization.md) -- Details on `--save-vid`, `--plot-tracks`, and `--trail-length`.
- [Output Format](output.md) -- What each output file contains.
- [COCO Class Reference](coco_classes.md) -- Full list of class IDs for the `--classes` argument.
- [Troubleshooting](troubleshooting.md) -- Common issues and solutions.
