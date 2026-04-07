"""Writer for MOTChallenge standard tracking output format.

Writes tracking results in the standard 10-column MOTChallenge format
used for multi-object tracking evaluation.

Output format (comma-separated, one detection per line):
    frame,id,bb_left,bb_top,bb_width,bb_height,conf,class,-1,-1

Columns:
    1. frame     - Frame number (1-indexed)
    2. id        - Unique track ID
    3. bb_left   - Bounding box left (x coordinate of top-left corner)
    4. bb_top    - Bounding box top (y coordinate of top-left corner)
    5. bb_width  - Bounding box width
    6. bb_height - Bounding box height
    7. conf      - Detection confidence (0-1)
    8. class     - COCO class ID (0=person, 2=car, etc.)
    9. visibility - Not used (-1)
    10. unused   - Not used (-1)
"""

import os


def write_mot_results(filepath: str, all_results: list[dict]) -> None:
    """Write tracking results to a text file in MOTChallenge format.

    Args:
        filepath: Output .txt file path.
        all_results: List of per-frame result dicts, each containing:
            - frame (int): 1-indexed frame number.
            - track_ids (ndarray): Integer track IDs, shape (N,).
            - bb_left (ndarray): Left x coordinates, shape (N,).
            - bb_top (ndarray): Top y coordinates, shape (N,).
            - bb_width (ndarray): Bounding box widths, shape (N,).
            - bb_height (ndarray): Bounding box heights, shape (N,).
            - confs (ndarray): Confidence scores, shape (N,).
            - classes (ndarray): Integer class IDs, shape (N,).

    Notes:
        - Coordinates are rounded to 1 decimal place.
        - Confidence is rounded to 2 decimal places.
        - Frames with no detections should not be included in all_results
          (they are simply omitted, which is standard MOTChallenge behavior).
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    fmt = "{frame},{tid},{left},{top},{w},{h},{conf},{cls},-1,-1\n"

    with open(filepath, "w") as f:
        for result in all_results:
            frame = result["frame"]
            track_ids = result["track_ids"]
            bb_left = result["bb_left"]
            bb_top = result["bb_top"]
            bb_width = result["bb_width"]
            bb_height = result["bb_height"]
            confs = result["confs"]
            classes = result["classes"]

            for i in range(len(track_ids)):
                line = fmt.format(
                    frame=frame,
                    tid=int(track_ids[i]),
                    left=round(float(bb_left[i]), 1),
                    top=round(float(bb_top[i]), 1),
                    w=round(float(bb_width[i]), 1),
                    h=round(float(bb_height[i]), 1),
                    conf=round(float(confs[i]), 2),
                    cls=int(classes[i]),
                )
                f.write(line)
