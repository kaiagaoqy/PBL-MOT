# 输出格式

本文档详细说明流水线生成的所有输出文件的格式、内容和用途。

---

## 目录结构

输出目录的层级结构**镜像输入目录**，每个视频的结果保存在以视频文件名（不含扩展名）命名的子目录中。

### 批量处理时的完整输出结构

```
outputs/                                # 输出根目录（--output 指定）
├── class_mapping.txt                   # [全局] COCO 类别 ID 映射
├── tracking_summary.log                # [全局] 批次处理摘要
├── tracker_config.yaml                 # [全局] 合并后的跟踪器配置（仅在使用覆盖参数时生成）
│
├── Sub140/                             # 镜像输入目录结构
│   ├── Task7_AV_Trial1~/              # 以视频文件名命名的子目录
│   │   ├── tracking_results.txt        # [必有] MOTChallenge 格式跟踪结果
│   │   ├── tracking.log                # [必有] 视频处理日志
│   │   ├── tracked_video.mp4           # [可选] --save-vid 生成
│   │   └── tracked_trajectories.mp4    # [可选] --plot-tracks 生成
│   └── Task7_AV_Trial2~/
│       ├── tracking_results.txt
│       └── tracking.log
│
└── Sub141/
    └── Task8_AV_Trial1~/
        ├── tracking_results.txt
        └── tracking.log
```

---

## tracking_results.txt — MOTChallenge 格式

### 格式说明

每行代表一个检测/跟踪结果，默认包含 10 个逗号分隔的字段。使用 `--eval-saliency` 后，会追加第 11 列显著性均值。

```
frame,id,bb_left,bb_top,bb_width,bb_height,conf,class,-1,-1[,mean_saliency]
```

### 列定义

| 列号 | 字段名 | 类型 | 说明 |
|------|--------|------|------|
| 1 | `frame` | int | 帧编号（从 1 开始） |
| 2 | `id` | int | 唯一跟踪 ID。同一目标在不同帧中保持相同 ID |
| 3 | `bb_left` | float | 边界框左上角 x 坐标（像素） |
| 4 | `bb_top` | float | 边界框左上角 y 坐标（像素） |
| 5 | `bb_width` | float | 边界框宽度（像素） |
| 6 | `bb_height` | float | 边界框高度（像素） |
| 7 | `conf` | float | 检测置信度 (0.0-1.0) |
| 8 | `class` | int | COCO 类别 ID（参见 `class_mapping.txt` 或 [COCO 类别参考](coco_classes.md)） |
| 9 | `visibility` | int | 未使用，固定为 `-1` |
| 10 | `unused` | int | 未使用，固定为 `-1` |
| 11 | `mean_saliency` | float | **（仅 `--eval-saliency` 时）** 边界框内的 Itti 显著性均值 (0.0-1.0)。值越高表示该区域越显眼。 |

### 坐标系

- **原点**：图像左上角 (0, 0)
- **x 轴**：从左到右递增
- **y 轴**：从上到下递增
- **坐标单位**：像素，对应原始视频分辨率（非推理尺寸）
- **坐标精度**：保留 1 位小数
- **置信度精度**：保留 2 位小数

### 示例

默认（10 列）：
```
1,1,512.3,284.1,45.6,123.8,0.89,0,-1,-1
1,2,1024.7,301.5,38.2,98.4,0.76,0,-1,-1
2,1,515.1,285.3,44.9,122.7,0.91,0,-1,-1
```

使用 `--eval-saliency` 后（追加第 11 列）：
```
1,1,512.3,284.1,45.6,123.8,0.89,0,-1,-1,0.2065
1,2,1024.7,301.5,38.2,98.4,0.76,0,-1,-1,0.3150
2,1,515.1,285.3,44.9,122.7,0.91,0,-1,-1,0.2235
```

**解读**：
- 第 1 帧有 3 个目标：ID 1 和 ID 2 是人物（class=0），ID 3 是汽车（class=2）
- 第 2 帧同样 3 个目标保持了相同的 ID，表示身份跟踪成功
- 没有检测结果的帧不会出现在文件中

### 注意事项

- 帧编号从 **1** 开始（非 0）
- 没有被跟踪到目标的帧会被省略（这是 MOTChallenge 标准行为）
- 坐标已映射回**原始视频分辨率**，与 `--imgsz` 推理尺寸无关
- 边界框格式为 `(left, top, width, height)`，非 `(x1, y1, x2, y2)`

---

## tracking.log — 视频处理日志

