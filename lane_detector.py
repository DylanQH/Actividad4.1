"""Deteccion de la linea central mediante Canny y HoughLinesP."""

import cv2
import numpy as np


class LaneDetector:
    def __init__(
        self,
        canny_low_threshold,
        canny_high_threshold,
        hough_rho,
        hough_theta,
        hough_threshold,
        hough_min_line_length,
        hough_max_line_gap,
        min_abs_slope,
        blur_level,
        roi_left_bottom_x,
        roi_left_bottom_y,
        roi_left_middle_x,
        roi_left_middle_y,
        roi_left_top_x,
        roi_left_top_y,
        roi_right_top_x,
        roi_right_top_y,
        roi_right_middle_x,
        roi_right_middle_y,
        roi_right_bottom_x,
        roi_right_bottom_y,
    ):
        self.canny_low_threshold = canny_low_threshold
        self.canny_high_threshold = canny_high_threshold
        self.hough_rho = hough_rho
        self.hough_theta = hough_theta
        self.hough_threshold = hough_threshold
        self.hough_min_line_length = hough_min_line_length
        self.hough_max_line_gap = hough_max_line_gap
        self.min_abs_slope = min_abs_slope
        self.blur_level = blur_level
        self.roi_points = [
            (roi_left_bottom_x, roi_left_bottom_y),
            (roi_left_middle_x, roi_left_middle_y),
            (roi_left_top_x, roi_left_top_y),
            (roi_right_top_x, roi_right_top_y),
            (roi_right_middle_x, roi_right_middle_y),
            (roi_right_bottom_x, roi_right_bottom_y),
        ]

    def get_roi_polygon(self, width, height):
        points = [
            (
                int(np.clip(x, 0.0, 1.0) * (width - 1)),
                int(np.clip(y, 0.0, 1.0) * (height - 1)),
            )
            for x, y in self.roi_points
        ]
        return np.array([points], dtype=np.int32)

    def apply_blur(self, gray):
        if self.blur_level <= 0:
            return gray

        kernel_size = self.blur_level * 2 + 1
        return cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)

    @staticmethod
    def normalize_lines(lines):
        if lines is None:
            return []
        return [tuple(int(value) for value in line[0]) for line in lines]

    def filter_lines(self, lines):
        valid_lines = []
        for line in lines:
            x1, y1, x2, y2 = line
            delta_x = x2 - x1
            if delta_x == 0:
                valid_lines.append(line)
                continue

            slope = (y2 - y1) / delta_x
            if abs(slope) >= self.min_abs_slope:
                valid_lines.append(line)
        return valid_lines

    @staticmethod
    def select_line(lines, image_center_x):
        if not lines:
            return None

        return min(
            lines,
            key=lambda line: abs(((line[0] + line[2]) / 2) - image_center_x),
        )

    @staticmethod
    def create_debug_image(
        original_image,
        roi_polygon,
        all_lines,
        valid_lines,
        selected_line,
        selected_center,
    ):
        if original_image.shape[2] == 4:
            debug_image = cv2.cvtColor(original_image, cv2.COLOR_BGRA2BGR)
        else:
            debug_image = original_image.copy()

        cv2.polylines(debug_image, roi_polygon, True, (255, 0, 0), 1)
        for x1, y1, x2, y2 in all_lines:
            cv2.line(debug_image, (x1, y1), (x2, y2), (100, 100, 100), 1)
        for x1, y1, x2, y2 in valid_lines:
            cv2.line(debug_image, (x1, y1), (x2, y2), (0, 255, 255), 1)
        if selected_line is not None:
            x1, y1, x2, y2 = selected_line
            cv2.line(debug_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        if selected_center is not None:
            cv2.circle(debug_image, (selected_center, debug_image.shape[0] - 3), 2, (0, 0, 255), -1)

        return debug_image

    def process(self, image):
        if image is None or image.ndim != 3 or image.shape[2] not in (3, 4):
            raise ValueError("LaneDetector esperaba una imagen BGR o BGRA")

        color_code = cv2.COLOR_BGRA2GRAY if image.shape[2] == 4 else cv2.COLOR_BGR2GRAY
        gray = cv2.cvtColor(image, color_code)
        blurred = self.apply_blur(gray)
        edges = cv2.Canny(
            blurred,
            self.canny_low_threshold,
            self.canny_high_threshold,
        )

        height, width = edges.shape
        roi_polygon = self.get_roi_polygon(width, height)
        mask = np.zeros_like(edges)
        cv2.fillPoly(mask, roi_polygon, 255)
        roi_edges = cv2.bitwise_and(edges, mask)

        raw_lines = cv2.HoughLinesP(
            roi_edges,
            self.hough_rho,
            self.hough_theta,
            self.hough_threshold,
            minLineLength=self.hough_min_line_length,
            maxLineGap=self.hough_max_line_gap,
        )
        all_lines = self.normalize_lines(raw_lines)
        valid_lines = self.filter_lines(all_lines)
        image_center = width / 2
        selected_line = self.select_line(valid_lines, image_center)

        selected_center = None
        error = None
        if selected_line is not None:
            selected_center = int((selected_line[0] + selected_line[2]) / 2)
            error = image_center - selected_center

        debug_image = self.create_debug_image(
            image,
            roi_polygon,
            all_lines,
            valid_lines,
            selected_line,
            selected_center,
        )

        return {
            "gray": gray,
            "edges": edges,
            "roi_edges": roi_edges,
            "roi_polygon": roi_polygon,
            "all_lines": all_lines,
            "valid_lines": valid_lines,
            "selected_line": selected_line,
            "selected_center": selected_center,
            "error": error,
            "debug_image": debug_image,
        }
