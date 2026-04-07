# 跟踪配置

本文档是流水线最核心的配置参考，涵盖所有命令行参数、模型选择、跟踪器算法、YAML 配置参数、命令行覆盖机制以及 ReID（重识别）功能的详细说明。

---

## 命令行参数

### 完整参数表

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--input` | str | **必填** | 输入路径。可以是单个视频文件或包含视频的目录（递归扫描） |
| `--output` | str | `outputs` | 输出根目录。输出结构镜像输入结构 |
| `--model` | str | `yolo26n.pt` | YOLO 模型名称或路径。首次使用时自动下载 |
| `--tracker` | str | `botsort.yaml` | 跟踪器配置。可选 `botsort.yaml`、`bytetrack.yaml` 或自定义 YAML 路径 |
| `--conf` | float | `0.25` | 检测置信度阈值 (0.0-1.0)。低于此值的检测将被丢弃 |
| `--iou` | float | `0.7` | IoU 阈值 (0.0-1.0)，用于非极大值抑制 (NMS) 和跟踪器关联 |
| `--device` | str | `""`（自动） | 推理设备。例如 `cpu`、`0`、`cuda:0`。空字符串表示自动检测 |
| `--classes` | int[] | `None`（全部） | 按 COCO 类别 ID 过滤。例如 `--classes 0` 仅跟踪人物 |
| `--imgsz` | int | `640` | 推理图像尺寸。长边缩放到此值，保持宽高比。越大越精确，但速度越慢 |

### 可视化参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--save-vid` | flag | 关闭 | 保存 Ultralytics 内置标注视频（边界框 + 跟踪 ID） |
| `--plot-tracks` | flag | 关闭 | 保存轨迹可视化视频（边界框 + 跟踪 ID + 运动轨迹线） |
| `--trail-length` | int | `30` | 轨迹线显示的过去帧数。仅与 `--plot-tracks` 配合使用 |

### 跟踪器参数覆盖

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--with-reid` / `--no-with-reid` | bool | 跟踪器配置值 | 启用/禁用 ReID（重识别） |
| `--track-high-thresh` | float | 跟踪器配置值 | 第一关联置信度阈值 |
| `--track-low-thresh` | float | 跟踪器配置值 | 第二关联置信度阈值 |
| `--new-track-thresh` | float | 跟踪器配置值 | 初始化新轨迹的最低置信度 |
| `--track-buffer` | int | 跟踪器配置值 | 丢失轨迹保持存活的帧数 |
| `--match-thresh` | float | 跟踪器配置值 | 轨迹匹配阈值 |
| `--proximity-thresh` | float | 跟踪器配置值 | ReID 匹配所需的最小 IoU |
| `--appearance-thresh` | float | 跟踪器配置值 | ReID 匹配所需的最小外观相似度 |
| `--gmc-method` | str | 跟踪器配置值 | 全局运动补偿方法 |

---

## 模型选择

YOLO 提供从 Nano 到 Extra-Large 的多种模型规格，在速度和精度之间提供不同的权衡。

### YOLO 模型对比表

| 模型 | 参数量 | 速度 | 精度 | 适用场景 |
|------|--------|------|------|----------|
| `yolo26n.pt` | 最小 | 最快 | 较低 | 实时应用、资源受限环境、快速原型验证 |
| `yolo26s.pt` | 小 | 快 | 中等 | 速度和精度的良好平衡 |
| `yolo26m.pt` | 中 | 中等 | 较高 | 通用场景，推荐用于大多数任务 |
| `yolo26l.pt` | 大 | 较慢 | 高 | 精度优先的场景 |
| `yolo26x.pt` | 最大 | 最慢 | 最高 | 最高精度需求，离线批量处理 |

### 选择建议

- **日常使用 / 快速测试**：`yolo26n.pt`（默认），速度最快，适合快速验证流水线工作是否正常
- **生产环境 / 平衡需求**：`yolo26m.pt`，在大多数场景下提供良好的速度-精度平衡
- **最高精度**：`yolo26x.pt`，适合离线处理、不需要实时速度的场景
- **GPU 内存有限**：优先选择较小的模型（`n` 或 `s`），或减小 `--imgsz`

### 使用示例

```bash
# 使用默认 Nano 模型（最快）
python -m MOT.run --input data/pbl/ --output outputs/

# 使用 Extra-Large 模型（最精确）
python -m MOT.run --input data/pbl/ --output outputs/ --model yolo26x.pt

