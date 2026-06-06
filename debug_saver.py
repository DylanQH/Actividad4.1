# debug_saver.py

import os
from datetime import datetime

import cv2


class DebugImageSaver:
    """
    Guarda imágenes de depuración.

    Si max_images es None, guarda sin límite.
    """

    def __init__(
        self,
        output_dir,
        max_images,
        save_every_n_frames,
        save_gray=True,
        save_edges=True,
        save_roi_edges=True,
        save_debug_overlay=True,
    ):
        self.output_dir = output_dir
        self.max_images = max_images
        self.save_every_n_frames = save_every_n_frames

        self.save_gray = save_gray
        self.save_edges = save_edges
        self.save_roi_edges = save_roi_edges
        self.save_debug_overlay = save_debug_overlay

        self.saved_count = 0

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.session_dir = os.path.join(self.output_dir, f"debug_{timestamp}")

        self.original_dir = os.path.join(self.session_dir, "original")
        self.gray_dir = os.path.join(self.session_dir, "gray")
        self.edges_dir = os.path.join(self.session_dir, "edges")
        self.roi_edges_dir = os.path.join(self.session_dir, "roi_edges")
        self.overlay_dir = os.path.join(self.session_dir, "overlay")

        self._create_directories()

    def _create_directories(self):
        os.makedirs(self.original_dir, exist_ok=True)

        if self.save_gray:
            os.makedirs(self.gray_dir, exist_ok=True)

        if self.save_edges:
            os.makedirs(self.edges_dir, exist_ok=True)

        if self.save_roi_edges:
            os.makedirs(self.roi_edges_dir, exist_ok=True)

        if self.save_debug_overlay:
            os.makedirs(self.overlay_dir, exist_ok=True)

    def should_save(self, frame_counter):
        if self.max_images is not None and self.saved_count >= self.max_images:
            return False

        if self.save_every_n_frames <= 0:
            return True

        if frame_counter % self.save_every_n_frames != 0:
            return False

        return True

    def save(self, frame_counter, original_image, result):
        if not self.should_save(frame_counter):
            return

        file_name = f"frame_{frame_counter:06d}.png"

        original_path = os.path.join(self.original_dir, file_name)
        cv2.imwrite(original_path, original_image)

        if self.save_gray:
            gray_path = os.path.join(self.gray_dir, file_name)
            cv2.imwrite(gray_path, result["gray"])

        if self.save_edges:
            edges_path = os.path.join(self.edges_dir, file_name)
            cv2.imwrite(edges_path, result["edges"])

        if self.save_roi_edges:
            roi_edges_path = os.path.join(self.roi_edges_dir, file_name)
            cv2.imwrite(roi_edges_path, result["roi_edges"])

        if self.save_debug_overlay:
            overlay_path = os.path.join(self.overlay_dir, file_name)
            cv2.imwrite(overlay_path, result["debug_image"])

        self.saved_count += 1

        if self.saved_count % 100 == 0:
            print(
                f"[DEBUG SAVER] Saved {self.saved_count} image sets. "
                f"Current frame: {frame_counter}"
            )

    def is_finished(self):
        if self.max_images is None:
            return False

        return self.saved_count >= self.max_images