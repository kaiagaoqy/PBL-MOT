"""YOLO Video Object Tracking Pipeline — Entry Point.

Track all objects in video(s) using Ultralytics YOLO and output:
- MOTChallenge format tracking results (.txt per video)
- Per-video tracking log (.log per video)
- Class ID mapping file (class_mapping.txt)
- Overall summary log (tracking_summary.log)
- (Optional) Annotated tracking video with bounding boxes and track IDs
- (Optional) Trajectory video showing movement paths over time

Prerequisites:
    conda activate py310
    pip install ultralytics

Usage:
    python -m MOT.run --input data/pbl/ --output outputs/
    python -m MOT.run --input data/pbl/Sub140/Task7_AV_Trial1~.mp4 --output outputs/
    python -m MOT.run --input data/pbl/ --output outputs/ --save-vid --model yolo26x.pt
    python -m MOT.run --input data/pbl/ --output outputs/ --plot-tracks --trail-length 50
    python -m MOT.run --input data/pbl/ --output outputs/ --with-reid --classes 0
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch
from ultralytics import YOLO

from MOT.log_writer import write_class_mapping, write_summary_log, write_video_log
from MOT.tracker import process_video
from MOT.tracker_config import resolve_tracker_config
from MOT.video_utils import compute_output_dir, discover_videos


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="YOLO Video Object Tracking Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python -m MOT.run --input data/pbl/ --output outputs/

  # With visualization
  python -m MOT.run --input video.mp4 --output outputs/ --save-vid --plot-tracks

  # Person-only with ReID enabled
  python -m MOT.run --input data/pbl/ --output outputs/ --classes 0 --with-reid

  # Custom tracker params
  python -m MOT.run --input data/pbl/ --output outputs/ --track-buffer 60 --track-high-thresh 0.5

  # Custom tracker YAML file
  python -m MOT.run --input video.mp4 --output outputs/ --tracker /path/to/custom.yaml
        """,
    )

    # === Core arguments ===
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to a single video file or directory tree of videos.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="Output root directory. Directory structure mirrors input. "
        "(default: outputs)",
    )
    parser.add_argument(
        "--tasks",
        type=int,
        nargs="+",
        default=None,
        help="Only process specific task numbers. E.g., --tasks 7 8 9 10 11 "
        "keeps only videos matching Task7_*, Task8_*, etc. "
        "(default: all tasks)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run tracking even if tracking_results.txt already exists. "
        "Without this flag, videos with existing results are skipped.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolo26l.pt",
        help="Ultralytics YOLO model name or path. "
        "Examples: yolo26n.pt, yolo26s.pt, yolo26m.pt, yolo26l.pt, yolo26x.pt. "
        "(default: yolo26n.pt)",
    )
    parser.add_argument(
        "--tracker",
        type=str,
        default="botsort.yaml",
        help="Tracker config: 'botsort.yaml', 'bytetrack.yaml', or path to "
        "a custom YAML file. (default: botsort.yaml)",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.4,
        help="Detection confidence threshold (0.0-1.0). "
        "Detections below this score are discarded. (default: 0.25)",
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.7,
        help="IoU threshold (0.0-1.0) for NMS and tracker association. "
        "(default: 0.7)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="Device for inference. Examples: '' (auto), 'cpu', '0', 'cuda:0'. "
        "When --workers > 1, this is ignored and GPUs are auto-assigned. "
        "(default: '' auto-detect)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of parallel workers for multi-GPU processing. "
        "Each worker loads its own model on a separate GPU. "
        "0 = auto (one worker per GPU, or 1 on CPU). (default: 0)",
    )
    parser.add_argument(
        "--classes",
        type=int,
        nargs="+",
        default=None,
        help="Filter by COCO class IDs. E.g., --classes 0 for person-only, "
        "--classes 0 2 7 for person+car+truck. (default: all classes)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image size. The longer side is scaled to this value; "
        "aspect ratio is preserved. Output coordinates are in original "
        "resolution. Larger values improve accuracy but reduce speed. "
        "(default: 640)",
    )

    # === Post-processing arguments ===
    parser.add_argument(
        "--eval-saliency",
        action="store_true",
        help="After tracking, compute Itti saliency for each bbox and "
        "update tracking_results.txt column 9 with mean saliency values. "
        "Runs after all videos are tracked (YOLO model is freed first).",
    )

    # === Visualization arguments ===
    vis_group = parser.add_argument_group(
        "Visualization",
        "Options for saving annotated videos.",
    )
    vis_group.add_argument(
        "--save-vid",
        action="store_true",
        help="Save annotated video with bounding boxes and track IDs "
        "(Ultralytics built-in rendering).",
    )
    vis_group.add_argument(
        "--plot-tracks",
        action="store_true",
        help="Save video with trajectory lines showing each object's "
        "movement path over time. Can be combined with --save-vid.",
    )
    vis_group.add_argument(
        "--trail-length",
        type=int,
        default=30,
        help="Number of past frames to draw trajectory lines for "
        "each tracked object. Only used with --plot-tracks. (default: 30)",
    )

    # === Tracker parameter overrides ===
    trk_group = parser.add_argument_group(
        "Tracker Parameters",
        "Override individual values in the tracker YAML config. "
        "These take precedence over values in the base config file.",
    )
    trk_group.add_argument(
        "--with-reid",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable Re-Identification for better track persistence "
        "through occlusions. Only works with botsort.yaml. "
        "(default: use tracker config value)",
    )
    trk_group.add_argument(
        "--track-high-thresh",
        type=float,
        default=None,
        help="First association confidence threshold. Detections below "
        "this won't update existing tracks. (default: tracker config)",
    )
    trk_group.add_argument(
        "--track-low-thresh",
        type=float,
        default=None,
        help="Second association threshold (more lenient). Used for "
        "low-confidence detections. (default: tracker config)",
    )
    trk_group.add_argument(
        "--new-track-thresh",
        type=float,
        default=None,
        help="Confidence threshold to initialize new tracks. "
        "(default: tracker config)",
    )
    trk_group.add_argument(
        "--track-buffer",
        type=int,
        default=None,
        help="Number of frames to keep lost tracks alive before removal. "
        "Higher = more tolerance for occlusion. (default: tracker config)",
    )
    trk_group.add_argument(
        "--match-thresh",
        type=float,
        default=None,
        help="Track matching threshold. Higher = more lenient matching. "
        "(default: tracker config)",
    )
    trk_group.add_argument(
        "--proximity-thresh",
        type=float,
        default=None,
        help="Minimum IoU required for a valid ReID match. Ensures "
        "spatial closeness. Only used with ReID. (default: tracker config)",
    )
    trk_group.add_argument(
        "--appearance-thresh",
        type=float,
        default=None,
        help="Minimum appearance similarity for ReID matching. "
        "Only used with ReID. (default: tracker config)",
    )
    trk_group.add_argument(
        "--gmc-method",
        type=str,
        default=None,
        choices=["orb", "sift", "ecc", "sparseOptFlow", "none"],
        help="Global motion compensation method. 'none' to disable. "
        "(default: tracker config)",
    )

    return parser.parse_args()