# 使用 Medium 模型 + 更大推理尺寸
python -m MOT.run --input data/pbl/ --output outputs/ --model yolo26m.pt --imgsz 1280
```

---

## 跟踪器选择

本流水线支持两种跟踪算法，均由 Ultralytics 内置提供。

### BoT-SORT vs ByteTrack 对比

| 特性 | BoT-SORT (`botsort.yaml`) | ByteTrack (`bytetrack.yaml`) |
|------|---------------------------|------------------------------|
| **默认** | 是 | 否 |
| **算法复杂度** | 较高 | 较低 |
| **ReID 支持** | 是（可选启用） | 否 |
| **全局运动补偿 (GMC)** | 是 | 是 |
| **低置信度检测利用** | 是 | 是 |
| **适用场景** | 拥挤场景、频繁遮挡、相机运动较大 | 清晰场景、目标较少、追求速度 |
| **运行速度** | 稍慢（尤其启用 ReID 时） | 更快 |
| **ID 稳定性** | 更高（尤其启用 ReID 时） | 一般 |

### BoT-SORT（默认推荐）

BoT-SORT (Bottom-up One-shot Tracking with SORT) 是默认跟踪器，结合了运动模型、IoU 匹配和可选的 ReID 外观特征。它在 MOT17 和 MOT20 基准测试上表现优异，特别适合：

- 拥挤场景中多个目标相互遮挡
- 相机有明显运动（平移、旋转）
- 需要在遮挡后重新识别目标（启用 ReID）

```bash
# 使用 BoT-SORT（默认）
python -m MOT.run --input data/pbl/ --output outputs/

# 显式指定
python -m MOT.run --input data/pbl/ --output outputs/ --tracker botsort.yaml
```

### ByteTrack

ByteTrack 是一种更简洁高效的跟踪算法。它的核心思想是充分利用所有检测结果（包括低置信度的），通过两阶段关联策略提高跟踪完整性。适合：

- 目标较少且相互不太遮挡的场景
- 追求更快的处理速度
- 不需要 ReID 功能

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --tracker bytetrack.yaml
```

---

## 跟踪器 YAML 配置（详细说明）

### 配置文件来源

`--tracker` 参数接受三种类型的值：

1. **`botsort.yaml`**：Ultralytics 内置的 BoT-SORT 默认配置
2. **`bytetrack.yaml`**：Ultralytics 内置的 ByteTrack 默认配置
3. **自定义 YAML 路径**：如 `/path/to/custom_tracker.yaml`

### 完整配置参数说明

以下是跟踪器 YAML 文件中所有可配置参数的详细说明：

