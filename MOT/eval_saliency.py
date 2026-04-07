"""Itti Saliency Evaluation — Standalone Entry Point.

Compute Itti saliency for each tracked bounding box in existing
tracking results. Can be run independently after MOT tracking, or
called automatically via `python -m MOT.run --eval-saliency`.

Usage:
    python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/
    python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/ --workers 2
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import torch

from MOT.saliency_eval import evaluate_video_saliency


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compute Itti saliency for tracked bounding boxes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/
  python -m MOT.eval_saliency --video-root data/pbl/ --results-root outputs/ --workers 1
        """,
    )

    parser.add_argument(
        "--video-root",
        type=str,
        required=True,
        help="Root directory of original videos (e.g., data/pbl/).",
    )
    parser.add_argument(
        "--results-root",
        type=str,
        required=True,
        help="Root directory of tracking outputs (e.g., outputs/). "
        "Will recursively find all tracking_results.txt files.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of parallel workers. 0 = auto (one per GPU). (default: 0)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device for inference. '' = auto, 'cpu', '0', etc. (default: auto)",
    )

    return parser.parse_args()


def discover_jobs(
    video_root: str, results_root: str
) -> list[tuple[str, str]]:
    """Find all (video_path, tracking_results_path) pairs.

    Walks results_root for tracking_results.txt files and maps each
    back to its corresponding video in video_root by reversing the
    output directory structure.

    Args:
        video_root: Root directory of original videos.
        results_root: Root directory of tracking outputs.

    Returns:
        List of (video_path, tracking_results_path) tuples.
    """
    video_root = os.path.abspath(video_root)
    results_root = os.path.abspath(results_root)

    jobs = []
    for root, _dirs, files in os.walk(results_root):
        if "tracking_results.txt" not in files:
            continue

        results_path = os.path.join(root, "tracking_results.txt")

        # Reverse the output structure to find the video.
        # Output:  outputs/Sub140/Task7_AV_Trial1~/tracking_results.txt
        # Video:   data/pbl/Sub140/Task7_AV_Trial1~.mp4
        # The last dir component is the video stem (without extension).
        rel_path = os.path.relpath(root, results_root)
        parts = Path(rel_path).parts

        if len(parts) < 1:
            continue

        # The last part is the video stem, everything before is subdirs
        video_stem = parts[-1]
        sub_dirs = os.path.join(*parts[:-1]) if len(parts) > 1 else ""

        # Search for the video file
        video_dir = os.path.join(video_root, sub_dirs)
        video_path = None
        video_exts = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"]

        for ext in video_exts:
            candidate = os.path.join(video_dir, video_stem + ext)
            if os.path.isfile(candidate):
                video_path = candidate
                break

        if video_path is None:
            print(f"  Warning: Video not found for {results_path} "
                  f"(searched in {video_dir} for {video_stem}.*)")
            continue

        jobs.append((video_path, results_path))

    return sorted(jobs, key=lambda x: x[1])


def _worker_fn(
    worker_id: int,
    gpu_id: int | None,
    jobs: list[tuple[str, str]],
) -> list[dict]:
    """Worker: process assigned videos on a specific GPU.

    Args:
        worker_id: Worker index.
        gpu_id: GPU device ID, or None for auto/CPU.
        jobs: List of (video_path, results_path) tuples.

    Returns:
        List of stats dicts.
    """
    device = str(gpu_id) if gpu_id is not None else ""
    device_label = f"cuda:{gpu_id}" if gpu_id is not None else "auto"

    print(f"  [Worker {worker_id}] GPU: {device_label}, videos: {len(jobs)}")

    stats_list = []
    for video_path, results_path in jobs:
        print(f"\n  [Worker {worker_id}] {os.path.basename(video_path)}")
        stats = evaluate_video_saliency(
            video_path=video_path,
            tracking_results_path=results_path,
            device=device,
        )
        stats_list.append(stats)

        # Append saliency stats to the per-video tracking.log
        log_path = os.path.join(os.path.dirname(results_path), "tracking.log")
        _append_saliency_log(log_path, stats)

    return stats_list


def _append_saliency_log(log_path: str, stats: dict) -> None:
    """Append saliency evaluation results to an existing tracking.log.

    Args:
        log_path: Path to the per-video tracking.log file.
        stats: Saliency evaluation stats dict.
    """
    lines = [
        "",
        "Saliency Evaluation:",
    ]

    if stats["status"] == "success":
        lines.append(f"  Status:      SUCCESS")
        lines.append(f"  Frames:      {stats['total_frames_processed']}")
        lines.append(f"  Detections:  {stats['total_detections']}")
        lines.append(f"  Time:        {stats['processing_time_s']}s")
    else:
        lines.append(f"  Status:      FAILED")
        lines.append(f"  Error:       {stats.get('error', 'Unknown')}")

    lines.append("=" * 50)

    with open(log_path, "a") as f:
        f.write("\n".join(lines) + "\n")


def run_saliency_evaluation(
    video_root: str,
    results_root: str,
    num_workers: int = 0,
    device: str = "",
) -> list[dict]:
    """Run saliency evaluation on all tracking results.

    This is the main function, usable both from CLI and from run.py.

    Args:
        video_root: Root directory of original videos.
        results_root: Root directory of tracking outputs.
        num_workers: Number of parallel workers (0 = auto).
        device: Device string ("", "cpu", "0").

    Returns:
        List of per-video stats dicts.
    """
    print(f"\n{'='*50}")
    print("SALIENCY EVALUATION")
    print(f"{'='*50}")

    # Discover jobs
    jobs = discover_jobs(video_root, results_root)
    if not jobs:
        print("No tracking results found.")
        return []

    print(f"Found {len(jobs)} video(s) with tracking results")

    # Determine workers
    if num_workers <= 0:
        if device == "cpu":
            num_workers = 1
        elif torch.cuda.is_available():
            num_workers = torch.cuda.device_count()
        else:
            num_workers = 1

    num_workers = min(num_workers, len(jobs))

    start_time = time.time()

    if num_workers <= 1:
        # Single worker
        gpu_id = None
        if not device and torch.cuda.is_available():
            gpu_id = 0
        elif device and device != "cpu":
            gpu_id = int(device)

        all_stats = _worker_fn(
            worker_id=0,
            gpu_id=gpu_id,
            jobs=jobs,
        )
    else:
        # Multi-GPU: distribute round-robin
        worker_jobs: list[list] = [[] for _ in range(num_workers)]
        for idx, job in enumerate(jobs):
            worker_jobs[idx % num_workers].append(job)

        print(f"Distributing across {num_workers} GPUs")

        all_stats = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            for w, wjobs in enumerate(worker_jobs):
                if not wjobs:
                    continue
                future = executor.submit(_worker_fn, w, w, wjobs)
                futures[future] = w

            for future in as_completed(futures):
                try:
                    all_stats.extend(future.result())
                except Exception as e:
                    print(f"  Worker error: {e}")

    elapsed = time.time() - start_time
    success = sum(1 for s in all_stats if s["status"] == "success")
    failed = len(all_stats) - success

    print(f"\n{'='*50}")
    print(f"SALIENCY COMPLETE: {len(all_stats)} videos "
          f"({success} success, {failed} failed) in {elapsed:.1f}s")
    print(f"{'='*50}")

    return all_stats


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    run_saliency_evaluation(
        video_root=args.video_root,
        results_root=args.results_root,
        num_workers=args.workers,
        device=args.device,
    )


if __name__ == "__main__":
    main()
