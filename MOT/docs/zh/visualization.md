# 可视化选项

本流水线提供两种独立的可视化方式，可以单独使用或同时启用。两者各有侧重，适用于不同的分析需求。

---

## --save-vid：Ultralytics 内置标注

### 概述

`--save-vid` 使用 Ultralytics 内部的渲染引擎（即 `model.track()` 的 `save=True` 参数），在每帧上绘制标准的目标检测标注。

### 渲染内容

- **边界框 (Bounding Box)**：每个检测到的目标周围绘制矩形框
- **跟踪 ID**：每个目标的唯一标识编号
- **类别标签**：目标的类别名称（如 "person"、"car"）
- **置信度分数**：检测的置信度百分比

### 输出文件

```
<video_output_dir>/tracked_video.mp4
```

### 使用方式

```bash
python -m MOT.run --input video.mp4 --output outputs/ --save-vid
```

### 特点

- 由 Ultralytics 官方渲染，风格与 YOLO 官方演示一致
- 不显示目标的运动历史或轨迹
- 每帧仅显示当前检测结果

### 注意事项

Ultralytics 会先将标注视频保存到其内部的 `runs/detect/track*/` 目录，流水线随后会自动将其移动到正确的输出目录并重命名为 `tracked_video.mp4`。

---

## --plot-tracks：轨迹可视化

### 概述

`--plot-tracks` 使用自定义渲染逻辑（基于 OpenCV），在 Ultralytics 标注的基础上叠加轨迹线，显示每个目标的运动路径。

### 渲染内容

- **边界框 (Bounding Box)**：每个检测到的目标周围绘制矩形框
- **跟踪 ID**：每个目标的唯一标识编号
- **类别标签**：目标的类别名称
- **轨迹线 (Trajectory Line)**：每个被跟踪目标的运动路径折线，显示其过去若干帧的位置
- **颜色编码**：每个跟踪 ID 分配独立的颜色，轨迹线与对应目标使用相同颜色，便于视觉区分

### 输出文件

```
<video_output_dir>/tracked_trajectories.mp4
```

### 使用方式

```bash
# 使用默认轨迹长度（30 帧）
python -m MOT.run --input video.mp4 --output outputs/ --plot-tracks

# 自定义轨迹长度（显示过去 50 帧的运动路径）
python -m MOT.run --input video.mp4 --output outputs/ --plot-tracks --trail-length 50
```

### --trail-length 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--trail-length` | `30` | 控制轨迹线显示的过去帧数。值越大，显示的运动历史越长 |

**选择建议**：

- **短轨迹 (10-20)**：适合目标密集场景，避免轨迹线相互重叠
- **中等轨迹 (30-50)**：适合大多数场景，能清晰展示运动趋势
- **长轨迹 (100+)**：适合需要查看完整运动路径的分析场景

### 工作原理

1. 每帧使用 Ultralytics 的 `result.plot()` 获取标注后的帧（边界框 + ID + 标签）
2. 记录每个跟踪 ID 的中心点位置历史（使用固定长度队列）
3. 在标注帧上叠加绘制每个目标的轨迹折线
4. 轨迹线使用 16 色调色板中的颜色，根据跟踪 ID 分配
5. 将合成帧写入输出视频

---

## 功能对比表

| 功能 | `--save-vid` | `--plot-tracks` |
|------|:------------:|:---------------:|
| 边界框 | 是 | 是 |
| 跟踪 ID | 是 | 是 |
| 类别标签 | 是 | 是 |
| 置信度分数 | 是 | 是 |
| 轨迹线 | **否** | **是** |
| 运动历史 | **否** | **是** (`--trail-length`) |
| 渲染引擎 | Ultralytics 内置 | 自定义 (OpenCV) |
| 输出文件名 | `tracked_video.mp4` | `tracked_trajectories.mp4` |
| 可组合使用 | 是 | 是 |

---

## 同时使用两种可视化

两种可视化方式可以**同时启用**，各自生成独立的输出文件：

```bash
python -m MOT.run --input video.mp4 --output outputs/ --save-vid --plot-tracks --trail-length 50
```

此命令将在视频输出目录下生成两个文件：

```
<video_output_dir>/
├── tracked_video.mp4          # Ultralytics 标注视频
└── tracked_trajectories.mp4   # 轨迹可视化视频
```

---

## 使用场景建议

| 场景 | 推荐选项 | 原因 |
|------|----------|------|
| 快速检查跟踪是否正常 | `--save-vid` | 简单直观，查看每帧的检测和 ID |
| 分析目标运动模式 | `--plot-tracks` | 轨迹线清晰展示运动方向和路径 |
| 调试 ID 切换问题 | `--plot-tracks --trail-length 100` | 长轨迹帮助观察 ID 是否在特定位置发生切换 |
| 论文/报告中的图示 | `--save-vid` + `--plot-tracks` | 两种视角的对比展示 |
| 大批量处理 | 不使用可视化 | 节省磁盘空间和处理时间 |

---

## 注意事项

1. **磁盘空间**：可视化视频会占用较多磁盘空间，尤其是高分辨率或长时间的视频。批量处理时请注意磁盘容量
2. **处理速度**：启用可视化会略微降低处理速度，因为需要额外的帧渲染和视频编码
3. **视频编码**：轨迹视频使用 `mp4v` 编码器。如果播放器不支持，可以使用 FFmpeg 转码：
   ```bash
   ffmpeg -i tracked_trajectories.mp4 -c:v libx264 output.mp4
   ```

---

[返回概述](README.md) | [上一步：跟踪配置](tracking.md) | [下一步：输出格式](output.md)