| 参数 | 类型 | BoT-SORT 默认值 | 说明 |
|------|------|-----------------|------|
| `tracker_type` | str | `botsort` | 跟踪算法类型。可选值：`botsort` 或 `bytetrack` |
| `track_high_thresh` | float | `0.25` | **第一关联阈值**。置信度高于此值的检测结果会与现有轨迹进行高优先级匹配。低于此值的检测在第一轮匹配中不会用于更新现有轨迹。这是控制跟踪质量的核心参数之一 |
| `track_low_thresh` | float | `0.1` | **第二关联阈值**（更宽松）。在第一轮高置信度匹配完成后，置信度介于 `track_low_thresh` 和 `track_high_thresh` 之间的检测结果会进入第二轮匹配。这使得跟踪器能够利用部分遮挡或模糊的低置信度检测来维持轨迹 |
| `new_track_thresh` | float | `0.25` | **初始化新轨迹的最低置信度**。只有置信度达到此阈值的未匹配检测才会被认为是新出现的目标并创建新轨迹。降低此值会检测到更多目标，但也可能引入更多误检 |
| `track_buffer` | int | `30` | **丢失轨迹的存活帧数**。当一个被跟踪的目标连续若干帧未被检测到时（例如被遮挡或暂时离开画面），其轨迹会被保留 `track_buffer` 帧。在此期间如果目标重新出现，会恢复原有 ID。超过此帧数后，轨迹被永久删除。值越大，对临时遮挡的容忍度越高，但也会占用更多内存 |
| `match_thresh` | float | `0.8` | **轨迹匹配阈值**。在将检测结果与现有轨迹进行匹配时，匹配代价（基于 IoU 距离）需低于此阈值才被视为有效匹配。值越高，匹配越宽松（更容易将检测分配给轨迹）；值越低，匹配越严格（可能导致更多 ID 切换） |
| `fuse_score` | bool | `true` | **融合置信度和 IoU 距离**。启用后，在匹配前将检测置信度分数融合到 IoU 距离矩阵中，使得高置信度的检测更容易匹配成功。通常建议保持启用 |
| `gmc_method` | str | `sparseOptFlow` | **全局运动补偿 (GMC) 方法**。用于估计和补偿相机的全局运动，使跟踪器在相机移动时仍能准确关联目标。可选值见下表 |
| `proximity_thresh` | float | `0.5` | **ReID 匹配的最小 IoU 要求**。在使用 ReID 特征进行匹配时，两个目标之间的 IoU 还必须高于此阈值，确保空间上的接近性。防止 ReID 将远处的相似目标错误匹配。**仅在 `with_reid: true` 时有效** |
| `appearance_thresh` | float | `0.8` | **ReID 匹配的最小外观相似度**。ReID 特征向量之间的余弦相似度必须高于此阈值才能认为是同一目标。值越高，匹配越严格。**仅在 `with_reid: true` 时有效** |
| `with_reid` | bool | `false` | **启用重识别 (Re-Identification)**。启用后，跟踪器会提取每个目标的外观特征，并利用这些特征在目标被遮挡后重新出现时恢复其原有 ID。详见下方 [ReID 章节](#reid重识别) |
| `model` | str | `auto` | **ReID 模型**。指定用于提取外观特征的模型。`auto` 表示使用 YOLO 检测模型自身的特征；也可以指定专用分类模型如 `yolo26n-cls.pt`。**仅在 `with_reid: true` 时有效** |

### GMC（全局运动补偿）方法

| 方法 | 说明 | 速度 | 精度 |
|------|------|------|------|
| `sparseOptFlow` | 稀疏光流法（默认）。使用 Lucas-Kanade 光流跟踪稀疏特征点来估计全局运动 | 快 | 高 |
| `orb` | ORB 特征匹配。提取 ORB 特征点并通过匹配估计运动 | 快 | 中 |
| `sift` | SIFT 特征匹配。更精确但更慢的特征匹配方法 | 慢 | 高 |
| `ecc` | ECC (Enhanced Correlation Coefficient) 图像对齐。基于像素级对齐 | 慢 | 高 |
| `none` | 禁用全局运动补偿。适用于固定相机（无运动）场景 | 最快 | N/A |

### BoT-SORT 配置示例

```yaml
# botsort.yaml
tracker_type: botsort
track_high_thresh: 0.25
track_low_thresh: 0.1
new_track_thresh: 0.25
track_buffer: 30
match_thresh: 0.8
fuse_score: true
gmc_method: sparseOptFlow
proximity_thresh: 0.5
appearance_thresh: 0.8
with_reid: false
model: auto
```

### ByteTrack 配置示例

```yaml
# bytetrack.yaml
tracker_type: bytetrack
track_high_thresh: 0.25
track_low_thresh: 0.1
new_track_thresh: 0.25
track_buffer: 30
match_thresh: 0.8
fuse_score: true
```

> **注意**：ByteTrack 不支持 ReID 相关参数（`with_reid`、`proximity_thresh`、`appearance_thresh`、`model`）。

---

## 命令行跟踪器覆盖

无需编辑 YAML 文件即可通过命令行直接覆盖跟踪器参数。这对于快速实验不同配置非常方便。

### 基本用法

```bash
# 启用 ReID + 增大轨迹缓冲区
python -m MOT.run --input video.mp4 --output outputs/ --with-reid --track-buffer 60

# 调整检测阈值
python -m MOT.run --input video.mp4 --output outputs/ --track-high-thresh 0.5 --new-track-thresh 0.4

# 禁用全局运动补偿（固定相机）
python -m MOT.run --input video.mp4 --output outputs/ --gmc-method none

# 禁用 ReID
python -m MOT.run --input video.mp4 --output outputs/ --no-with-reid
```

### 可用的覆盖参数

| 命令行参数 | 对应 YAML 键 | 类型 |
|-----------|-------------|------|
| `--with-reid` / `--no-with-reid` | `with_reid` | bool |
| `--track-high-thresh` | `track_high_thresh` | float |
| `--track-low-thresh` | `track_low_thresh` | float |
| `--new-track-thresh` | `new_track_thresh` | float |
| `--track-buffer` | `track_buffer` | int |
| `--match-thresh` | `match_thresh` | float |
| `--proximity-thresh` | `proximity_thresh` | float |
| `--appearance-thresh` | `appearance_thresh` | float |
| `--gmc-method` | `gmc_method` | str |

### 覆盖机制原理

1. 流水线首先加载基础配置文件（`--tracker` 指定的 YAML）
2. 命令行提供的覆盖参数会**合并**到基础配置中，优先级更高
3. 合并后的最终配置保存为 `outputs/tracker_config.yaml`，确保实验的可复现性
4. 跟踪器实际使用的是合并后的配置文件

如果没有使用任何覆盖参数，则直接使用原始 YAML 文件，不会生成 `tracker_config.yaml`。

### 查看生效的配置

运行时的控制台输出会显示是否应用了覆盖：

```
Tracker config: outputs/tracker_config.yaml (with overrides: {'with_reid': True, 'track_buffer': 60})
```

你也可以查看保存的配置文件：

```bash
cat outputs/tracker_config.yaml
```

---

## 自定义跟踪器配置

如果需要更精细的控制，可以创建自定义的跟踪器 YAML 配置文件。

### 步骤一：获取基础配置

有两种方式获取基础配置文件作为起点：

**方式 A**：从之前的运行中复制（推荐）

如果你之前使用了命令行覆盖，`outputs/tracker_config.yaml` 中已包含完整配置：

```bash
cp outputs/tracker_config.yaml my_tracker.yaml
```

**方式 B**：从 Ultralytics 安装目录复制

```bash
# 查找 Ultralytics 内置配置路径
python -c "import ultralytics; print(ultralytics.__file__)"
# 通常在类似 .../ultralytics/cfg/trackers/botsort.yaml 的位置
```

### 步骤二：编辑参数

用你喜欢的编辑器打开并修改参数：

```yaml
# my_tracker.yaml
tracker_type: botsort
track_high_thresh: 0.3      # 提高第一关联阈值
track_low_thresh: 0.05      # 降低第二关联阈值
new_track_thresh: 0.3       # 提高新轨迹阈值
track_buffer: 60            # 增大缓冲区（适合长时间遮挡）
match_thresh: 0.7           # 收紧匹配阈值
fuse_score: true
gmc_method: sparseOptFlow
proximity_thresh: 0.5
appearance_thresh: 0.8
with_reid: true             # 启用 ReID
model: auto
```

### 步骤三：使用自定义配置

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --tracker /path/to/my_tracker.yaml
```

> **注意**：使用自定义 YAML 时，仍然可以通过命令行覆盖参数进一步调整。

---

## ReID（重识别）

### 什么是 ReID

ReID (Re-Identification) 是一种利用**外观特征**来识别目标身份的技术。它为每个被跟踪的目标提取一个外观特征向量（Embedding），当目标被遮挡后重新出现时，通过比较外观特征向量的相似度来恢复原有的跟踪 ID。

### 工作原理

1. 对每个检测到的目标，ReID 模型提取一个外观特征向量
2. 跟踪器同时使用**运动信息**（位置、速度预测）和**外观信息**（特征相似度）进行匹配
3. 当目标被遮挡后重新出现时，即使位置变化较大，外观特征仍可帮助正确匹配

### 何时应该启用 ReID

建议在以下场景启用 ReID：

- **拥挤场景**：多个目标频繁相互遮挡
- **长时间遮挡**：目标可能消失较长时间后重新出现
- **需要稳定的 ID**：下游分析依赖于准确的身份追踪
- **目标外观差异较大**：如不同着装的行人

### 何时不需要启用 ReID

以下场景可以不启用 ReID：

- **目标稀疏**：画面中目标较少，很少发生遮挡
- **追求最快速度**：ReID 会增加计算开销
- **使用 ByteTrack**：ByteTrack 不支持 ReID

### 性能影响

- **首次启用时**：会自动下载 ReID 模型（默认 `yolo26n-cls.pt`），大小约几 MB
- **推理延迟**：每帧需要额外的特征提取计算，处理速度会有所下降
- **GPU 内存**：略微增加 GPU 内存占用

### 启用方式

**方式一：命令行标志**

```bash
# 启用
python -m MOT.run --input video.mp4 --output outputs/ --with-reid

# 禁用（如果 YAML 中默认启用）
python -m MOT.run --input video.mp4 --output outputs/ --no-with-reid
```

**方式二：YAML 配置**

在跟踪器 YAML 文件中设置：

```yaml
with_reid: true
model: auto           # 使用 YOLO 自身特征
# model: yolo26n-cls.pt  # 或使用专用分类模型
```

### 相关参数调优

| 参数 | 默认值 | 调优建议 |
|------|--------|----------|
| `with_reid` | `false` | 设为 `true` 启用 |
| `proximity_thresh` | `0.5` | 降低以允许更远距离的 ReID 匹配（但可能增加误匹配） |
| `appearance_thresh` | `0.8` | 降低以放宽外观匹配（更容易匹配，但可能混淆相似目标） |
| `track_buffer` | `30` | 增大以允许更长的遮挡时间（配合 ReID 效果更好） |

---

## 参数调优指南

### 场景一：目标频繁 ID 切换

**症状**：同一目标的 ID 频繁变化。

**调优建议**：
- 增大 `--track-buffer`（如 60 或更大）
- 启用 `--with-reid`
- 降低 `--match-thresh`（如 0.9，更宽松的匹配）
- 降低 `--track-high-thresh`（如 0.2，接受更多检测用于匹配）

```bash
python -m MOT.run --input video.mp4 --output outputs/ \
    --with-reid --track-buffer 60 --match-thresh 0.9 --track-high-thresh 0.2
```

### 场景二：过多误检（虚假目标）

**症状**：出现不存在的跟踪目标。

**调优建议**：
- 提高 `--conf`（如 0.4 或 0.5）
- 提高 `--new-track-thresh`（如 0.5，需要更高置信度才创建新轨迹）
- 提高 `--track-high-thresh`

```bash
python -m MOT.run --input video.mp4 --output outputs/ \
    --conf 0.5 --new-track-thresh 0.5 --track-high-thresh 0.5
```

### 场景三：固定相机

**症状**：相机不动，不需要运动补偿。

**调优建议**：
- 设置 `--gmc-method none` 禁用全局运动补偿，节省计算时间

```bash
python -m MOT.run --input video.mp4 --output outputs/ --gmc-method none
```

### 场景四：仅跟踪特定类别

**症状**：只关心某些类别（如人物、车辆）。

**调优建议**：
- 使用 `--classes` 过滤。参见 [COCO 类别参考](coco_classes.md) 获取完整 ID 列表

```bash
# 仅跟踪人物
python -m MOT.run --input video.mp4 --output outputs/ --classes 0

# 跟踪人物 + 汽车 + 卡车
python -m MOT.run --input video.mp4 --output outputs/ --classes 0 2 7
```

---

## 显著性评估 (Saliency Evaluation)

### 概述

流水线可选地为每个跟踪边界框计算 **Itti 显著性**分数。Itti 模型是经典的视觉注意力计算模型，结合颜色、亮度和方向特征通道生成显著性图，标出视觉上最显眼的区域。实现通过 PyTorch 在 GPU 上加速。

启用后，为每个边界框计算均值显著性 (0.0-1.0)，追加为 `tracking_results.txt` 的**第 11 列**。

### 集成模式（推荐）

在正常跟踪命令后加 `--eval-saliency`：

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --eval-saliency
```

流程：

1. 照常运行所有视频的跟踪
2. 释放 YOLO 模型的 GPU 显存
3. 对每个已跟踪视频的每一帧计算 Itti 显著性
4. 对每个边界框提取显著性图中的均值
5. 将均值显著性追加为 `tracking_results.txt` 的第 11 列
6. 在 `tracking.log` 中记录显著性评估结果

### 独立模式

如果跟踪已完成，可以单独运行（或重新运行）显著性评估：

```bash
python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/
```

适用于不想重新跟踪、只想重算显著性的场景。

#### 独立模式参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--video-root` | str | **（必填）** | 原始视频根目录（跟踪时的 `--input`） |
| `--results-root` | str | **（必填）** | 跟踪输出根目录（跟踪时的 `--output`） |
| `--workers` | int | `0` | 并行 worker 数。`0` = 自动（每块 GPU 一个） |

### 工作原理

对每个有 `tracking_results.txt` 的视频：

1. 逐帧读取视频
2. 对每一帧，用 Itti 模型在 GPU 上计算全分辨率显著性图
3. 对该帧的每个边界框，提取框内区域的显著性均值
4. 立即丢弃显著性图（内存高效）
5. 所有帧处理完后，将第 11 列追加到 `tracking_results.txt`

### 性能

- **速度**：1920x1080 分辨率约 ~107ms/帧（GPU）
- **GPU 加速**：所有显著性计算通过 PyTorch 在 GPU 上运行
- **多 GPU**：多块 GPU 可用时，视频按轮询分配（与跟踪相同策略）
- **内存**：显著性图逐帧计算和消费，不在内存中保留全视频缓冲。集成模式下 YOLO 模型在显著性计算前释放，不会争抢 GPU 显存

### 输出

显著性评估完成后，`tracking.log` 追加一段：

```
Saliency Evaluation:
  Status:      SUCCESS
  Frames:      103
  Detections:  198
  Time:        11.1s
```

详见 [输出格式](output.md) 中 `tracking_results.txt` 的列定义。

---

[返回概述](README.md) | [上一步：输入数据格式](dataset.md) | [下一步：可视化选项](visualization.md)
