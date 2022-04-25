"""This file's purpose is to import various classes from seg_utils
in order to test them in isolation"""

from PyQt5.QtWidgets import QApplication
import sys

from seg_utils.ui.main_window_new import LabelingMainWindow
from seg_utils.ui.dialogs_new import NewLabelDialog
from seg_utils.ui.list_widgets_new import *
from seg_utils.utils.qt import colormap_rgb


def test_main_window():
    window = LabelingMainWindow()
    window.show()
    app.exec_()


def test_new_label_dialog():
    window = NewLabelDialog()
    window.show()
    app.exec()


def test_label_list():
    label_list = LabelList()
    colors, _ = colormap_rgb(25)
    classes = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
    label_list.update_with_classes(classes, colors)
    label_list.show()
    app.exec()


def test_comment_list():
    comment_list = CommentList()
    comment_list.show()
    app.exec()


def test_label_viewing_widget():
    label_widget = LabelsViewingWidget()
    colors, _i = colormap_rgb(25)
    classes = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
    label_widget.label_list.update_with_classes(classes, colors)
    label_widget.show()
    app.exec()


def test_file_viewing_widget():
    file_widget = FileViewingWidget()
    filenames = ["Picture1", "Picture2", "Video1", "Vid2", "SpecialFile"]
    for fn in filenames:
        item = QListWidgetItem(fn)
        file_widget.file_list.addItem(item)
    file_widget.show()
    app.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    test_main_window()
    test_new_label_dialog()
    test_label_list()
    test_comment_list()
    test_label_viewing_widget()
    test_file_viewing_widget()