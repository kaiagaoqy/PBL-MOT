# 常见问题

本文档汇总了使用流水线过程中常见的问题及其解决方案。

---

## 1. GPU 内存不足 (CUDA Out of Memory)

### 错误信息

```
torch.cuda.OutOfMemoryError: CUDA out of memory.
Tried to allocate XXX MiB (GPU 0; XX.XX GiB total capacity; ...)
```

### 原因

模型推理所需的 GPU 内存超过了可用显存。常见于使用较大模型或较大推理尺寸时。

### 解决方案

**方案 A：使用更小的模型**

```bash
# 从 yolo26x.pt 切换到 yolo26n.pt
python -m MOT.run --input data/pbl/ --output outputs/ --model yolo26n.pt
```

**方案 B：减小推理图像尺寸**

```bash
# 从默认的 640 减小到 320
python -m MOT.run --input data/pbl/ --output outputs/ --imgsz 320
```

**方案 C：使用 CPU 推理**

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --device cpu
```

**方案 D：检查其他进程是否占用 GPU**

```bash
nvidia-smi
```

如果有其他进程占用 GPU 内存，考虑关闭它们或切换到另一块 GPU：

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --device 1
```

---

## 2. 无检测结果

### 症状

- `tracking_results.txt` 文件为空
- 日志显示 `0 tracks, 0 detections`

### 可能原因与解决方案

**原因 A：置信度阈值过高**

默认的 `--conf 0.25` 对大多数场景是合理的，但如果目标较小或图像质量较差，检测置信度可能偏低。

```bash
# 降低置信度阈值
python -m MOT.run --input video.mp4 --output outputs/ --conf 0.1
```

**原因 B：类别过滤排除了所有目标**

检查 `--classes` 参数是否正确。

```bash
# 检查视频中有哪些目标：先不使用 --classes 过滤
python -m MOT.run --input video.mp4 --output outputs/

# 查看结果中出现了哪些类别
awk -F',' '{print $8}' outputs/<video_name>/tracking_results.txt | sort -u
```

**原因 C：推理尺寸过小**

对于包含小目标的视频，增大推理尺寸可以提高检测率。

```bash
python -m MOT.run --input video.mp4 --output outputs/ --imgsz 1280
```

**原因 D：视频内容问题**

- 视频过暗、过曝或严重模糊
- 视频中确实没有 COCO 数据集包含的目标类别

---

## 3. 跟踪 ID 频繁跳变

### 症状

同一个目标在不同帧之间被分配了不同的 ID，导致轨迹不连续。

### 解决方案

**方案 A：启用 ReID（重识别）**

ReID 利用外观特征帮助在遮挡后恢复 ID。

```bash
python -m MOT.run --input video.mp4 --output outputs/ --with-reid
```

**方案 B：增大轨迹缓冲区**

允许丢失的轨迹存活更长时间，等待目标重新出现。

```bash
python -m MOT.run --input video.mp4 --output outputs/ --track-buffer 60
```

**方案 C：放宽匹配阈值**

```bash
python -m MOT.run --input video.mp4 --output outputs/ --match-thresh 0.9
```

**方案 D：综合调优**

```bash
python -m MOT.run --input video.mp4 --output outputs/ \
    --with-reid \
    --track-buffer 60 \
    --match-thresh 0.9 \
    --track-high-thresh 0.2
```

**方案 E：检查全局运动补偿**

如果相机有运动，确保 GMC 已启用（默认即启用）：

```bash
# 使用默认的稀疏光流法
python -m MOT.run --input video.mp4 --output outputs/ --gmc-method sparseOptFlow
```

如果相机固定不动，反而应该禁用 GMC：

```bash
python -m MOT.run --input video.mp4 --output outputs/ --gmc-method none
```

---

## 4. 视频编解码器错误

### 错误信息

```
RuntimeError: Cannot open video file: /path/to/video.mp4
```

或

```
cv2.error: OpenCV(4.x.x) ... error: (-215:Assertion failed) ...
```

### 解决方案

**方案 A：检查视频文件是否完整**

```bash
# 使用 ffprobe 检查视频信息
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 video.mp4
```

**方案 B：使用 FFmpeg 转码**

某些编解码器可能不被 OpenCV 支持。使用 FFmpeg 转为标准 H.264 格式：

```bash
ffmpeg -i problematic_video.mkv -c:v libx264 -preset fast -crf 23 output.mp4
```

**方案 C：检查 OpenCV 安装**

确认 OpenCV 已安装并支持所需的编解码器：

```bash
python -c "import cv2; print(cv2.getBuildInformation())" | grep -i ffmpeg
```

如果 FFmpeg 支持为 `NO`，重新安装 OpenCV：

```bash
pip install opencv-python --force-reinstall
```

