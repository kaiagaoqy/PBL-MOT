# YOLO 多目标跟踪流水线

## 概述

本项目是基于 [Ultralytics YOLO](https://docs.ultralytics.com/) 的**多目标跟踪 (Multi-Object Tracking, MOT) 流水线**。它利用 YOLO 的 `model.track()` API，实现对视频中所有目标的检测与跟踪，并为每个目标分配跨帧持久化的唯一 ID。

### 核心特性

- **跨帧持久化 ID**：使用 BoT-SORT 或 ByteTrack 跟踪算法，在视频帧之间保持目标身份的一致性
- **MOTChallenge 标准格式输出**：跟踪结果以通用的 10 列 MOTChallenge 格式保存，便于后续分析和评估
- **灵活的可视化选项**：支持 Ultralytics 内置标注视频 (`--save-vid`) 和自定义轨迹可视化 (`--plot-tracks`)
- **批量处理**：支持单个视频文件或整个目录树的递归处理
- **输出结构镜像输入**：自动保持输入目录结构，便于组织管理
- **可复现的配置管理**：命令行覆盖参数自动保存为 YAML 文件

### 与相关项目的关系

本流水线使用的跟踪器算法源自学术领域的先进研究：

- **BoT-SORT**：默认跟踪器，在 MOT17/MOT20 基准上表现优异。支持 ReID（重识别）特征，适合拥挤和遮挡场景。相关项目：[BoostTrack](https://github.com/vbalogh-ultralytics/BoostTrack)
- **ByteTrack**：更轻量的跟踪器，适合清晰场景。相关项目：[TrackTrack (CVPR 2025)](https://github.com/SysCV/TrackTrack)

Ultralytics 已将这些算法集成到其统一的 `model.track()` API 中，本流水线在此基础上进一步封装，提供批量处理、日志记录和自定义可视化功能。

---

## 快速开始

### 1. 激活环境

```bash
conda activate py310
```

### 2. 运行跟踪

```bash
python -m MOT.run --input data/pbl/ --output outputs/
```

这将递归扫描 `data/pbl/` 目录下的所有视频文件，对每个视频执行目标跟踪，并将结果保存到 `outputs/` 目录。

### 3. 更多示例

```bash
# 处理单个视频
python -m MOT.run --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 --output outputs/

# 使用更大的模型 + 生成标注视频
python -m MOT.run --input data/pbl/ --output outputs/ --save-vid --model yolo26x.pt

# 生成轨迹可视化
python -m MOT.run --input data/pbl/ --output outputs/ --plot-tracks --trail-length 50

# 仅跟踪人物 + 启用 ReID
python -m MOT.run --input data/pbl/ --output outputs/ --with-reid --classes 0
```

---

## 输出文件说明

每个视频处理后会生成以下文件：

| 文件 | 说明 |
|------|------|
| `tracking_results.txt` | MOTChallenge 格式的跟踪结果（每行一个检测） |
| `tracking.log` | 单个视频的跟踪日志（配置、视频信息、运行结果） |
| `tracked_video.mp4` | Ultralytics 内置标注视频（仅在使用 `--save-vid` 时生成） |
| `tracked_trajectories.mp4` | 轨迹可视化视频（仅在使用 `--plot-tracks` 时生成） |

在输出根目录下还会生成：

| 文件 | 说明 |
|------|------|
| `class_mapping.txt` | COCO 类别 ID 到类别名称的映射表 |
| `tracking_summary.log` | 所有视频的批次处理摘要 |
| `tracker_config.yaml` | 合并后的跟踪器配置（仅在使用命令行覆盖参数时生成） |

---

## 文档目录

| 文档 | 说明 |
|------|------|
| [安装指南](installation.md) | 环境配置与依赖安装 |
| [输入数据格式](dataset.md) | 支持的视频格式、目录结构、输入方式 |
| [跟踪配置](tracking.md) | 命令行参数、模型选择、跟踪器配置、ReID 详解 |
| [可视化选项](visualization.md) | `--save-vid` 与 `--plot-tracks` 的对比与使用 |
| [输出格式](output.md) | MOTChallenge 格式详解、日志文件、目录结构 |
| [COCO 类别参考](coco_classes.md) | 全部 80 个 COCO 类别 ID 与名称对照表 |
| [常见问题](troubleshooting.md) | 常见错误与解决方案 |
