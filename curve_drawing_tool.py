import numpy as np
from PIL import Image, ImageDraw
import math

class CurveDrawingTool:
    def __init__(self):
        self.control_points = []
        self.curve_points = []
        self.tension = 0.5
        self.steps = 30

    def add_control_point(self, point):
        self.control_points.append(point)
        self._update_curve()
        return len(self.control_points) - 1

    def update_control_point(self, index, point):
        if 0 <= index < len(self.control_points):
            self.control_points[index] = point
            self._update_curve()
            return True
        return False

    def remove_control_point(self, index):
        if 0 <= index < len(self.control_points):
            self.control_points.pop(index)
            self._update_curve()
            return True
        return False

    def clear_control_points(self):
        self.control_points = []
        self.curve_points = []

    def set_tension(self, tension):
        self.tension = max(0.0, min(1.0, tension))
        self._update_curve()

    def set_steps(self, steps):
        self.steps = max(5, steps)
        self._update_curve()

    def _update_curve(self):
        self.curve_points = []
        if len(self.control_points) < 2:
            self.curve_points = self.control_points.copy()
            return
        for i in range(len(self.control_points) - 1):
            p0 = self.control_points[i]
            p1 = self.control_points[i + 1]
            if i > 0:
                p_prev = self.control_points[i - 1]
            else:
                p_prev = (p0[0] - (p1[0] - p0[0]), p0[1] - (p1[1] - p0[1]))
            if i < len(self.control_points) - 2:
                p_next = self.control_points[i + 2]
            else:
                p_next = (p1[0] + (p1[0] - p0[0]), p1[1] + (p1[1] - p0[1]))
            t0 = (p1[0] - p_prev[0], p1[1] - p_prev[1])
            t1 = (p_next[0] - p0[0], p_next[1] - p0[1])
            t0 = (t0[0] * self.tension, t0[1] * self.tension)
            t1 = (t1[0] * self.tension, t1[1] * self.tension)
            for step in range(self.steps + 1):
                t = step / self.steps
                h1 = 2*t**3 - 3*t**2 + 1
                h2 = -2*t**3 + 3*t**2
                h3 = t**3 - 2*t**2 + t
                h4 = t**3 - t**2
                x = h1 * p0[0] + h2 * p1[0] + h3 * t0[0] + h4 * t1[0]
                y = h1 * p0[1] + h2 * p1[1] + h3 * t0[1] + h4 * t1[1]
                self.curve_points.append((int(x), int(y)))

    def get_curve_points(self):
        return self.curve_points

    def draw_curve_on_image(self, image, color=(255, 0, 0), width=2):
        if not self.curve_points or len(self.curve_points) < 2:
            return image
        result = image.copy()
        draw = ImageDraw.Draw(result)
        for i in range(len(self.curve_points) - 1):
            draw.line([self.curve_points[i], self.curve_points[i + 1]], fill=color, width=width)
        for point in self.control_points:
            draw.ellipse((point[0] - 3, point[1] - 3, point[0] + 3, point[1] + 3),
                         fill=(0, 0, 255), outline=(255, 255, 255))
        return result

    def create_mask(self, image_size, line_width=5):
        if not self.curve_points or len(self.curve_points) < 2:
            return Image.new('L', image_size, 0)
        mask = Image.new('L', image_size, 0)
        draw = ImageDraw.Draw(mask)
        for i in range(len(self.curve_points) - 1):
            draw.line([self.curve_points[i], self.curve_points[i + 1]], fill=255, width=line_width)
        return mask

    def create_closed_mask(self, image_size, fill=255):
        if len(self.curve_points) < 3:
            return Image.new('L', image_size, 0)
        mask = Image.new('L', image_size, 0)
        draw = ImageDraw.Draw(mask)
        closed_curve = self.curve_points.copy()
        if closed_curve[0] != closed_curve[-1]:
            closed_curve.append(closed_curve[0])
        draw.polygon(closed_curve, fill=fill, outline=fill)
        return mask
