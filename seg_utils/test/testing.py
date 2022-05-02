"""This file's purpose is to import various classes from seg_utils
in order to test them in isolation"""
import sys

from seg_utils.ui.main_window_new import LabelingMainWindow
from seg_utils.ui.dialogs_new import *
from seg_utils.ui.list_widgets_new import *
from seg_utils.ui.image_display import ImageDisplay
from seg_utils.ui.poly_frame import PolyFrame
from seg_utils.ui.shape import Shape
from seg_utils.utils.qt import colormap_rgb


COLORS, _ = colormap_rgb(25)
CLASSES = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
SHAPES = [Shape(QSize(10, 10), _class, color=_color, shape_type='polygon')
          for _class, _color in zip(CLASSES, COLORS)]
PATIENTS = ["Alex", "Mark", "Clara"]


def test_comment_list():
    # done
    comment_list = CommentList()
    comment_list.show()
    app.exec()


def test_dialog_close():
    # done
    dlg = CloseMessageBox()
    dlg.exec()
    print(dlg.result())


def test_dialog_comment():
    # done
    dlg = CommentDialog("")
    dlg.exec()
    print(dlg.comment)


def test_dialog_delete_class():
    # done
    dlg = DeleteClassMessageBox("tumour")
    dlg.exec()
    print(dlg.answer)


def test_dialog_delete_shape():
    # done
    dlg = DeleteShapeMessageBox("tumour")
    print(dlg.answer)


def test_dialog_forgot_to_save():
    # done
    dlg = ForgotToSaveMessageBox()
    dlg.exec()
    print(dlg.result())


def test_dialog_new_label():
    # done
    dlg = NewLabelDialog(CLASSES, COLORS)
    dlg.exec()
    print(dlg.result)


def test_dialog_project_handler():
    # done
    dlg = ProjectHandlerDialog()
    dlg.exec()
    print("Project Path: {}\n".format(dlg.project_path))
    print("Created Patients:\n")
    for p in dlg.patients:
        print(p)


def test_dialog_select_patient():
    # done
    dlg = SelectPatientDialog(PATIENTS)
    dlg.exec()
    print(dlg.result)


def test_file_viewing_widget():
    # done
    file_widget = FileViewingWidget()
    filenames = ["Picture1", "Picture2", "Video1", "Vid2", "SpecialFile"]
    for fn in filenames:
        item = QListWidgetItem(fn)
        file_widget.file_list.addItem(item)
    file_widget.show()
    app.exec()


def test_image_display():
    window = ImageDisplay()
    pm = QPixmap("../examples/images/video0001_0001.png")
    window.init_image(pm, None)
    window.show()
    app.exec()


def test_label_list():
    # done
    label_list = LabelList()
    label_list.update_with_classes(CLASSES, COLORS)
    label_list.show()
    app.exec()


def test_label_viewing_widget():
    # done
    label_widget = LabelsViewingWidget()
    label_widget.label_list.update_with_classes(CLASSES, COLORS)
    label_widget.show()
    app.exec()


def test_main_window():
    window = LabelingMainWindow()
    window.show()
    app.exec_()


def test_poly_frame():
    window = PolyFrame()
    window.update_frame(SHAPES)
    window.show()
    app.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    test_main_window()
    # test_dialog_new_label()
    # test_dialog_delete_shape()
    # test_dialog_forgot_to_save()
    # test_dialog_close()
    # test_dialog_delete_class()
    # test_dialog_select_patient()
    # test_dialog_project_handler()
    # test_dialog_comment()
    # test_label_list()
    # test_comment_list()
    # test_label_viewing_widget()
    # test_file_viewing_widget()
    # test_image_display()
    test_poly_frame()