def _collect_tracker_overrides(args: argparse.Namespace) -> dict:
    """Collect non-None tracker parameter overrides from parsed args.

    Maps CLI arg names (with hyphens) to tracker config keys (with underscores).

    Args:
        args: Parsed command-line arguments.

    Returns:
        Dict of {tracker_param: value} for non-None overrides only.
    """
    # CLI arg name -> tracker config key
    mapping = {
        "with_reid": "with_reid",
        "track_high_thresh": "track_high_thresh",
        "track_low_thresh": "track_low_thresh",
        "new_track_thresh": "new_track_thresh",
        "track_buffer": "track_buffer",
        "match_thresh": "match_thresh",
        "proximity_thresh": "proximity_thresh",
        "appearance_thresh": "appearance_thresh",
        "gmc_method": "gmc_method",
    }

    overrides = {}
    for attr, key in mapping.items():
        value = getattr(args, attr, None)
        if value is not None:
            overrides[key] = value

    return overrides


def _resolve_workers(args: argparse.Namespace) -> int:
    """Determine the number of parallel workers.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Number of workers to use.
    """
    if args.workers > 0:
        return args.workers
    if args.device and args.device != "cpu":
        return 1  # explicit single device
    if torch.cuda.is_available():
        return torch.cuda.device_count()
    return 1


