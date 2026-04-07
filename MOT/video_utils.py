"""Utilities for video file discovery and metadata extraction.

Provides functions to find video files recursively in directory trees,
extract video metadata via OpenCV, and compute output directory paths
that mirror the input directory structure.
"""

import os
from pathlib import Path

import cv2

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}


def discover_videos(input_path: str) -> list[str]:
    """Find video files from a file path or directory (recursive).

    If input_path is a file, returns it as a single-element list.
    If input_path is a directory, recursively walks the directory tree
    and collects all files with recognized video extensions.

    Args:
        input_path: Path to a single video file or directory tree
            containing videos.

    Returns:
        Sorted list of absolute video file paths.

    Raises:
        FileNotFoundError: If input_path does not exist.
    """
    input_path = os.path.abspath(input_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input path does not exist: {input_path}")

    if os.path.isfile(input_path):
        return [input_path]

    videos = []
    for root, _dirs, files in os.walk(input_path):
        for f in files:
            if os.path.splitext(f)[1].lower() in VIDEO_EXTENSIONS:
                videos.append(os.path.join(root, f))

    return sorted(videos)


def get_video_info(video_path: str) -> dict:
    """Extract metadata from a video file using OpenCV.

    Args:
        video_path: Path to the video file.

    Returns:
        Dict with keys:
            - total_frames (int): Total number of frames.
            - fps (float): Frames per second.
            - width (int): Frame width in pixels.
            - height (int): Frame height in pixels.
            - duration_s (float): Video duration in seconds.

    Raises:
        RuntimeError: If the video file cannot be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video file: {video_path}")

    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_s = total_frames / fps if fps > 0 else 0.0
    finally:
        cap.release()

    return {
        "total_frames": total_frames,
        "fps": fps,
        "width": width,
        "height": height,
        "duration_s": round(duration_s, 2),
    }


def compute_output_dir(
    video_path: str, input_root: str, output_root: str
) -> str:
    """Compute the output directory for a video, preserving relative path structure.

    The output mirrors the input hierarchy, with each video getting its own
    subdirectory named after the video file stem (filename without extension).

    Examples:
        >>> compute_output_dir(
        ...     "data/pbl/Sub140/Task7_AV_Trial1~.mp4",
        ...     "data/pbl/",
        ...     "outputs/",
        ... )
        'outputs/Sub140/Task7_AV_Trial1~'

        >>> compute_output_dir(
        ...     "data/pbl/Sub140/Task7_AV_Trial1~.mp4",
        ...     "data/pbl/Sub140/Task7_AV_Trial1~.mp4",  # single file input
        ...     "outputs/",
        ... )
        'outputs/Task7_AV_Trial1~'

    Args:
        video_path: Absolute path to the video file.
        input_root: The --input value. If it was a directory, this is the
            root from which relative paths are computed. If it was a single
            file, the video stem is used directly.
        output_root: The --output value (root output directory).

    Returns:
        Absolute path to the video's output directory.
    """
    video_path = os.path.abspath(video_path)
    input_root = os.path.abspath(input_root)
    output_root = os.path.abspath(output_root)

    video_stem = Path(video_path).stem

    if os.path.isfile(input_root):
        # Single file input: output directly under output_root/video_stem/
        return os.path.join(output_root, video_stem)

    # Directory input: preserve relative path structure
    rel_path = os.path.relpath(video_path, input_root)
    rel_dir = os.path.dirname(rel_path)

    return os.path.join(output_root, rel_dir, video_stem)
