# 安装指南

本文档介绍如何配置运行环境和安装所需依赖。

---

## 前置条件

- **操作系统**：Linux（推荐）、macOS 或 Windows
- **Python**：3.10+（推荐使用 Conda 管理）
- **GPU**（可选但推荐）：NVIDIA GPU + CUDA（显著加速推理速度）

---

## 第一步：激活 Conda 环境

本流水线使用 `py310` Conda 环境。每次运行前请先激活：

```bash
conda activate py310
```

> **提示**：如果尚未创建该环境，可以使用以下命令创建：
> ```bash
> conda create -n py310 python=3.10 -y
> conda activate py310
> ```

---

## 第二步：安装 Ultralytics

Ultralytics 是本流水线的核心依赖，提供 YOLO 模型和跟踪功能：

```bash
pip install ultralytics
```

这将自动安装以下主要依赖：
- `torch`（PyTorch，深度学习框架）
- `torchvision`（计算机视觉工具）
- `opencv-python`（视频读写与图像处理）
- `numpy`（数值计算）
- `pyyaml`（YAML 配置文件解析）

---

## 第三步：处理 NumPy 版本冲突（如需要）

如果系统中的 PyTorch 是基于 NumPy 1.x 编译的，安装 `ultralytics` 后可能会自动升级 NumPy 到 2.x，导致不兼容错误。常见错误信息：

```
AttributeError: module 'numpy' has no attribute 'int'.
```

或

```
A module that was compiled using NumPy 1.x cannot be run with NumPy 2.x
```

**解决方法**：将 NumPy 降级到 1.x：

```bash
pip install "numpy<2"
```

---

## 第四步：验证安装

运行以下命令验证 Ultralytics 是否安装成功：

```bash
python -c "from ultralytics import YOLO; print('OK')"
```

如果输出 `OK`，说明安装成功。

进一步验证 GPU 可用性（可选）：

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')"
```

---

## YOLO 模型自动下载

YOLO 模型权重文件（如 `yolo26n.pt`）**无需手动下载**。首次使用某个模型时，Ultralytics 会自动从官方服务器下载并缓存到本地：

```bash
# 首次运行时会自动下载 yolo26n.pt
python -m MOT.run --input video.mp4 --output outputs/
```

下载完成后，模型文件会被缓存，后续运行不再需要重新下载。

> **提示**：如果在无网络环境下运行，可以先在有网络的机器上下载模型，然后将 `.pt` 文件复制到工作目录，并通过 `--model /path/to/model.pt` 指定路径。

---

## 安装摘要

```bash
# 1. 激活环境
conda activate py310

# 2. 安装 ultralytics
pip install ultralytics

# 3. 修复 numpy 兼容性（如需要）
pip install "numpy<2"

# 4. 验证
python -c "from ultralytics import YOLO; print('OK')"
```

---

[返回概述](README.md) | [下一步：输入数据格式](dataset.md)