def _worker_fn(
    worker_id: int,
    gpu_id: int | None,
    video_jobs: list[tuple[int, str, str]],
    args: argparse.Namespace,
    resolved_tracker: str,
    run_config: dict,
) -> list[dict]:
    """Worker function: loads its own model on assigned GPU, processes videos.

    Args:
        worker_id: Worker index (0-based).
        gpu_id: GPU device ID to use, or None for CPU/auto.
        video_jobs: List of (global_index, video_path, output_dir) tuples.
        args: Parsed CLI arguments.
        resolved_tracker: Path to resolved tracker YAML config.
        run_config: Run configuration dict for logging.

    Returns:
        List of stats dicts, one per video processed.
    """
    device = str(gpu_id) if gpu_id is not None else args.device
    device_label = f"cuda:{gpu_id}" if gpu_id is not None else (args.device or "auto")

    # Each worker loads its own model instance on its assigned GPU
    model = YOLO(args.model)
    print(f"  [Worker {worker_id}] Model loaded → {device_label}")

    stats_list = []
    for global_idx, vpath, video_output_dir in video_jobs:
        print(f"\n{'='*50}")
        print(f"[{global_idx}] [GPU {device_label}] {vpath}")
        print("=" * 50)

        stats = process_video(
            model=model,
            video_path=vpath,
            video_output_dir=video_output_dir,
            tracker=resolved_tracker,
            conf=args.conf,
            iou=args.iou,
            save_vid=args.save_vid,
            plot_tracks=args.plot_tracks,
            trail_length=args.trail_length,
            device=device,
            classes=args.classes,
            imgsz=args.imgsz,
        )
        stats_list.append(stats)

        # Write per-video log immediately
        video_log_path = os.path.join(video_output_dir, "tracking.log")
        write_video_log(video_log_path, stats, run_config)

    return stats_list


