"""This file's purpose is to import various classes from seg_utils
in order to test them in isolation"""

from PyQt5.QtWidgets import QApplication
import sys

from seg_utils.ui.main_window_new import LabelingMainWindow


def test_main_window():
    window = LabelingMainWindow()
    window.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Select a function of the above to test out a class in isolation
    window = LabelingMainWindow()
    window.show()

    sys.exit(app.exec_())
