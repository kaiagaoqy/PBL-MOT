# Input Data Format

This guide describes the supported video formats, directory structures, and how the pipeline discovers input videos and computes output paths.

---

## Supported Video Formats

The pipeline recognizes the following video file extensions (case-insensitive):

| Extension | Format |
|-----------|--------|
| `.mp4` | MPEG-4 Part 14 |
| `.avi` | Audio Video Interleave |
| `.mov` | Apple QuickTime |
| `.mkv` | Matroska |
| `.wmv` | Windows Media Video |
| `.flv` | Flash Video |
| `.webm` | WebM |

Any file with one of these extensions will be picked up during video discovery. Files with other extensions are silently skipped.

---

## Single File vs. Directory Input

The `--input` argument accepts either a single video file or a directory.

### Single File

```bash
python -m MOT.run --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 --output outputs/
```

When a single file is provided, only that video is processed. The output is placed in a subdirectory named after the video's stem (filename without extension):

```
outputs/
  Task7_AV_Trial1~/
    tracking_results.txt
    tracking.log
```

### Directory (Recursive Discovery)

```bash
python -m MOT.run --input data/pbl/ --output outputs/
```

When a directory is provided, the pipeline recursively walks the entire directory tree, discovers all files with recognized video extensions, sorts them alphabetically, and processes them in order.

---

## Expected Directory Structure

A typical input directory follows this layout:

```
data/pbl/
  Sub140/
    Task7_AV_Trial1~.mp4
    Task7_AV_Trial2~.mp4
    Task8_AV_Trial1~.mp4
  Sub141/
    Task7_AV_Trial1~.mp4
    Task8_AV_Trial1~.mp4
  Sub142/
    Task7_AV_Trial1~.mp4
```

The naming convention is: `SubXXX/TaskX_AV_TrialX~.mp4`, where:

- `SubXXX` is a subject/participant identifier.
- `TaskX_AV_TrialX~` encodes the task number, modality, and trial number.

However, the pipeline does not enforce any particular naming convention. Any directory structure with video files at any depth will work.

---

## Output Directory Mirroring

The output directory structure mirrors the input hierarchy. Each video gets its own subdirectory named after the video's stem (filename without extension).

### Directory Input Example

Given:

```
--input  data/pbl/
--output outputs/
```

The output structure is:

```
outputs/
  class_mapping.txt
  tracking_summary.log
  Sub140/
    Task7_AV_Trial1~/
      tracking_results.txt
      tracking.log
    Task7_AV_Trial2~/
      tracking_results.txt
      tracking.log
  Sub141/
    Task7_AV_Trial1~/
      tracking_results.txt
      tracking.log
```

### Single File Input Example

Given:

```
--input  data/pbl/Sub140/Task7_AV_Trial1~.mp4
--output outputs/
```

The output structure is:

```
outputs/
  class_mapping.txt
  tracking_summary.log
  Task7_AV_Trial1~/
    tracking_results.txt
    tracking.log
```

---

## How Output Paths Are Computed

The function `compute_output_dir()` in `video_utils.py` determines the output directory for each video. The logic works as follows:

1. **Single file input**: The video's stem is used directly. The output directory is `<output_root>/<video_stem>/`.

2. **Directory input**: The relative path from the input root to the video file is computed. The directory part of that relative path is preserved, and the video's stem is appended as a final subdirectory.

### Detailed Example

```
video_path:  data/pbl/Sub140/Task7_AV_Trial1~.mp4
input_root:  data/pbl/
output_root: outputs/

Relative path:  Sub140/Task7_AV_Trial1~.mp4
Directory part: Sub140/
Video stem:     Task7_AV_Trial1~

Output dir:     outputs/Sub140/Task7_AV_Trial1~/
```

This mirroring ensures that the output directory structure is predictable and that results from different subjects or sessions never collide.

---

## Next Steps

- [Tracking Configuration](tracking.md) -- Configure models, trackers, and all tracking parameters.
- [Output Format](output.md) -- Understand the contents of each output file.
