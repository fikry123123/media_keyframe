#!/usr/bin/env python3
"""
Utility helpers for working with image sequence captures.

Provides a thin wrapper that mimics the subset of OpenCV's VideoCapture API
needed by the player so that frame numbers that don't start at zero (common in
VFX pipelines) can still be read without relying on ffmpeg's numbering rules.
"""

import os
import re
from typing import Optional

import cv2


class ImageSequenceCapture:
    """
    Minimal capture implementation for numbered image sequences.

    The class supports the subset of the cv2.VideoCapture interface that the
    application relies on (read, set/get for CAP_PROP_POS_FRAMES and
    CAP_PROP_FRAME_COUNT, release, isOpened). Frames are read on demand to avoid
    loading the entire sequence into memory.
    """

    def __init__(self, pattern: str, default_fps: float = 24.0) -> None:
        self.pattern = pattern
        self.default_fps = float(default_fps)
        self._frame_paths = []
        self._frame_numbers = []
        self._current_index = 0
        self.first_frame_number: Optional[int] = None
        self.last_frame_number: Optional[int] = None
        self._is_valid = False
        self._prepare_frames()

    def _prepare_frames(self) -> None:
        directory = os.path.dirname(self.pattern)
        filename_pattern = os.path.basename(self.pattern)
        match = re.match(r'^(.*)%0(\d+)d(\.[^.]+)$', filename_pattern)
        if not match:
            return

        base_name, digits_str, extension = match.groups()
        digits = int(digits_str)
        regex = re.compile(
            rf'^{re.escape(base_name)}(\d{{{digits}}}){re.escape(extension)}$'
        )

        try:
            entries = os.listdir(directory)
        except OSError:
            return

        collected = []
        for entry in entries:
            match_entry = regex.match(entry)
            if not match_entry:
                continue
            frame_number = int(match_entry.group(1))
            frame_path = os.path.join(directory, entry)
            if os.path.isfile(frame_path):
                collected.append((frame_number, frame_path))

        if not collected:
            return

        collected.sort(key=lambda item: item[0])
        self._frame_numbers = [frame for frame, _ in collected]
        self._frame_paths = [path for _, path in collected]
        self.first_frame_number = self._frame_numbers[0]
        self.last_frame_number = self._frame_numbers[-1]
        self._is_valid = True

    def isOpened(self) -> bool:
        return self._is_valid and bool(self._frame_paths)

    def read(self):
        if not self.isOpened():
            return False, None

        if self._current_index >= len(self._frame_paths):
            return False, None

        frame_path = self._frame_paths[self._current_index]
        frame = cv2.imread(frame_path, cv2.IMREAD_COLOR)
        if frame is None:
            return False, None

        self._current_index += 1
        return True, frame

    def set(self, prop_id, value) -> bool:
        if prop_id == cv2.CAP_PROP_POS_FRAMES:
            try:
                new_index = int(value)
            except (TypeError, ValueError):
                return False
            if new_index < 0:
                new_index = 0
            if new_index > len(self._frame_paths):
                new_index = len(self._frame_paths)
            self._current_index = new_index
            return True
        return False

    def get(self, prop_id) -> float:
        if prop_id == cv2.CAP_PROP_FRAME_COUNT:
            return float(len(self._frame_paths))
        if prop_id == cv2.CAP_PROP_POS_FRAMES:
            return float(self._current_index)
        if prop_id == cv2.CAP_PROP_FPS:
            return float(self.default_fps)
        return 0.0

    def release(self) -> None:
        self._current_index = 0


def create_media_capture(file_path: Optional[str], default_sequence_fps: float = 24.0):
    """
    Create either a VideoCapture or an ImageSequenceCapture depending on the
    provided path. Returns None if the media cannot be opened.
    """
    if not file_path:
        return None

    if '%' in file_path:
        capture = ImageSequenceCapture(file_path, default_sequence_fps)
        if capture.isOpened():
            return capture
        return None

    cap = cv2.VideoCapture(file_path, cv2.CAP_FFMPEG)
    if cap is not None and cap.isOpened():
        return cap
    if cap is not None:
        cap.release()

    cap = cv2.VideoCapture(file_path)
    if cap is not None and cap.isOpened():
        return cap
    if cap is not None:
        cap.release()
    return None