每个视频（无论成功或失败）都会生成一个日志文件，记录处理的详细信息。

### 成功时的内容

```
==================================================
Tracking Log: Task7_AV_Trial1~.mp4
==================================================
Date:       2026-04-06 15:30:42
Model:      yolo26n.pt
Tracker:    botsort.yaml
Confidence: 0.25 | IoU: 0.7 | imgsz: 640
Device:     auto

Video Info:
  Path:       /path/to/Task7_AV_Trial1~.mp4
  Resolution: 1920x1080
  Frames:     5400
  FPS:        30.0
  Duration:   180.0s

Results:
  Status:      SUCCESS
  Tracks:      12
  Detections:  48350
  Time:        95.3s
  Process FPS: 56.7
  Output:      tracking_results.txt
==================================================

Saliency Evaluation:
  Status:      SUCCESS
  Frames:      103
  Detections:  198
  Time:        11.1s
==================================================
```

"Saliency Evaluation" 部分仅在使用 `--eval-saliency` 时追加。

### 失败时的内容

```
==================================================
Tracking Log: corrupted_video.mp4
==================================================
Date:       2026-04-06 15:35:10
Model:      yolo26n.pt
Tracker:    botsort.yaml
Confidence: 0.25 | IoU: 0.7 | imgsz: 640
Device:     auto

Video Info:
  Path:       /path/to/corrupted_video.mp4

Results:
  Status:      FAILED
  Error:       Cannot open video file: /path/to/corrupted_video.mp4
  Traceback:
    Traceback (most recent call last):
      File "...", line ..., in process_video
        ...
    RuntimeError: Cannot open video file: /path/to/corrupted_video.mp4
==================================================
```

---

## class_mapping.txt — COCO 类别映射

此文件在输出根目录下生成一次，记录 YOLO 模型使用的 COCO 类别 ID 到名称的映射关系。用于解读 `tracking_results.txt` 中第 8 列（class）的含义。

### 格式

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

> **提示**：完整的 COCO 类别列表请参见 [COCO 类别参考](coco_classes.md)。

---

## tracking_summary.log — 批次处理摘要

在输出根目录下生成，汇总所有视频的处理结果。

### 格式

```
==================================================
YOLO Tracking Run Summary
==================================================
Date:  2026-04-06 15:45:00
Model: yolo26n.pt | Tracker: botsort.yaml
Conf:  0.25 | IoU: 0.7 | imgsz: 640
Input: data/pbl/

--------------------------------------------------
[1/5] Task7_AV_Trial1~ -- SUCCESS -- 5400 frames, 12 tracks, 95.3s
[2/5] Task7_AV_Trial2~ -- SUCCESS -- 3200 frames, 8 tracks, 55.1s
[3/5] Task8_AV_Trial1~ -- SUCCESS -- 7200 frames, 15 tracks, 128.7s
[4/5] corrupted_video -- FAILED -- Cannot open video file: ...
[5/5] Task8_AV_Trial2~ -- SUCCESS -- 4800 frames, 10 tracks, 82.4s
--------------------------------------------------
Totals: 5 videos (4 success, 1 failed) | 20600 frames | 361.5s
==================================================
```

---

## tracked_video.mp4 — 标注视频

仅在使用 `--save-vid` 参数时生成。

- **内容**：每帧叠加边界框、跟踪 ID 和类别标签
- **渲染引擎**：Ultralytics 内置
- **位置**：`<video_output_dir>/tracked_video.mp4`

---

## tracked_trajectories.mp4 — 轨迹视频

仅在使用 `--plot-tracks` 参数时生成。

- **内容**：每帧叠加边界框、跟踪 ID、类别标签以及轨迹线
- **渲染引擎**：自定义 OpenCV 渲染
- **编码格式**：mp4v
- **位置**：`<video_output_dir>/tracked_trajectories.mp4`

---

## tracker_config.yaml — 跟踪器配置

仅在通过命令行覆盖跟踪器参数时生成（参见 [跟踪配置 - 命令行跟踪器覆盖](tracking.md#命令行跟踪器覆盖)）。

- **内容**：基础 YAML 配置与命令行覆盖参数合并后的完整配置
- **用途**：确保实验可复现。将此文件传给 `--tracker` 即可精确重现相同配置
- **位置**：`outputs/tracker_config.yaml`

### 示例

```yaml
tracker_type: botsort
track_high_thresh: 0.25
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

---

[返回概述](README.md) | [上一步：可视化选项](visualization.md) | [下一步：COCO 类别参考](coco_classes.md)
