# Installation

This guide covers the prerequisites and setup steps for the YOLO multi-object tracking pipeline.

---

## Prerequisites

- **Conda** (Miniconda or Anaconda) with the `py310` environment already created.
- **Python 3.10+** (provided by the `py310` environment).
- **CUDA-capable GPU** (recommended for reasonable inference speed; CPU mode is supported but significantly slower).

---

## Step 1: Activate the Conda Environment

```bash
conda activate py310
```

All subsequent commands assume this environment is active.

---

## Step 2: Install Ultralytics

The pipeline depends on the `ultralytics` package, which provides the YOLO model, tracker implementations (BoT-SORT and ByteTrack), and all necessary deep learning infrastructure.

```bash
pip install ultralytics
```

This will install `ultralytics` along with its dependencies, including PyTorch, OpenCV, NumPy, and others.

---

## Step 3: Handle NumPy Version Compatibility (If Needed)

If your system's PyTorch was compiled against NumPy 1.x, you may encounter errors like:

```
A module that was compiled using NumPy 1.x cannot be run in NumPy 2.x
```

or:

```
RuntimeError: Numpy is not available
```

To resolve this, downgrade NumPy to a 1.x version:

```bash
pip install "numpy<2"
```

This is only necessary if you see NumPy-related errors. If `ultralytics` installs cleanly and runs without errors, you can skip this step.

---

## Step 4: Verify the Installation

Run the following one-liner to confirm that Ultralytics is installed and importable:

```bash
python -c "from ultralytics import YOLO; print('OK')"
```

If this prints `OK`, the installation is complete.

---

## YOLO Model Download

YOLO model weights are **automatically downloaded on first use**. There is no need to manually download model files.

For example, when you run:

```bash
python -m MOT.run --input data/pbl/ --output outputs/ --model yolo26n.pt
```

The pipeline will automatically download `yolo26n.pt` (if not already cached) before starting inference. Downloaded models are cached in the Ultralytics default directory (typically `~/.config/Ultralytics/` or the current working directory) and reused on subsequent runs.

The same applies to ReID models. If you enable `--with-reid`, the appearance model (`yolo26n-cls.pt` or whichever model is configured) is downloaded automatically on first use.

---

## Summary

| Step | Command |
|------|---------|
| Activate environment | `conda activate py310` |
| Install Ultralytics | `pip install ultralytics` |
| Fix NumPy (if needed) | `pip install "numpy<2"` |
| Verify installation | `python -c "from ultralytics import YOLO; print('OK')"` |

After completing these steps, proceed to [Input Data Format](dataset.md) to prepare your video data, or jump directly to [Tracking Configuration](tracking.md) to start running the pipeline.
