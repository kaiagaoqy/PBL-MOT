"""Compute Itti saliency for each tracked bounding box.

For each frame that has detections in tracking_results.txt, computes
the Itti saliency map (GPU-accelerated) and extracts the mean saliency
within each bounding box. Appends the mean saliency value as a new column 11
to tracking_results.txt, preserving the original 10-column format.

Memory efficient: saliency map is computed per frame, bbox means are
extracted immediately, and the map is discarded. No intermediate files.
"""

import os
import time
from collections import defaultdict

import cv2
import numpy as np
import torch

from MOT.utils.cv.itti import compute_saliency_map


def parse_tracking_results(filepath: str) -> list[dict]:
    """Parse a MOTChallenge-format tracking results file.

    Args:
        filepath: Path to tracking_results.txt.

    Returns:
        List of detection dicts, each with keys:
            frame, id, bb_left, bb_top, bb_width, bb_height,
            conf, cls, col9, col10, line_index.
    """
    detections = []
    with open(filepath) as f:
        for i, line in enumerate(f):
            parts = line.strip().split(",")
            if len(parts) < 10:
                continue
            detections.append({
                "frame": int(parts[0]),
                "id": int(parts[1]),
                "bb_left": float(parts[2]),
                "bb_top": float(parts[3]),
                "bb_width": float(parts[4]),
                "bb_height": float(parts[5]),
                "conf": float(parts[6]),
                "cls": int(parts[7]),
                "col9": parts[8],
                "col10": parts[9],
                "line_index": i,
            })
    return detections


def _group_by_frame(detections: list[dict]) -> dict[int, list[dict]]:
    """Group detections by frame number.

    Args:
        detections: List of detection dicts from parse_tracking_results().

    Returns:
        Dict mapping frame_number → list of detections in that frame.
    """
    grouped = defaultdict(list)
    for det in detections:
        grouped[det["frame"]].append(det)
    return dict(grouped)


def _compute_bbox_mean_saliency(
    saliency_map: np.ndarray,
    bb_left: float,
    bb_top: float,
    bb_width: float,
    bb_height: float,
) -> float:
    """Compute mean saliency within a bounding box region.

    Clips the bbox to image boundaries. Returns 0.0 if the bbox
    has zero area after clipping.

    Args:
        saliency_map: Saliency map, shape (H, W), values in [0, 1].
        bb_left: Bounding box left x coordinate.
        bb_top: Bounding box top y coordinate.
        bb_width: Bounding box width.
        bb_height: Bounding box height.

    Returns:
        Mean saliency value within the bbox (0.0-1.0).
    """
    h, w = saliency_map.shape

    x1 = max(0, int(round(bb_left)))
    y1 = max(0, int(round(bb_top)))
    x2 = min(w, int(round(bb_left + bb_width)))
    y2 = min(h, int(round(bb_top + bb_height)))

    if x2 <= x1 or y2 <= y1:
        return 0.0

    region = saliency_map[y1:y2, x1:x2]
    return float(np.mean(region))


def evaluate_video_saliency(
    video_path: str,
    tracking_results_path: str,
    device: str = "",
) -> dict:
    """Compute mean Itti saliency for each bbox and update tracking results.

    Flow:
        1. Parse tracking_results.txt → group by frame number
        2. Open video, read frames in order
        3. For frames with detections: compute saliency, extract bbox means
        4. Append mean saliency as new column 11 to tracking_results.txt

    Args:
        video_path: Path to the original video file.
        tracking_results_path: Path to tracking_results.txt to read and update.
        device: GPU device string ("0", "1", etc.) or "" for auto.

    Returns:
        Stats dict with keys: video_name, total_frames_processed,
        total_detections, status, error.
    """
    video_name = os.path.splitext(os.path.basename(video_path))[0]

    stats = {
        "video_name": video_name,
        "total_frames_processed": 0,
        "total_detections": 0,
        "processing_time_s": 0.0,
        "status": "failed",
        "error": None,
    }

    try:
        start_time = time.time()

        # Set device for Itti saliency
        if device:
            torch.cuda.set_device(int(device))

        # Parse tracking results
        detections = parse_tracking_results(tracking_results_path)
        if not detections:
            stats["status"] = "success"
            print(f"  No detections to evaluate")
            return stats

        frame_groups = _group_by_frame(detections)
        target_frames = sorted(frame_groups.keys())
        print(f"  Frames with detections: {len(target_frames)}, "
              f"total bboxes: {len(detections)}")

        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Process frames sequentially
        frame_idx = 0  # 0-indexed
        target_set = set(target_frames)

        # Saliency results: (line_index, mean_saliency)
        saliency_results = {}

        frames_processed = 0
        for frame_idx in range(total_frames):
            frame_number = frame_idx + 1  # 1-indexed (MOT format)

            ret, frame = cap.read()
            if not ret:
                break

            if frame_number not in target_set:
                continue

            # Convert BGR → RGB for Itti saliency
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Compute saliency map only (GPU-accelerated, lightweight)
            saliency_map = compute_saliency_map(frame_rgb)  # (H, W), float32, [0, 1]

            # Extract mean saliency for each bbox in this frame
            for det in frame_groups[frame_number]:
                mean_sal = _compute_bbox_mean_saliency(
                    saliency_map,
                    det["bb_left"],
                    det["bb_top"],
                    det["bb_width"],
                    det["bb_height"],
                )
                saliency_results[det["line_index"]] = mean_sal

            frames_processed += 1
            if frames_processed % 20 == 0:
                print(f"\r  Saliency: {frames_processed}/{len(target_frames)} frames",
                      end="", flush=True)

        cap.release()
        print(f"\r  Saliency: {frames_processed}/{len(target_frames)} frames")

        # Rewrite tracking_results.txt with saliency values in column 9
        _update_tracking_results(tracking_results_path, saliency_results)

        elapsed = time.time() - start_time
        stats.update({
            "total_frames_processed": frames_processed,
            "total_detections": len(saliency_results),
            "processing_time_s": round(elapsed, 2),
            "status": "success",
        })
        print(f"  Updated {len(saliency_results)} detections in {elapsed:.1f}s")

    except Exception as e:
        import traceback
        stats["error"] = str(e)
        print(f"\n  Saliency evaluation FAILED: {e}")
        traceback.print_exc()

    return stats


def _update_tracking_results(filepath: str, saliency_results: dict) -> None:
    """Append saliency values as column 11 to tracking_results.txt.

    Original 10 columns are preserved. Saliency is appended at the end.

    Args:
        filepath: Path to tracking_results.txt.
        saliency_results: Dict mapping line_index → mean_saliency value.
    """
    with open(filepath) as f:
        lines = f.readlines()

    with open(filepath, "w") as f:
        for i, line in enumerate(lines):
            stripped = line.strip()
            if i in saliency_results:
                f.write(f"{stripped},{saliency_results[i]:.4f}\n")
            else:
                f.write(stripped + "\n")
