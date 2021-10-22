import os.path as osp

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QListWidgetItem
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QRect, QSize

import colorsys
from typing import List, Tuple, Union
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def hsv2rgb(h,s,v):
    """Maps the value of colorsys to [0 255]"""
    return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))


def colormapRGB(n: int, ret_type: str = "qt") -> Union[Tuple[List[QColor], QColor],
                                                       Tuple[List[QColor], QColor]]:
    r"""Creates a colormap with n colors. It reserves the magenta color for a drawNewColor"""
    n_max = 8  # This determines the maximum colors per layer in the hsv cone
    hsv_values = []
    for i in range(n):
        h = (i % (n_max-1)) * (1.0/n_max)
        s = 1.0
        v = 1.0 - (0.2*(i//n_max))
        hsv_values.append((h, s, v))

    drawNewColor = ((n_max-1)/n_max, 1.0, 1.0)
    if ret_type == "qt":
        return [QColor.fromRgbF(*colorsys.hsv_to_rgb(*_hsv))
                for _hsv in hsv_values], QColor.fromRgbF(*colorsys.hsv_to_rgb(*drawNewColor))
    else:
        return [colorsys.hsv_to_rgb(*_hsv) for _hsv in hsv_values], colorsys.hsv_to_rgb(*drawNewColor)


def visualizeColorMap(n: int):
    colourMap, drawNewColor = colormapRGB(n, ret_type="other")
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.set_xlim(10)
    ax.set_ylim(10)

    for i in range(len(colourMap)):
        rect = patches.Rectangle((i % 7 + 1, i // 7 + 1), 1, 1, facecolor=colourMap[i])
        ax.add_patch(rect)

    # new color
    i += 1
    rect_nc = patches.Rectangle((i % 7 + 1, i // 7 + 1), 1, 1, facecolor=drawNewColor)
    ax.add_patch(rect_nc)
    ax.annotate("New\nColor", ((i % 7 + 1) + 0.5, i // 7 + 1 + 0.5), color='w', weight='bold',
                fontsize=6, ha='center', va='center')
    plt.show()


def closestEuclideanDistance(point: np.ndarray, points: np.ndarray):
    dist_2 = np.sum((points - point) ** 2, axis=1)
    return int(np.argmin(dist_2))


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


def getIcon(icon):
    thisFile = osp.dirname(osp.abspath(__file__))
    icons_dir = osp.join(thisFile, "../icons")
    return QIcon(osp.join(":/", icons_dir, "%s.png" % icon))


def QSizeToList(size: QSize):
    return [size.width(), size.height()]


def isInCircle(point: QPointF, centerPointEllipse: QPointF, r=2):
    """Function to check if a point is within a circle with radius r around the centerPoint"""
    raise NotImplementedError
    circle = (point.x()-centerPointEllipse.x()) ** 2 / a ** 2 + (point.y() - centerPointEllipse.y()) ** 2 / b ** 2

    if circle < r ** 2:
        return True
    else:
        return False

