# Troubleshooting

This guide covers common issues encountered when running the YOLO tracking pipeline, along with their causes and solutions.

---

## GPU Out of Memory (CUDA OOM)

### Symptom

```
torch.cuda.OutOfMemoryError: CUDA out of memory. Tried to allocate XXX MiB
```

or the process is killed unexpectedly.

### Causes

- The YOLO model is too large for the available GPU memory.
- The inference image size (`--imgsz`) is too high.
- Another process is occupying GPU memory.

### Solutions

1. **Use a smaller model.** Switch from `yolo26x.pt` or `yolo26l.pt` to a lighter model:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --model yolo26n.pt
   ```

2. **Reduce the inference image size.** Lower `--imgsz` from 1280 to 640 (the default):

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --imgsz 640
   ```

3. **Check GPU memory usage.** Ensure no other processes are consuming GPU memory:

   ```bash
   nvidia-smi
   ```

4. **Use CPU inference.** As a last resort, run on CPU (significantly slower):

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --device cpu
   ```

---

## No Detections in Output

### Symptom

`tracking_results.txt` is empty or contains very few lines. The log shows 0 tracks and 0 detections.

### Causes

- The confidence threshold (`--conf`) is too high.
- The `--classes` filter excludes the objects in the video.
- The objects are too small relative to the inference resolution.
- The model is not appropriate for the content.

### Solutions

1. **Lower the confidence threshold:**

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --conf 0.1
   ```

2. **Remove the class filter.** If you are using `--classes`, try running without it to track all 80 COCO classes:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/
   ```

3. **Increase the inference image size** to detect smaller objects:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --imgsz 1280
   ```

4. **Use a larger model** for better detection accuracy:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --model yolo26m.pt
   ```

5. **Verify the video** is not corrupted by opening it in a media player or checking with:

   ```bash
   ffprobe video.mp4
   ```

---

## Track ID Jumps and Fragmentation

### Symptom

The same physical object receives multiple different track IDs over the course of the video. IDs are not persistent.

### Causes

- Objects are frequently occluded or leave and re-enter the frame.
- The track buffer is too short for the duration of occlusions.
- ReID is not enabled, so the tracker cannot re-identify objects by appearance.
- The detection confidence threshold is too high, causing intermittent detections.

### Solutions

1. **Enable ReID** for better re-identification through occlusions:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --with-reid
   ```

2. **Increase the track buffer** to keep lost tracks alive longer:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --track-buffer 90
   ```

   At 30 FPS, `--track-buffer 90` keeps tracks alive for 3 seconds of absence.

3. **Lower the confidence threshold** to reduce detection gaps:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --conf 0.15
   ```

4. **Lower the track matching threshold** for stricter matching (reduces ID switches between different objects):

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --match-thresh 0.6
   ```

5. **Enable global motion compensation** if the camera is moving. The default `sparseOptFlow` should handle this, but verify it is not set to `none`:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --gmc-method sparseOptFlow
   ```

---

## Video Codec Errors

### Symptom

```
RuntimeError: Cannot open video file: /path/to/video.mp4
```

or:

```
Cannot create video writer for: /path/to/output.mp4
```

### Causes

- The video file is corrupted or uses a codec not supported by the installed OpenCV build.
- OpenCV was not compiled with FFmpeg support.
- The output directory path contains characters that the OS cannot handle.

### Solutions

1. **Check the video file** with `ffprobe`:

   ```bash
   ffprobe /path/to/video.mp4
   ```

   If this fails, the file is likely corrupted.

2. **Re-encode the video** to a widely-supported format:

   ```bash
   ffmpeg -i input.mkv -c:v libx264 -crf 23 output.mp4
   ```

3. **Verify OpenCV FFmpeg support:**

   ```bash
   python -c "import cv2; print(cv2.getBuildInformation())" | grep -i ffmpeg
   ```

   If FFmpeg is listed as `NO`, reinstall OpenCV with FFmpeg support:

   ```bash
   pip install opencv-python-headless
   ```

4. **Check output path.** Ensure the output directory path does not contain special characters that might cause issues on your filesystem.

---

## No Video Files Found

### Symptom

```
No video files found at: /path/to/directory
```