def main() -> None:
    """Run the tracking pipeline.

    Orchestrates the full pipeline: discovers videos, loads the model(s),
    resolves tracker config, processes videos (in parallel across GPUs
    when available), writes per-video logs, and writes the overall
    summary log.
    """
    args = parse_args()

    # Discover videos
    print(f"Discovering videos in: {args.input}")
    if args.tasks:
        print(f"Filtering tasks: {args.tasks}")
    try:
        video_paths = discover_videos(args.input, tasks=args.tasks)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not video_paths:
        print(f"No video files found at: {args.input}")
        sys.exit(1)

    print(f"Found {len(video_paths)} video(s)")

    # Create output root directory
    os.makedirs(args.output, exist_ok=True)

    # Resolve tracker config (apply CLI overrides if any)
    tracker_overrides = _collect_tracker_overrides(args)
    resolved_tracker = resolve_tracker_config(
        tracker=args.tracker,
        overrides=tracker_overrides,
        output_dir=args.output,
    )
    if tracker_overrides:
        print(f"Tracker config: {resolved_tracker} (with overrides: {tracker_overrides})")
    else:
        print(f"Tracker config: {args.tracker}")

    # Determine number of workers
    num_workers = _resolve_workers(args)
    num_gpus = torch.cuda.device_count() if torch.cuda.is_available() else 0

    if num_workers > 1:
        gpu_names = [torch.cuda.get_device_name(i) for i in range(num_gpus)]
        print(f"Workers: {num_workers} (GPUs: {gpu_names})")
    else:
        if args.device:
            infer_device = args.device
        elif torch.cuda.is_available():
            infer_device = f"cuda:0 (auto)"
        else:
            infer_device = "cpu"
        print(f"Workers: 1 | Device: {infer_device}")

    # Write class mapping (load a temporary model to get class names)
    class_mapping_path = os.path.join(args.output, "class_mapping.txt")
    _tmp_model = YOLO(args.model)
    write_class_mapping(class_mapping_path, _tmp_model.names)
    del _tmp_model
    print(f"Class mapping written to: {class_mapping_path}")

    # Build run config dict for logging
    run_config = {
        "model": args.model,
        "tracker": args.tracker,
        "tracker_overrides": tracker_overrides if tracker_overrides else None,
        "conf": args.conf,
        "iou": args.iou,
        "imgsz": args.imgsz,
        "device": f"{num_workers} GPUs" if num_workers > 1 else (args.device or "auto"),
        "classes": args.classes,
        "save_vid": args.save_vid,
        "plot_tracks": args.plot_tracks,
        "trail_length": args.trail_length,
        "input": args.input,
        "output": args.output,
        "workers": num_workers,
    }

    # Prepare video jobs, skip already-completed unless --force
    video_jobs = []
    skipped = 0
    for i, vpath in enumerate(video_paths, 1):
        video_output_dir = compute_output_dir(vpath, args.input, args.output)
        results_file = os.path.join(video_output_dir, "tracking_results.txt")
        if not args.force and os.path.isfile(results_file):
            skipped += 1
            continue
        video_jobs.append((i, vpath, video_output_dir))

    if skipped > 0:
        print(f"Skipped {skipped} video(s) with existing results (use --force to re-run)")
    if not video_jobs:
        print("All videos already processed. Nothing to do.")
    total_label = f"{len(video_jobs)} video(s)"

    # === Execute ===
    all_stats = []

    if num_workers <= 1:
        # Single worker: sequential processing
        gpu_id = None
        if not args.device and num_gpus > 0:
            gpu_id = 0
        all_stats = _worker_fn(
            worker_id=0,
            gpu_id=gpu_id if not args.device else None,
            video_jobs=video_jobs,
            args=args,
            resolved_tracker=resolved_tracker,
            run_config=run_config,
        )
    else:
        # Multi-GPU: distribute videos round-robin across workers
        worker_jobs: list[list] = [[] for _ in range(num_workers)]
        for idx, job in enumerate(video_jobs):
            worker_jobs[idx % num_workers].append(job)

        print(f"\nDistributing {total_label} across {num_workers} GPUs:")
        for w, jobs in enumerate(worker_jobs):
            print(f"  GPU {w}: {len(jobs)} video(s)")

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {}
            for w, jobs in enumerate(worker_jobs):
                if not jobs:
                    continue
                future = executor.submit(
                    _worker_fn,
                    worker_id=w,
                    gpu_id=w,
                    video_jobs=jobs,
                    args=args,
                    resolved_tracker=resolved_tracker,
                    run_config=run_config,
                )
                futures[future] = w

            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    stats_list = future.result()
                    all_stats.extend(stats_list)
                except Exception as e:
                    print(f"  [Worker {worker_id}] FATAL ERROR: {e}")

    # Sort stats by video name for consistent summary order
    all_stats.sort(key=lambda s: s["video_name"])

    # Write overall summary log
    summary_log_path = os.path.join(args.output, "tracking_summary.log")
    write_summary_log(summary_log_path, all_stats, run_config)

    # Print final summary
    success_count = sum(1 for s in all_stats if s["status"] == "success")
    failed_count = len(all_stats) - success_count
    print(f"\n{'='*50}")
    print("TRACKING COMPLETE")
    print(f"{'='*50}")
    print(f"Videos: {len(all_stats)} ({success_count} success, {failed_count} failed)")
    if num_workers > 1:
        print(f"Workers: {num_workers} GPUs")
    print(f"Summary log: {summary_log_path}")
    print(f"Class mapping: {class_mapping_path}")

    # === Saliency evaluation (post-tracking) ===
    if args.eval_saliency:
        # Free YOLO model memory before running saliency
        torch.cuda.empty_cache()

        from MOT.eval_saliency import run_saliency_evaluation

        run_saliency_evaluation(
            video_root=args.input,
            results_root=args.output,
            num_workers=num_workers,
        )


if __name__ == "__main__":
    main()
