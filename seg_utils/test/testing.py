"""This file's purpose is to import various classes from seg_utils
in order to test them in isolation"""
import sys

from seg_utils.ui.main_window_new import LabelingMainWindow
from seg_utils.ui.dialogs_new import *
from seg_utils.ui.list_widgets_new import *
from seg_utils.ui.image_display import CenterDisplayWidget
from seg_utils.ui.poly_frame import PolyFrame
from seg_utils.ui.shape import Shape
from seg_utils.ui.toolbar import Toolbar
from seg_utils.src.main_logic import MainLogic
from seg_utils.utils.qt import colormap_rgb
from seg_utils.utils.stylesheets import TAB_STYLESHEET


COLORS, _ = colormap_rgb(25)
CLASSES = ["Tumour", "Blood", "Vein", "Healthy Tissue"]
SHAPES = [Shape(QSize(10, 10), _class, color=_color, shape_type='polygon')
          for _class, _color in zip(CLASSES, COLORS)]
PATIENTS = ["Alex", "Mark", "Clara"]


def test_all():
    gui = MainLogic()
    app.exec()


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
    dlg = DeleteClassMessageBox("Gesundes Gewebe")
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
    images = ["Picture1", "Picture2", "PicThree", "importantPicture"]
    wsi = ["WholeSlideImage0001", "WholeSlideImage0002", "anotherWSI"]
    for i, w in zip(images, wsi):
        item1 = QListWidgetItem(i)
        file_widget.image_list.addItem(item1)
        item2 = QListWidgetItem(w)
        file_widget.wsi_list.addItem(item2)
    file_widget.show()
    app.exec()


def test_image_display():
    window = CenterDisplayWidget()
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
    # done
    window = PolyFrame()
    window.update_frame(SHAPES)
    window.show()
    app.exec()


def test_tab():
    tab = QTabWidget()
    w1 = QWidget()
    w2 = QWidget()
    w1.setLayout(QVBoxLayout())
    w2.setLayout(QVBoxLayout())
    w1.layout().addWidget(QLabel("Widget 1"))
    w2.layout().addWidget(QLabel("Widget 2"))
    tab.addTab(w1, 'First')
    tab.addTab(w2, 'Second')
    tab.setStyleSheet(TAB_STYLESHEET)
    tab.show()
    app.exec()


def test_toolbar():
    window = QMainWindow()
    window.setFixedSize(150, 800)
    tb = Toolbar(window)
    window.addToolBar(Qt.ToolBarArea.LeftToolBarArea, tb)
    tb.init_margins()
    tb.init_actions(window)
    window.show()
    app.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # test_dialog_delete_shape()
    # test_dialog_forgot_to_save()
    # test_dialog_close()
    # test_dialog_select_patient()
    # test_dialog_project_handler()
    # test_dialog_comment()
    # test_comment_list()
    # test_label_viewing_widget()
    test_all()
    # test_tab()

    # test_label_list()
    # test_dialog_delete_class()
    # test_file_viewing_widget()
    # test_poly_frame()
    # test_dialog_new_label()
    # test_image_display()
    # test_toolbar()
    # test_main_window()
