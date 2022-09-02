import argparse
import sys

from PyQt6.QtWidgets import QApplication
from taplt.src.main_logic import MainLogic


def main(_args):
    app = QApplication(sys.argv)
    _ = MainLogic()  # the labeling window
    sys.exit(app.exec())


if __name__ == "__main__":
    # Add arguments to argument parser
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    main(args)
