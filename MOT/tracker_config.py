"""Tracker configuration resolution and override support.

Loads a base tracker YAML config (built-in or custom), applies CLI
overrides, and writes the merged config to the output directory for
reproducibility.

Supported base configs:
    - "botsort.yaml": BoT-SORT with optional ReID (default)
    - "bytetrack.yaml": ByteTrack, simpler and faster
    - Any custom YAML file path

Tracker parameters that can be overridden via CLI:
    - track_high_thresh: First association confidence threshold
    - track_low_thresh: Second association threshold (more lenient)
    - new_track_thresh: Threshold to initialize new tracks
    - track_buffer: Frames to keep lost tracks alive
    - match_thresh: Matching threshold (higher = more lenient)
    - proximity_thresh: Min IoU for valid ReID match
    - appearance_thresh: Min appearance similarity for ReID
    - gmc_method: Global motion compensation method
    - with_reid: Enable/disable Re-Identification
"""

import os
import shutil
from typing import Any

import yaml


# Parameters that can be overridden via CLI, with their expected types
OVERRIDABLE_PARAMS = {
    "track_high_thresh": float,
    "track_low_thresh": float,
    "new_track_thresh": float,
    "track_buffer": int,
    "match_thresh": float,
    "proximity_thresh": float,
    "appearance_thresh": float,
    "gmc_method": str,
    "with_reid": bool,
}


def _find_builtin_config(tracker_name: str) -> str:
    """Find the path to a built-in Ultralytics tracker config YAML.

    Args:
        tracker_name: Config name like "botsort.yaml" or "bytetrack.yaml".

    Returns:
        Absolute path to the YAML file.

    Raises:
        FileNotFoundError: If the config cannot be found.
    """
    # Try ultralytics's built-in config resolution
    try:
        from ultralytics.cfg import CFG_PATH

        cfg_path = os.path.join(CFG_PATH, "trackers", tracker_name)
        if os.path.isfile(cfg_path):
            return cfg_path
    except (ImportError, AttributeError):
        pass

    # Fallback: search in ultralytics package directory
    try:
        import ultralytics

        pkg_dir = os.path.dirname(ultralytics.__file__)
        cfg_path = os.path.join(pkg_dir, "cfg", "trackers", tracker_name)
        if os.path.isfile(cfg_path):
            return cfg_path
    except ImportError:
        pass

    raise FileNotFoundError(
        f"Built-in tracker config '{tracker_name}' not found. "
        f"Provide a full path to a custom YAML file instead."
    )


def resolve_tracker_config(
    tracker: str,
    overrides: dict[str, Any],
    output_dir: str,
) -> str:
    """Resolve tracker config by loading base YAML and applying overrides.

    If no overrides are provided, returns the path to the base config
    as-is. If overrides are provided, writes a merged config to the
    output directory for reproducibility.

    Args:
        tracker: Base config — "botsort.yaml", "bytetrack.yaml", or
            a path to a custom YAML file.
        overrides: Dict of parameter overrides from CLI args. Only
            non-None values should be included. Keys must be valid
            tracker config parameter names.
        output_dir: Directory to write the merged config. The merged
            file is named "tracker_config.yaml" and serves as a
            reproducible record of the exact tracker settings used.

    Returns:
        Path to the final tracker config YAML to pass to model.track().

    Raises:
        FileNotFoundError: If the base config cannot be found.
        ValueError: If an override key is not a valid tracker parameter.
    """
    # Resolve base config path
    if os.path.isfile(tracker):
        base_path = tracker
    else:
        base_path = _find_builtin_config(tracker)

    # If no overrides, return the base config directly
    if not overrides:
        return base_path

    # Validate override keys
    for key in overrides:
        if key not in OVERRIDABLE_PARAMS:
            raise ValueError(
                f"Unknown tracker parameter: '{key}'. "
                f"Valid parameters: {list(OVERRIDABLE_PARAMS.keys())}"
            )

    # Load base config
    with open(base_path) as f:
        config = yaml.safe_load(f)

    # Apply overrides
    for key, value in overrides.items():
        expected_type = OVERRIDABLE_PARAMS[key]
        config[key] = expected_type(value)

    # Write merged config to output directory
    os.makedirs(output_dir, exist_ok=True)
    merged_path = os.path.join(output_dir, "tracker_config.yaml")

    with open(merged_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    return merged_path