---

## 5. 找不到视频文件

### 错误信息

```
Error: Input path does not exist: /path/to/videos
```

或

```
No video files found at: /path/to/videos
```

### 解决方案

**检查路径是否正确**

```bash
# 确认路径存在
ls -la /path/to/videos

# 确认目录中有视频文件
find /path/to/videos -type f \( -name "*.mp4" -o -name "*.avi" -o -name "*.mov" \)
```

**检查文件扩展名**

流水线仅识别以下扩展名：`.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm`。

如果视频使用非标准扩展名（如 `.MP4`），仍然可以被识别（扩展名匹配不区分大小写）。但如果使用了完全不同的扩展名（如 `.vid`），需要先重命名。

**检查路径中的特殊字符**

虽然路径中的波浪号 `~` 等字符是被支持的，但某些特殊字符可能导致问题。建议使用绝对路径：

```bash
python -m MOT.run --input /absolute/path/to/videos --output /absolute/path/to/outputs
```

---

## 6. 处理速度慢

### 症状

处理 FPS 远低于预期。

### 诊断

首先确认当前的处理速度和硬件使用情况：

```bash
# 查看 GPU 使用率
nvidia-smi

# 查看 CPU 使用率
top
```

### 解决方案

**方案 A：确认使用了 GPU**

```bash
# 检查 CUDA 是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 显式指定 GPU
python -m MOT.run --input data/pbl/ --output outputs/ --device 0
```

**方案 B：使用更小的模型**

```bash
# yolo26n.pt 是最快的
python -m MOT.run --input data/pbl/ --output outputs/ --model yolo26n.pt
```

**方案 C：减小推理尺寸**

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --imgsz 320
```

**方案 D：禁用不需要的可视化**

可视化（尤其是 `--plot-tracks`）会增加每帧的处理时间。如果不需要可视化，不要启用这些参数。

**方案 E：禁用 ReID**

如果启用了 ReID 但不是必需的，禁用它可以加速处理：

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --no-with-reid
```

**方案 F：对于固定相机禁用 GMC**

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --gmc-method none
```

---

## 7. NumPy 版本冲突

### 错误信息

```
AttributeError: module 'numpy' has no attribute 'int'.
```

或

```
A module that was compiled using NumPy 1.x cannot be run with NumPy 2.x
```

或

```
numpy.core.multiarray failed to import
```

### 原因

PyTorch 或其他依赖是基于 NumPy 1.x 编译的，但环境中安装了 NumPy 2.x。NumPy 2.0 移除了 `numpy.int`、`numpy.float` 等旧版别名，导致不兼容。

### 解决方案

将 NumPy 降级到 1.x：

```bash
pip install "numpy<2"
```

验证：

```bash
python -c "import numpy; print(numpy.__version__)"
```

确保版本号以 `1.` 开头（如 `1.26.4`）。

---

## 8. 模型下载失败

### 错误信息

```
ConnectionError: ... unable to access 'https://...'
```

### 解决方案

**方案 A：检查网络连接**

```bash
# 测试网络连通性
curl -I https://github.com
```

**方案 B：手动下载模型**

在有网络的机器上从 [Ultralytics 官方发布页面](https://github.com/ultralytics/assets/releases) 下载模型文件，然后复制到工作目录：

```bash
# 使用本地路径
python -m MOT.run --input data/pbl/ --output outputs/ --model /path/to/yolo26n.pt
```

**方案 C：设置代理**

```bash
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
python -m MOT.run --input data/pbl/ --output outputs/
```

---

## 9. 输出视频无法播放

### 症状

生成的 `tracked_trajectories.mp4` 在某些播放器中无法播放。

### 原因

轨迹视频使用 `mp4v` (MPEG-4) 编码器，部分播放器可能不完全支持。

### 解决方案

使用 FFmpeg 将视频转码为更通用的 H.264 格式：

```bash
ffmpeg -i tracked_trajectories.mp4 -c:v libx264 -preset fast -crf 23 output.mp4
```

---

## 10. 获取帮助

### 查看命令行帮助

```bash
python -m MOT.run --help
```

### 查看日志

处理过程中的详细信息记录在每个视频的 `tracking.log` 和全局的 `tracking_summary.log` 中。

### 检查配置

如果使用了命令行覆盖参数，查看 `outputs/tracker_config.yaml` 确认配置是否正确。

### 快速诊断流程

1. 查看 `tracking_summary.log`，确认哪些视频失败
2. 查看失败视频的 `tracking.log`，查看完整错误信息和堆栈跟踪
3. 使用单个视频进行测试，缩小问题范围
4. 检查本文档中对应的错误类型和解决方案

---

[返回概述](README.md) | [上一步：COCO 类别参考](coco_classes.md)
