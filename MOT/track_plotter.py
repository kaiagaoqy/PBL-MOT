"""Trajectory visualization for tracked objects.

Renders annotated video frames with bounding boxes, track IDs, and
trajectory lines showing each object's movement history over time.
This is different from Ultralytics' built-in `save=True` which only
draws bounding boxes and IDs without movement trajectories.

Comparison:
    --save-vid:     Ultralytics built-in. Bounding boxes + track IDs.
                    No trajectory history.
    --plot-tracks:  Custom rendering. Bounding boxes + track IDs +
                    trajectory lines showing past positions.
"""

import os
from collections import defaultdict, deque

import cv2
import numpy as np


# Color palette for trajectory lines (BGR format)
_PALETTE = [
    (255, 128, 0),    # orange
    (0, 255, 128),    # spring green
    (128, 0, 255),    # violet
    (255, 255, 0),    # cyan
    (0, 128, 255),    # sky blue
    (255, 0, 128),    # rose
    (128, 255, 0),    # chartreuse
    (0, 255, 255),    # yellow
    (255, 0, 255),    # magenta
    (0, 0, 255),      # red
    (255, 0, 0),      # blue
    (0, 255, 0),      # green
    (128, 128, 255),  # salmon
    (255, 128, 128),  # light blue
    (128, 255, 128),  # light green
    (128, 255, 255),  # light yellow
]


class TrackPlotter:
    """Renders video frames with bounding boxes and trajectory lines.

    Accumulates center points for each tracked object and draws
    trajectory polylines on annotated frames, then writes to a
    video file.

    Args:
        output_path: Path to the output video file (.mp4).
        width: Frame width in pixels.
        height: Frame height in pixels.
        fps: Output video frame rate.
        trail_length: Maximum number of past positions to draw per track.
            Controls how long the trajectory "tail" is. Default: 30 frames.

    Example:
        >>> plotter = TrackPlotter("output.mp4", 1920, 1080, 30.0)
        >>> for result in model.track(source, persist=True, stream=True):
        ...     plotter.update(result)
        >>> plotter.close()
    """

    def __init__(
        self,
        output_path: str,
        width: int,
        height: int,
        fps: float,
        trail_length: int = 30,
    ):
        self.output_path = output_path
        self.trail_length = trail_length

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not self.writer.isOpened():
            raise RuntimeError(
                f"Cannot create video writer for: {output_path}"
            )

        # track_id -> deque of (cx, cy) center points
        self.track_history: dict[int, deque] = defaultdict(
            lambda: deque(maxlen=trail_length)
        )

    def update(self, result) -> None:
        """Process one frame: draw boxes, IDs, and trajectory lines.

        Uses result.plot() to get Ultralytics-annotated frame (bounding
        boxes + track IDs + class labels), then overlays trajectory lines.

        Args:
            result: Single Ultralytics tracking result for one frame.
        """
        # Get Ultralytics-annotated frame (boxes + IDs + labels)
        frame = result.plot()

        # Draw trajectory lines if there are tracked objects
        if result.boxes.id is not None:
            boxes = result.boxes.xywh.cpu().numpy()
            track_ids = result.boxes.id.int().cpu().numpy()

            for box, track_id in zip(boxes, track_ids):
                cx, cy = float(box[0]), float(box[1])
                tid = int(track_id)

                self.track_history[tid].append((cx, cy))
                track = self.track_history[tid]

                if len(track) >= 2:
                    points = np.array(track, dtype=np.int32).reshape((-1, 1, 2))
                    color = _PALETTE[tid % len(_PALETTE)]
                    cv2.polylines(
                        frame,
                        [points],
                        isClosed=False,
                        color=color,
                        thickness=2,
                        lineType=cv2.LINE_AA,
                    )

        self.writer.write(frame)

    def close(self) -> str:
        """Finalize the video file and release resources.

        Returns:
            Path to the written video file.
        """
        self.writer.release()
        return self.output_path
