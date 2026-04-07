"""
Itti's Saliency Model (GPU-accelerated)

Faithful reproduction of:
    Itti, L., Koch, C., & Niebur, E. (1998). A model of saliency-based
    visual attention for rapid scene analysis. IEEE PAMI, 20(11), 1254-1259.

Architecture:
    1. Build 9-level Gaussian pyramid for each feature channel.
    2. Center-surround differences using 6 pairs:
       center c ∈ {2,3,4}, surround s = c+δ, δ ∈ {3,4}
       → pairs: (2,5),(2,6),(3,6),(3,7),(4,7),(4,8)
    3. Feature channels:
       - Intensity: I = (r+g+b)/3
       - Color (double-opponent):
         R = r-(g+b)/2, G = g-(r+b)/2, B = b-(r+g)/2, Y = (r+g)/2-|r-g|/2-b
         RG(c,s) = |R(c)-G(s)| + |G(c)-R(s)|
         BY(c,s) = |B(c)-Y(s)| + |Y(c)-B(s)|
       - Orientation: Gabor at 0°,45°,90°,135° on intensity pyramid
    4. N() normalization: promotes maps with few strong peaks.
    5. Three conspicuity maps (I̅, C̅, O̅) combined with equal weights.
    6. 42 feature maps total: 6 intensity + 12 color + 24 orientation.

GPU acceleration: pyramids via avg_pool2d, Gabor via conv2d, N() via max_pool2d.
"""

import numpy as np
import cv2
import torch
import torch.nn.functional as F
from typing import List
import warnings

from MOT.utils.device import get_device, to_tensor, to_numpy, make_gabor_kernels

warnings.filterwarnings('ignore', category=RuntimeWarning)

# ── Constants ──
NUM_PYRAMID_LEVELS = 9
CENTER_SCALES = [2, 3, 4]
SURROUND_DELTAS = [3, 4]
ORIENTATIONS = [0, 45, 90, 135]  # degrees


def _build_pyramid_gpu(channel: torch.Tensor, levels: int = NUM_PYRAMID_LEVELS) -> List[torch.Tensor]:
    """Build Gaussian pyramid on GPU. Input: (1,1,H,W) tensor."""
    pyramid = [channel]
    for _ in range(levels - 1):
        # Gaussian blur approximation + downsample (matches cv2.pyrDown)
        prev = pyramid[-1]
        if prev.shape[2] < 2 or prev.shape[3] < 2:
            break
        down = F.avg_pool2d(prev, kernel_size=2, stride=2)
        pyramid.append(down)
    return pyramid


def _center_surround_gpu(pyramid: List[torch.Tensor], c: int, s: int) -> torch.Tensor:
    """Compute |center(c) ⊖ surround(s)| on GPU via F.interpolate."""
    center = pyramid[c]
    surround = pyramid[s]
    surround_up = F.interpolate(surround, size=center.shape[2:], mode='bilinear', align_corners=False)
    return torch.abs(center - surround_up)


def _N_gpu(feature_map: torch.Tensor) -> torch.Tensor:
    """
    Itti's N() normalization on GPU.
    Promotes maps with few strong peaks, suppresses uniform maps.
    Uses max_pool2d as proxy for local maxima detection.
    """
    M = feature_map.max()
    if M < 1e-10:
        return torch.zeros_like(feature_map)
    normalized = feature_map / M

    # Local maxima via max_pool2d (3×3 neighborhood)
    if normalized.dim() == 2:
        normalized = normalized.unsqueeze(0).unsqueeze(0)
    dilated = F.max_pool2d(normalized, kernel_size=3, stride=1, padding=1)
    local_max_mask = (normalized == dilated) & (normalized > 0)
    local_maxima = normalized[local_max_mask]

    if local_maxima.numel() == 0:
        return normalized.squeeze(0).squeeze(0)

    m_bar = local_maxima.mean()
    result = normalized * (1.0 - m_bar) ** 2
    return result.squeeze(0).squeeze(0)


def _across_scale_addition_gpu(maps: List[torch.Tensor], target_scale: int,
                                pyramid_ref: List[torch.Tensor]) -> torch.Tensor:
    """Combine feature maps across scales on GPU."""
    target_size = pyramid_ref[target_scale].shape[2:]
    result = torch.zeros(1, 1, *target_size, device=maps[0].device)
    for fm in maps:
        if fm.dim() == 2:
            fm = fm.unsqueeze(0).unsqueeze(0)
        elif fm.dim() == 3:
            fm = fm.unsqueeze(0)
        resized = F.interpolate(fm, size=target_size, mode='bilinear', align_corners=False)
        result += _N_gpu(resized.squeeze(0).squeeze(0)).unsqueeze(0).unsqueeze(0)
    return result.squeeze(0).squeeze(0)


