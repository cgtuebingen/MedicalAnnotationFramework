"""This file's purpose is to import various classes from seg_utils
in order to test them in isolation"""
import sys

from seg_utils.ui.main_window_new import LabelingMainWindow
from seg_utils.ui.dialogs_new import *
from seg_utils.ui.list_widgets_new import *
from seg_utils.utils.qt import colormap_rgb


def test_comment_list():
    # done
    comment_list = CommentList()
    comment_list.show()
    app.exec()


def test_dialog_delete_shape():
    # done
    dlg = DeleteShapeMessageBox("tumour")
    print(dlg.answer)


def test_dialog_forgot_to_save():
    # done
    dlg = ForgotToSaveMessageBox()
    dlg.exec()


def test_dialog_new_label():
    # done
    colors, _ = colormap_rgb(25)
    classes = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
    dlg = NewLabelDialog(classes, colors)
    dlg.exec()


def test_file_viewing_widget():
    # done
    file_widget = FileViewingWidget()
    filenames = ["Picture1", "Picture2", "Video1", "Vid2", "SpecialFile"]
    for fn in filenames:
        item = QListWidgetItem(fn)
        file_widget.file_list.addItem(item)
    file_widget.show()
    app.exec()


def test_label_list():
    # done
    label_list = LabelList()
    colors, _ = colormap_rgb(25)
    classes = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
    label_list.update_with_classes(classes, colors)
    label_list.show()
    app.exec()


def test_label_viewing_widget():
    # done
    label_widget = LabelsViewingWidget()
    colors, _i = colormap_rgb(25)
    classes = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
    label_widget.label_list.update_with_classes(classes, colors)
    label_widget.show()
    app.exec()


def test_main_window():
    window = LabelingMainWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # test_main_window()
    test_dialog_new_label()
    test_dialog_delete_shape()
    test_dialog_forgot_to_save()
    # test_label_list()
    # test_comment_list()
    # test_label_viewing_widget()
    # test_file_viewing_widget()
