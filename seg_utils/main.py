import argparse
import sys

from PyQt5.QtWidgets import QApplication
from seg_utils.src.main_logic import MainLogic


def main(_args):
    app = QApplication(sys.argv)
    _ = MainLogic()  # the labeling window
    sys.exit(app.exec_())


if __name__ == "__main__":
    # Add arguments to argument parser
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