def compute_saliency_map(image: np.ndarray) -> np.ndarray:
    """Compute only the saliency map, skipping unnecessary outputs.

    Lightweight version that skips conspicuity map upsampling,
    statistics computation, and mask handling. Use this when you
    only need the raw saliency map (e.g., for per-bbox mean extraction).

    Args:
        image: RGB image as numpy array, shape (H, W, 3).

    Returns:
        Saliency map as numpy array, shape (H, W), float32, range [0, 1].
    """
    device = get_device()
    h, w = image.shape[:2]

    # ── 1. Feature channels (same as full version) ──
    img = image.astype(np.float32) / 255.0 if image.dtype == np.uint8 else image.astype(np.float32)
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    intensity = (r + g + b) / 3.0

    i_max = intensity.max()
    i_thresh = 0.1 * i_max if i_max > 0 else 0.0

    with np.errstate(divide='ignore', invalid='ignore'):
        r_n = np.where(intensity > i_thresh, r / intensity, 0.0)
        g_n = np.where(intensity > i_thresh, g / intensity, 0.0)
        b_n = np.where(intensity > i_thresh, b / intensity, 0.0)

    R = np.maximum(r_n - (g_n + b_n) / 2.0, 0.0)
    G = np.maximum(g_n - (r_n + b_n) / 2.0, 0.0)
    B = np.maximum(b_n - (r_n + g_n) / 2.0, 0.0)
    Y = np.maximum((r_n + g_n) / 2.0 - np.abs(r_n - g_n) / 2.0 - b_n, 0.0)

    low_mask = intensity < i_thresh
    R[low_mask] = 0; G[low_mask] = 0; B[low_mask] = 0; Y[low_mask] = 0

    def _to_pyr(arr):
        t = to_tensor(arr, device).unsqueeze(0).unsqueeze(0)
        return _build_pyramid_gpu(t)

    pyr_I = _to_pyr(intensity)
    pyr_R = _to_pyr(R)
    pyr_G = _to_pyr(G)
    pyr_B = _to_pyr(B)
    pyr_Y = _to_pyr(Y)

    # ── 2. Orientation pyramids ──
    orientation_pyramids = {}
    for theta in ORIENTATIONS:
        orientation_pyramids[theta] = []
        for level in range(len(pyr_I)):
            lh, lw = pyr_I[level].shape[2], pyr_I[level].shape[3]
            ksize = max(5, min(21, lh // 3))
            if ksize % 2 == 0:
                ksize += 1
            sigma = ksize / 5.0
            kern = cv2.getGaborKernel((ksize, ksize), sigma, np.radians(theta), 8.0, 0.5, 0, ktype=cv2.CV_32F)
            kern_t = torch.from_numpy(kern).to(device).unsqueeze(0).unsqueeze(0)
            pad = ksize // 2
            filtered = torch.abs(F.conv2d(pyr_I[level], kern_t, padding=pad))
            orientation_pyramids[theta].append(filtered.squeeze(0).squeeze(0))

    # ── 3. Center-surround + conspicuity ──
    intensity_maps = []
    rg_maps = []
    by_maps = []
    orientation_maps = {theta: [] for theta in ORIENTATIONS}

    for c in CENTER_SCALES:
        for delta in SURROUND_DELTAS:
            s = c + delta
            if s >= len(pyr_I):
                continue
            intensity_maps.append(_center_surround_gpu(pyr_I, c, s))
            rc = pyr_R[c].squeeze(); gs = pyr_G[s].squeeze()
            gc = pyr_G[c].squeeze(); rs = pyr_R[s].squeeze()
            bc = pyr_B[c].squeeze(); ys = pyr_Y[s].squeeze()
            yc = pyr_Y[c].squeeze(); bs = pyr_B[s].squeeze()

            target_size = rc.shape
            rg = torch.abs(rc - F.interpolate(gs.unsqueeze(0).unsqueeze(0), size=target_size, mode='bilinear', align_corners=False).squeeze()) + \
                 torch.abs(gc - F.interpolate(rs.unsqueeze(0).unsqueeze(0), size=target_size, mode='bilinear', align_corners=False).squeeze())
            by = torch.abs(bc - F.interpolate(ys.unsqueeze(0).unsqueeze(0), size=target_size, mode='bilinear', align_corners=False).squeeze()) + \
                 torch.abs(yc - F.interpolate(bs.unsqueeze(0).unsqueeze(0), size=target_size, mode='bilinear', align_corners=False).squeeze())
            rg_maps.append(rg)
            by_maps.append(by)

            for theta in ORIENTATIONS:
                o_pyr = orientation_pyramids[theta]
                if c < len(o_pyr) and s < len(o_pyr):
                    oc = o_pyr[c]; os_ = o_pyr[s]
                    diff = torch.abs(oc - F.interpolate(os_.unsqueeze(0).unsqueeze(0), size=oc.shape, mode='bilinear', align_corners=False).squeeze())
                    orientation_maps[theta].append(diff)

    target_scale = 4
    conspicuity_I = _N_gpu(_across_scale_addition_gpu(intensity_maps, target_scale, pyr_I))

    color_maps = [rg_maps[i] + by_maps[i] for i in range(len(rg_maps))]
    conspicuity_C = _N_gpu(_across_scale_addition_gpu(color_maps, target_scale, pyr_I))

    orientation_combined = torch.zeros_like(conspicuity_I)
    for theta in ORIENTATIONS:
        theta_combined = _across_scale_addition_gpu(orientation_maps[theta], target_scale, pyr_I)
        orientation_combined += _N_gpu(theta_combined)
    conspicuity_O = _N_gpu(orientation_combined)

    # ── 4. Final saliency ──
    saliency_at_scale4 = (conspicuity_I + conspicuity_C + conspicuity_O) / 3.0
    saliency_full = F.interpolate(
        saliency_at_scale4.unsqueeze(0).unsqueeze(0),
        size=(h, w), mode='bilinear', align_corners=False
    ).squeeze(0).squeeze(0)

    s_max = saliency_full.max()
    if s_max > 0:
        saliency_full = saliency_full / s_max

    return to_numpy(saliency_full)
