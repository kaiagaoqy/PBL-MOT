"""Writer for tracking run logs.

Provides functions to write:
- Per-video tracking log (success and failure details)
- Overall batch summary log
- COCO class ID mapping file
"""

import os
from datetime import datetime


def write_video_log(log_path: str, video_stats: dict, run_config: dict) -> None:
    """Write a log file for a single video's tracking run.

    This is written for BOTH successful and failed videos.
    For failed videos, includes the full error message and traceback.

    Args:
        log_path: Output log file path (placed in the video's output dir).
        video_stats: Stats dict from process_video(), containing:
            - video_name (str): Video filename stem.
            - video_path (str): Full path to the video.
            - total_frames (int): Number of frames processed.
            - total_tracks (int): Number of unique track IDs.
            - total_detections (int): Total detections across all frames.
            - processing_time_s (float): Wall-clock processing time.
            - fps (float): Processing speed (frames/second).
            - status (str): "success" or "failed".
            - error (str or None): Error message if failed.
            - traceback_str (str or None): Full traceback if failed.
            - video_info (dict or None): Video metadata from get_video_info().
            - output_txt (str or None): Path to MOT results file.
            - output_vid (str or None): Path to annotated video.
        run_config: Dict of run configuration (model, tracker, conf, etc.).
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    lines = []
    sep = "=" * 50
    lines.append(sep)
    lines.append(f"Tracking Log: {os.path.basename(video_stats['video_path'])}")
    lines.append(sep)
    lines.append(f"Date:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Model:      {run_config.get('model', 'N/A')}")
    lines.append(f"Tracker:    {run_config.get('tracker', 'N/A')}")
    lines.append(
        f"Confidence: {run_config.get('conf', 'N/A')} | "
        f"IoU: {run_config.get('iou', 'N/A')} | "
        f"imgsz: {run_config.get('imgsz', 'N/A')}"
    )
    lines.append(f"Device:     {run_config.get('device', 'auto')}")
    lines.append("")

    # Video info section
    lines.append("Video Info:")
    lines.append(f"  Path:       {video_stats['video_path']}")

    video_info = video_stats.get("video_info")
    if video_info:
        lines.append(
            f"  Resolution: {video_info['width']}x{video_info['height']}"
        )
        lines.append(f"  Frames:     {video_info['total_frames']}")
        lines.append(f"  FPS:        {video_info['fps']}")
        lines.append(f"  Duration:   {video_info['duration_s']}s")

    lines.append("")

    # Results section
    lines.append("Results:")
    if video_stats["status"] == "success":
        lines.append("  Status:      SUCCESS")
        lines.append(f"  Tracks:      {video_stats['total_tracks']}")
        lines.append(f"  Detections:  {video_stats['total_detections']}")
        lines.append(f"  Time:        {video_stats['processing_time_s']:.1f}s")
        lines.append(f"  Process FPS: {video_stats['fps']:.1f}")
        if video_stats.get("output_txt"):
            lines.append(
                f"  Output:      {os.path.basename(video_stats['output_txt'])}"
            )
        if video_stats.get("output_vid"):
            lines.append(
                f"  Video:       {os.path.basename(video_stats['output_vid'])}"
            )
    else:
        lines.append("  Status:      FAILED")
        lines.append(f"  Error:       {video_stats.get('error', 'Unknown error')}")
        if video_stats.get("traceback_str"):
            lines.append("  Traceback:")
            for tb_line in video_stats["traceback_str"].strip().splitlines():
                lines.append(f"    {tb_line}")

    lines.append(sep)

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_summary_log(
    log_path: str, video_stats: list[dict], run_config: dict
) -> None:
    """Write an overall summary log for the entire batch run.

    Args:
        log_path: Output log file path (in the output root).
        video_stats: List of per-video stats dicts from process_video().
        run_config: Dict of run configuration (model, tracker, conf, etc.).
    """
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    lines = []
    sep = "=" * 50
    dash = "-" * 50

    lines.append(sep)
    lines.append("YOLO Tracking Run Summary")
    lines.append(sep)
    lines.append(f"Date:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(
        f"Model: {run_config.get('model', 'N/A')} | "
        f"Tracker: {run_config.get('tracker', 'N/A')}"
    )
    lines.append(
        f"Conf:  {run_config.get('conf', 'N/A')} | "
        f"IoU: {run_config.get('iou', 'N/A')} | "
        f"imgsz: {run_config.get('imgsz', 'N/A')}"
    )
    lines.append(f"Input: {run_config.get('input', 'N/A')}")
    lines.append("")
    lines.append(dash)

    total_count = len(video_stats)
    for i, stats in enumerate(video_stats, 1):
        name = stats["video_name"]
        status = stats["status"].upper()
        if stats["status"] == "success":
            frames = stats["total_frames"]
            tracks = stats["total_tracks"]
            time_s = stats["processing_time_s"]
            lines.append(
                f"[{i}/{total_count}] {name} -- {status} -- "
                f"{frames} frames, {tracks} tracks, {time_s:.1f}s"
            )
        else:
            error = stats.get("error", "Unknown error")
            lines.append(
                f"[{i}/{total_count}] {name} -- {status} -- {error}"
            )

    lines.append(dash)

    # Totals
    success_count = sum(1 for s in video_stats if s["status"] == "success")
    failed_count = total_count - success_count
    total_frames = sum(
        s["total_frames"] for s in video_stats if s["status"] == "success"
    )
    total_time = sum(
        s["processing_time_s"] for s in video_stats if s["status"] == "success"
    )

    lines.append(
        f"Totals: {total_count} videos "
        f"({success_count} success, {failed_count} failed) | "
        f"{total_frames} frames | {total_time:.1f}s"
    )
    lines.append(sep)

    with open(log_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_class_mapping(filepath: str, class_names: dict[int, str]) -> None:
    """Write a class ID to class name mapping file.

    YOLO uses COCO class IDs. This file maps each numeric ID to its
    human-readable name, allowing users to interpret the 'class' column
    (column 8) in MOTChallenge tracking results.

    Args:
        filepath: Output file path (e.g., outputs/class_mapping.txt).
        class_names: Dict from model.names, mapping int IDs to string names,
            e.g. {0: 'person', 1: 'bicycle', 2: 'car', ...}.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    lines = [
        "# YOLO COCO Class ID Mapping",
        "# Used to interpret the 'class' column (column 8) in tracking_results.txt",
        "# Format: class_id: class_name",
        "",
    ]

    for class_id in sorted(class_names.keys()):
        lines.append(f"{class_id}: {class_names[class_id]}")

    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")
