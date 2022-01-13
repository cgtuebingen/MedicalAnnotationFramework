import sys

from PyQt5.QtWidgets import QApplication
from seg_utils.src.label_main import LabelMain
from seg_utils.src.selection_main import SelectionMain
from seg_utils.src.viewer_main import ViewerMain
import argparse


import numpy as np
from PyQt5.QtGui import QPolygonF
from PyQt5.QtCore import QPointF


def main(args):

    app = QApplication(sys.argv)
    window = SelectionMain()  # this opens the selection window
    #window = LabelMain()
    #window = ViewerMain()
    window.show()
    sys.exit(app.exec_())


def closest_node(node, nodes):
    dist_2 = np.sum((nodes - node)**2, axis=1)
    return np.argmin(dist_2)


if __name__ == "__main__":
    # Add arguments to argument parser
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
