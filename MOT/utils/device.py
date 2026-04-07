"""Device utilities for GPU/CPU tensor operations.

Provides helpers for device detection and numpy/torch conversions
used by the Itti saliency model and other GPU-accelerated code.
"""

import numpy as np
import torch


def get_device() -> torch.device:
    """Return the best available torch device (GPU if available, else CPU).

    Returns:
        torch.device pointing to CUDA GPU 0 if available, otherwise CPU.
    """
    if torch.cuda.is_available():
        return torch.device("cuda:0")
    return torch.device("cpu")


def to_tensor(arr: np.ndarray, device: torch.device) -> torch.Tensor:
    """Convert a numpy array to a torch tensor on the specified device.

    Args:
        arr: Numpy array (any dtype, will be converted to float32).
        device: Target torch device.

    Returns:
        Float32 torch tensor on the specified device.
    """
    return torch.from_numpy(np.ascontiguousarray(arr).astype(np.float32)).to(device)


def to_numpy(tensor: torch.Tensor) -> np.ndarray:
    """Convert a torch tensor to a numpy array.

    Handles GPU tensors by moving to CPU first.

    Args:
        tensor: Torch tensor on any device.

    Returns:
        Numpy array (float32).
    """
    return tensor.detach().cpu().numpy()


def make_gabor_kernels():
    """Placeholder for Gabor kernel generation (imported but unused by itti.py)."""
    pass
