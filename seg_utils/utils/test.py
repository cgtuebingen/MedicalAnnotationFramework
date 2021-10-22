# This file is just for internal testing of certain functionality NOT FOR A TEST OF THE TOOL
from typing import Optional
import numpy as np
import pickle
from typing import List
from PyQt5.QtCore import QSize, QPointF, QRectF
from PyQt5.QtGui import QPolygonF, QVector2D

import time


class Test(object):
    def __init__(self, points: List[QPointF]):
        # i am going to save them as a polygon as it is a representation of a vector and i can access it like a matrix
        self._points = QPolygonF(points)
        self.dummy = 0

    def __getitem__(self, item):
        if not isinstance(item, tuple):
            item = tuple((item,))
            # TODO: could be accelerated but most likely doesn't matter
        ret = tuple([self._points[_pt] for _pt in item])
        if len(ret) == 1:
            return ret[0]
        else:
            return ret

    def __len__(self):
        return len(self._points)


def qt_method(points, displacement):
    return [_pt - displacement for _pt in points]


def for_loop(lst, value):
    for _l in lst:
        _l.val = value


def add_value(a, displacement):
    return a + displacement


def set_class_attribute(element: Test, value):
    element.val = value
    return element


def polytoqpointF(element: QPolygonF):
    return element


def main():
    clock = time.CLOCK_REALTIME

    points = [QPointF(0.0, 0.0), QPointF(0.0, 1.0), QPointF(1.0, 1.0), QPointF(1.0, 0.0)]
    test = Test(points)
    a = test[0]
    four = 4



    #
    """
    start = time.clock_gettime_ns(clock)
    a = map(add_value, points, [displacement]*len(points))
    a_time = time.clock_gettime_ns(clock) - start
    start = time.clock_gettime_ns(clock)
    b = qt_method(points, displacement)
    b_time = time.clock_gettime_ns(clock) - start

    print(f"Map: \t\t {a_time}")  # 3314
    print(f"QT: \t\t {b_time}")  # 242590
    
    inst = [Test() for _ in range(10)]

    start = time.clock_gettime_ns(clock)
    b = list(map(lambda test: test.val, inst))
    b_time = time.clock_gettime_ns(clock) - start

    start = time.clock_gettime_ns(clock)
    a = list(map(set_class_attribute, inst, [1] * len(points)))
    a_time = time.clock_gettime_ns(clock) - start

    print(f"Map: \t\t {a_time}")  # 2426
    print(f"Loop: \t\t {b_time}")   # 47778
    """

if __name__ == "__main__":
    main()
