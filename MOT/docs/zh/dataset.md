# 输入数据格式

本文档说明流水线支持的视频格式、输入方式，以及输入与输出之间的目录结构映射关系。

---

## 支持的视频格式

流水线支持以下常见视频格式：

| 扩展名 | 格式 | 说明 |
|--------|------|------|
| `.mp4` | MPEG-4 | 最常用的视频格式，推荐使用 |
| `.avi` | AVI | Microsoft 音视频交错格式 |
| `.mov` | QuickTime | Apple QuickTime 格式 |
| `.mkv` | Matroska | 开源多媒体容器格式 |
| `.wmv` | Windows Media | Microsoft Windows 媒体格式 |
| `.flv` | Flash Video | Adobe Flash 视频格式 |
| `.webm` | WebM | Google 开发的开源格式 |

> **注意**：文件扩展名不区分大小写（`.MP4` 和 `.mp4` 均可识别）。

---

## 输入方式

### 方式一：单个视频文件

直接指定视频文件路径：

```bash
python -m MOT.run --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 --output outputs/
```

### 方式二：目录输入（递归发现）

指定一个目录路径，流水线会**递归扫描**该目录及所有子目录，自动发现所有支持格式的视频文件：

```bash
python -m MOT.run --input data/pbl/ --output outputs/
```

流水线将：
1. 遍历 `data/pbl/` 下的整个目录树
2. 收集所有扩展名匹配的视频文件
3. 按文件路径字母排序
4. 依次处理每个视频

---

## 目录结构示例

### 输入目录结构

典型的输入数据组织方式如下：

```
data/pbl/
├── Sub140/
│   ├── Task7_AV_Trial1~.mp4
│   ├── Task7_AV_Trial2~.mp4
│   └── Task8_AV_Trial1~.mp4
├── Sub141/
│   ├── Task7_AV_Trial1~.mp4
│   └── Task8_AV_Trial1~.mp4
└── Sub142/
    └── Task7_AV_Trial1~.mp4
```

### 输出目录结构（镜像输入）

输出目录会**自动镜像输入目录的层级结构**，每个视频的结果保存在以视频文件名（不含扩展名）命名的子目录中：

```
outputs/
├── class_mapping.txt              # 全局：COCO 类别映射
├── tracking_summary.log           # 全局：批次摘要
├── Sub140/
│   ├── Task7_AV_Trial1~/
│   │   ├── tracking_results.txt   # MOTChallenge 格式跟踪结果
│   │   └── tracking.log           # 视频处理日志
│   ├── Task7_AV_Trial2~/
│   │   ├── tracking_results.txt
│   │   └── tracking.log
│   └── Task8_AV_Trial1~/
│       ├── tracking_results.txt
│       └── tracking.log
├── Sub141/
│   ├── Task7_AV_Trial1~/
│   │   ├── tracking_results.txt
│   │   └── tracking.log
│   └── Task8_AV_Trial1~/
│       ├── tracking_results.txt
│       └── tracking.log
└── Sub142/
    └── Task7_AV_Trial1~/
        ├── tracking_results.txt
        └── tracking.log
```

### 单文件输入时的输出结构

当输入为单个文件时，输出直接位于 `outputs/<视频名>/` 下：

```bash
python -m MOT.run --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 --output outputs/
```

```
outputs/
├── class_mapping.txt
├── tracking_summary.log
└── Task7_AV_Trial1~/
    ├── tracking_results.txt
    └── tracking.log
```

---

## 最佳实践

1. **使用 MP4 格式**：MP4 (H.264) 是最广泛支持的格式，兼容性最好
2. **保持一致的目录结构**：按被试（Subject）和任务（Task）组织视频，便于批量处理和结果分析
3. **避免文件名中的特殊字符**：虽然波浪号 `~` 等字符是被支持的，但建议避免使用空格和其他特殊字符
4. **检查视频完整性**：损坏的视频文件会导致处理失败，失败信息将记录在 `tracking.log` 中

---

[返回概述](README.md) | [上一步：安装指南](installation.md) | [下一步：跟踪配置](tracking.md)