### Causes

- The input path does not exist.
- The directory contains no files with recognized video extensions (`.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm`).
- The video files have uppercase or non-standard extensions.

### Solutions

1. **Verify the input path exists:**

   ```bash
   ls /path/to/directory
   ```

2. **Check file extensions.** The pipeline recognizes extensions case-insensitively, but ensure files actually have one of the supported extensions. Files like `video.MP4` are recognized; files like `video.264` or `video.ts` are not.

3. **List the actual files in the directory:**

   ```bash
   find /path/to/directory -type f | head -20
   ```

4. **Try pointing to a specific file** to verify the pipeline works:

   ```bash
   python -m MOT.run --input /path/to/directory/specific_file.mp4 --output outputs/
   ```

---

## Slow Processing Speed

### Symptom

Processing is much slower than expected. FPS is low.

### Causes

- Running on CPU instead of GPU.
- Using a large model (`yolo26x.pt`) or high inference resolution (`--imgsz 1280`).
- Visualization options (`--save-vid`, `--plot-tracks`) add overhead.
- The GPU is throttling due to thermal limits or power constraints.

### Solutions

1. **Verify GPU is being used.** Check the device printed at startup:

   ```
   Model loaded on device: cuda:0
   ```

   If it says `cpu`, ensure CUDA is properly installed:

   ```bash
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **Use a smaller model:**

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --model yolo26n.pt
   ```

3. **Reduce inference resolution:**

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --imgsz 640
   ```

4. **Disable visualization** for pure tracking runs:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/
   ```

   (omit `--save-vid` and `--plot-tracks`)

5. **Use ByteTrack** instead of BoT-SORT for faster tracking:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --tracker bytetrack.yaml
   ```

6. **Disable ReID** if enabled, as it adds per-frame overhead:

   ```bash
   python -m MOT.run --input video.mp4 --output outputs/ --no-with-reid
   ```

---

## NumPy Version Conflict

### Symptom

```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x
```

or:

```
RuntimeError: Numpy is not available
```

or:

```
AttributeError: module 'numpy' has no attribute 'float'
```

### Cause

The installed PyTorch (or another dependency) was compiled against NumPy 1.x, but NumPy 2.x is installed.

### Solution

Downgrade NumPy to a 1.x version:

```bash
pip install "numpy<2"
```

Then verify the fix:

```bash
python -c "from ultralytics import YOLO; print('OK')"
```

---

## Ultralytics Import Error

### Symptom

```
ModuleNotFoundError: No module named 'ultralytics'
```

### Solution

Ensure you have activated the correct conda environment and installed Ultralytics:

```bash
conda activate py310
pip install ultralytics
```

---

## Annotated Video Not Found After `--save-vid`

### Symptom

The log says the video was tracked successfully, but `tracked_video.mp4` is missing from the output directory. A warning may appear:

```
Warning: Could not find annotated video for video_name
```

### Cause

The pipeline looks for the annotated video in Ultralytics' default `runs/detect/track*/` directory and moves it to the output directory. If Ultralytics changes its save path in a newer version, the file may not be found.

### Solutions

1. **Check the `runs/` directory** in the current working directory:

   ```bash
   find runs/ -name "*.avi" -o -name "*.mp4" 2>/dev/null
   ```

2. **Manually move the file** if found:

   ```bash
   mv runs/detect/track/video_name.avi outputs/video_name/tracked_video.mp4
   ```

3. **Use `--plot-tracks` instead** as an alternative visualization method. The trajectory video is saved directly to the output directory without relying on Ultralytics' save path.

---

## Getting Help

If you encounter an issue not covered here:

1. **Check the per-video log** (`tracking.log`) for detailed error messages and tracebacks.
2. **Check the batch summary** (`tracking_summary.log`) to identify which videos failed.
3. **Run with a single video** to isolate the issue:

   ```bash
   python -m MOT.run --input /path/to/problematic_video.mp4 --output debug_outputs/
   ```

---

## Related Documentation

- [Installation](installation.md) -- Setup and dependency installation.
- [Tracking Configuration](tracking.md) -- Full parameter reference.
- [Output Format](output.md) -- Understanding output files and logs.
