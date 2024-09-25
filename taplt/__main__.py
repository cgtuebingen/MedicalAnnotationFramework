import argparse
import sys

from PySide6.QtWidgets import QApplication
from taplt.src.main_logic import MainLogic


def main(_args):
    app = QApplication(sys.argv)
    dev_mode = False
    _ = MainLogic(dev_mode)  # the labeling window
    sys.exit(app.exec())


if __name__ == "__main__":
    # Add arguments to argument parser
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
