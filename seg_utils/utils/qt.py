import os.path as osp
import numpy as np
import colorsys
from typing import List, Tuple, Union

from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import QRect


def closest_euclidean_distance(point: np.ndarray, points: np.ndarray):
    dist_2 = np.sum((points - point) ** 2, axis=1)
    return int(np.argmin(dist_2))


def colormap_rgb(n: int, ret_type: str = "qt") -> Union[Tuple[List[QColor], QColor],
                                                        Tuple[List[QColor], QColor]]:
    r"""Creates a colormap with n colors. It reserves the magenta color for a draw_new_color"""
    n_max = 8  # This determines the maximum colors per layer in the hsv cone
    hsv_values = []
    for i in range(n):
        h = (i % (n_max-1)) * (1.0/n_max)
        s = 1.0
        v = 1.0 - (0.2*(i//n_max))
        hsv_values.append((h, s, v))

    draw_new_color = ((n_max-1)/n_max, 1.0, 1.0)
    if ret_type == "qt":
        return [QColor.fromRgbF(*colorsys.hsv_to_rgb(*_hsv))
                for _hsv in hsv_values], QColor.fromRgbF(*colorsys.hsv_to_rgb(*draw_new_color))
    else:
        return [colorsys.hsv_to_rgb(*_hsv) for _hsv in hsv_values], colorsys.hsv_to_rgb(*draw_new_color)


def createListWidgetItemWithSquareIcon(text: str, color: QColor, size: int = 5) -> QListWidgetItem:
    pixmap = QPixmap(size, size)
    painter = QPainter()
    painter.begin(pixmap)
    painter.setPen(color)
    painter.setBrush(color)
    painter.drawRect(QRect(0, 0, size, size))
    icon = QIcon(pixmap)
    painter.end()
    return QListWidgetItem(icon, text)


def get_icon(icon):
    this_file = osp.dirname(osp.abspath(__file__))
    icons_dir = osp.join(this_file, "../icons")
    return QIcon(osp.join(":/", icons_dir, "%s.png" % icon))
