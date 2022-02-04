from PyQt5.QtWidgets import *
from PyQt5.QtCore import QSize, QPoint, Qt
from PyQt5.QtGui import QFont, QIcon

from seg_utils.ui.list_widget import ListWidget
from seg_utils.utils.qt import createListWidgetItemWithSquareIcon, get_icon

from pathlib import Path
import os

STYLESHEET = """QPushButton {
                background-color: lightgray;
                color: black;
                min-height: 2em;
                border-width: 2px;
                border-radius: 8px;
                border-color: black;
                font: bold 12px;
                padding: 2px;
                %s
                }
                QPushButton::hover {
                background-color: gray;
                }
                QPushButton::pressed {
                border-style: outset;
                }"""
BUTTON_STYLESHEET = STYLESHEET % ""
BUTTON_SELECTED_STYLESHEET = STYLESHEET % "border-style: outset;\nbackground-color: gray;"


class NewLabelDialog(QDialog):
    def __init__(self, parent: QWidget, *args):
        super(NewLabelDialog, self).__init__(*args)

        # Default values
        self.class_name = ""
        self.parent = parent

        # Create the shape of the QDialog
        self.setFixedSize(QSize(300, 400))
        move_to_center(self, self.parent.pos(), self.parent.size())
        self.setWindowTitle("Select class of new shape")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Textedit
        self.shapeSearch = QTextEdit(self)
        font = QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.shapeSearch.setFont(font)
        self.shapeSearch.setPlaceholderText("Search shape label")
        self.shapeSearch.setMaximumHeight(25)
        self.shapeSearch.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.shapeSearch.textChanged.connect(self.handle_shape_search)

        # Buttons
        button_widget = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_widget.accepted.connect(self.close)
        button_widget.rejected.connect(self.on_cancel)

        # List of labels
        self.listWidget = ListWidget(self)
        self.listWidget.itemClicked.connect(self.on_list_selection)

        # Combining everything
        layout.addWidget(self.shapeSearch)
        layout.addWidget(button_widget)
        layout.addWidget(self.listWidget)

        self.fill()

    def fill(self):
        """ get all the current label classes and display them in the dialog """
        self.listWidget.clear()
        for idx, _class in enumerate(self.parent.classes):
            item = createListWidgetItemWithSquareIcon(_class, self.parent.colorMap[idx], 10)
            self.listWidget.addItem(item)

        # last entry in the list is used for creating a new label_class
        item = QListWidgetItem(QIcon('icons/plus.png'), "New")
        self.listWidget.addItem(item)

    def handle_shape_search(self):
        """ If user enters text, only suitable shapes are displayed """
        text = self.shapeSearch.toPlainText()
        for item_idx in range(self.listWidget.count()):
            item = self.listWidget.item(item_idx)
            if text not in item.text():
                item.setHidden(True)
            else:
                item.setHidden(False)

    def on_cancel(self):
        self.class_name = ""
        self.close()

    def on_list_selection(self, item):
        """ handles the functions to be executed when user selects something from the list"""
        text = item.text()

        # let user enter a new label class
        if text == "New":
            create_new_class = CreateNewClassDialog(self, self.parent.classes)
            create_new_class.exec()

            # if user entered a name, update the stored label classes
            if create_new_class.new_class:
                text = create_new_class.new_class
                idx = len(self.parent.classes)
                self.parent.classes[text] = idx
                self.fill()
                self.listWidget.item(self.listWidget.count() - 2).setSelected(True)  # highlight new item

            # otherwise, make sure that nothing is passed on
            else:
                text = ""
                self.listWidget.currentItem().setSelected(False)

        # use selected/created label class to name the label
        self.class_name = text

    def set_text(self, text):
        self.shapeSearch.setText(text)
        # move the cursor to the end
        new_cursor = self.shapeSearch.textCursor()
        new_cursor.movePosition(self.shapeSearch.document().characterCount())
        self.shapeSearch.setTextCursor(new_cursor)


class ForgotToSaveMessageBox(QMessageBox):
    def __init__(self, *args):
        super(ForgotToSaveMessageBox, self).__init__(*args)

        save_button = QPushButton(get_icon('save'), "Save Changes")
        dismiss_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogDiscardButton), "Dismiss Changes")
        cancel_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Cancel")

        self.setWindowTitle("Caution: Unsaved Changes")
        self.setText("Unsaved Changes: How do you want to progress?")

        # NOTE FOR SOME REASON THE ORDER IS IMPORTANT DESPITE THE ROLE - IDK WHY
        self.addButton(save_button, QMessageBox.AcceptRole)
        self.addButton(cancel_button, QMessageBox.RejectRole)
        self.addButton(dismiss_button, QMessageBox.DestructiveRole)

        move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())
        
        
class DeleteShapeMessageBox(QMessageBox):
    def __init__(self, shape: str, *args):
        super(DeleteShapeMessageBox, self).__init__(*args)
        move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())
        reply = self.question(self, "Deleting Shape", f"You are about to delete {shape}. Continue?",
                              QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.answer = 1
        else:
            self.answer = 0


class CloseMessageBox(QMessageBox):
    def __init__(self, *args):
        super(CloseMessageBox, self).__init__(*args)

        quit_button = QPushButton(get_icon('quit'), "Quit Program")
        cancel_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogCancelButton), "Cancel")
        self.addButton(quit_button, QMessageBox.AcceptRole)
        self.addButton(cancel_button, QMessageBox.RejectRole)

        self.setWindowTitle("Quit Program")
        self.setText("Are you sure you want to quit?")
        move_to_center(self, self.parentWidget().pos(), self.parentWidget().size())


class CreateNewClassDialog(QDialog):
    """ handles a QDialog used to let the user enter a new label class """
    def __init__(self, parent, existing_classes: list, topic: str = "Label"):
        super(CreateNewClassDialog, self).__init__()

        self.setFixedSize(QSize(200, 120))
        move_to_center(self, parent.pos(), parent.size())
        self.setWindowTitle("Create new {} class".format(topic))

        # need it later to prevent duplicates
        self.new_class = ""
        self.existing_classes = existing_classes

        # Textedit
        self.text_edit = QTextEdit(self)
        font = QFont()
        font.setPointSize(10)
        font.setKerning(True)
        self.text_edit.setFont(font)
        self.text_edit.setPlaceholderText("Enter new {} name".format(topic))
        self.text_edit.setMaximumHeight(25)

        # Buttons
        self.buttonWidget = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonWidget.accepted.connect(self.ok_clicked)
        self.buttonWidget.rejected.connect(self.close)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.buttonWidget)

    def ok_clicked(self):
        """ only accepts the new class if
        (1) the name doesn't already exist and
        (2) the name is not an empty string"""
        name = self.text_edit.toPlainText()
        if name in self.existing_classes:
            self.text_edit.setText("")
            self.text_edit.setPlaceholderText("'{}' already exists".format(name))
        elif name:
            self.new_class = name
            self.close()


class SelectFileTypeAndPatientDialog(QDialog):
    """
    handles a QDialog to let the user select between video, image and whole slide image
    the selected type is the used when importing a new file
    """
    def __init__(self, existing_patients: list):
        super(SelectFileTypeAndPatientDialog, self).__init__()

        self.setFixedSize(QSize(400, 300))
        self.setWindowTitle("Select File Type")
        self.filetype = ""
        self.patient = ""

        # create buttons and apply stylesheet
        v = QPushButton("Video")
        i = QPushButton("Image")
        w = QPushButton("Whole Slide Image")
        self.new_patient = QPushButton("New Patient")
        self.confirmation = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons = [v, i, w, self.new_patient]
        self.set_stylesheets()

        # TODO: Extend by other accepted types, substitute 'whatever' by actual WSI type
        v.clicked.connect(lambda: self.set_type("mp4"))
        i.clicked.connect(lambda: self.set_type("png"))
        w.clicked.connect(lambda: self.set_type("whatever"))
        self.new_patient.clicked.connect(self.create_new_patient)
        self.confirmation.accepted.connect(self.finish)
        self.confirmation.rejected.connect(self.cancel)

        # create patient_list list
        self.patient_list = QListWidget()
        self.patient_list.itemClicked.connect(self.set_patient)
        self.patients_label = QLabel("Select a patient")
        self.patients_label.setStyleSheet("font: bold 12px")
        self.patients = existing_patients
        self.fill()

        # set up the Dialog-Layout
        self.upper_frame = QFrame(self)
        self.upper_layout = QHBoxLayout(self.upper_frame)

        self.btn_frame = QFrame(self.upper_frame)
        self.btn_layout = QVBoxLayout(self.btn_frame)
        self.btn_layout.addStretch(5)
        self.btn_layout.addWidget(v)
        self.btn_layout.addWidget(i)
        self.btn_layout.addWidget(w)
        self.btn_layout.addStretch(5)

        self.patients_frame = QFrame(self.upper_frame)
        self.patients_layout = QVBoxLayout(self.patients_frame)
        self.patients_layout.addWidget(self.patients_label)
        self.patients_layout.addWidget(self.patient_list)
        self.patients_layout.addWidget(self.new_patient)

        self.upper_layout.addWidget(self.btn_frame)
        self.upper_layout.addWidget(self.patients_frame)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.upper_frame)
        self.layout.addWidget(self.confirmation)

    def cancel(self):
        """resets the class variables and closes the dialog"""
        self.filetype, self.patient = "", ""
        self.close()

    def create_new_patient(self):
        """lets user enter a new patient name/id"""
        dlg = CreateNewClassDialog(self, self.patients, topic="Patient")
        dlg.exec()

        if dlg.new_class:
            self.patients.append(dlg.new_class)
            self.fill()
            self.patient_list.item(self.patient_list.count() - 1).setSelected(True)  # highlight new item

    def fill(self):
        """fills the patient listWidget"""
        self.patient_list.clear()
        for patient in self.patients:
            item = QListWidgetItem(patient)
            self.patient_list.addItem(item)

    def finish(self):
        """only allows a closing process when class variables contain values"""
        if self.filetype and self.patient:
            self.close()
        else:
            pass

    def set_patient(self, item):
        """sets the patient class variable"""
        self.patient = item.text()

    def set_stylesheets(self, sel_button: QPushButton = None):
        """sets the stylesheets, if a selected button is passed, apply another stylesheet for it"""
        for b in self.buttons:
            if b == sel_button:
                b.setStyleSheet(BUTTON_SELECTED_STYLESHEET)
            else:
                b.setStyleSheet(BUTTON_STYLESHEET)

    def set_type(self, t: str):
        """ updates the class variable"""
        # sender() returns the currently pressed button, update stylesheets accordingly
        self.set_stylesheets(self.sender())
        self.filetype = t


class ProjectHandlerDialog(QDialog):
    def __init__(self, parent):
        super(ProjectHandlerDialog, self).__init__()
        self.setFixedSize(parent.size() / 2)
        self.setWindowTitle('Create new Project')

        self.project_path = ""
        self.files = dict()
        self.patients = list()

        # Header for LineEdit
        self.header = QLabel()
        self.header.setStyleSheet("font: bold 12px")
        self.header.setText("Choose Project Location")

        # LineEdit where user can enter a path
        self.enter_path = QLineEdit(self)
        self.enter_path.setFixedHeight(30)

        # suggestion for a project location
        suggestion = f"{Path.home()}{os.path.sep}AnnotationProjects{os.path.sep}project"
        for i in range(1, 100):
            if not os.path.exists(suggestion + str(i)):
                suggestion = suggestion + str(i)
                break
        self.enter_path.setText(suggestion)

        # button to open up a FileDialog
        self.select_path_button = QPushButton()
        self.select_path_button.setFixedSize(QSize(40, 30))
        self.select_path_button.setStyleSheet(BUTTON_STYLESHEET)
        self.select_path_button.setText('...')
        self.select_path_button.clicked.connect(self.select_path)

        # button to add initial files
        self.add_files_button = QPushButton()
        self.add_files_button.setFixedWidth(180)
        self.add_files_button.setStyleSheet(BUTTON_STYLESHEET)
        self.add_files_button.setText("Add files to get started")
        self.add_files_button.clicked.connect(self.add_files)

        # ListWidget to display added files
        self.added_files = QListWidget()

        # Accept & cancel buttons
        self.confirmation = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirmation.button(QDialogButtonBox.Ok).setText("Create Project")
        self.confirmation.accepted.connect(self.check_path)
        self.confirmation.rejected.connect(self.close)

        # layout setup
        self.header_frame = QFrame()
        self.header_layout = QHBoxLayout(self.header_frame)
        self.header_layout.setContentsMargins(10, 20, 10, 0)
        self.header_layout.addWidget(self.header)

        self.upper_row = QFrame()
        self.upper_row_layout = QHBoxLayout(self.upper_row)
        self.upper_row_layout.setContentsMargins(10, 0, 10, 0)
        self.upper_row_layout.addWidget(self.enter_path)
        self.upper_row_layout.addWidget(self.select_path_button)

        self.bottom = QFrame()
        self.bottom_layout = QVBoxLayout(self.bottom)
        self.bottom_layout.addWidget(self.add_files_button)
        self.bottom_layout.addWidget(self.added_files)
        self.bottom_layout.addWidget(self.confirmation)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.header_frame)
        self.layout.addWidget(self.upper_row)
        self.layout.addStretch(1)
        self.layout.addWidget(self.bottom)

    def add_files(self):
        """ function to let user select a file which will be added when the project is finally created"""

        # user first needs to specify the type of the file to be imported
        select_filetype = SelectFileTypeAndPatientDialog(self.patients)
        select_filetype.exec()
        self.patients = select_filetype.patients
        filetype, patient = select_filetype.filetype, select_filetype.patient

        if filetype:
            # TODO: implement smarter filetype recognition
            _filter = '*png *jpg *jpeg' if filetype == 'png' else filetype

            filepath, _ = QFileDialog.getOpenFileName(self,
                                                      caption="Select File",
                                                      directory=str(Path.home()),
                                                      filter="File ({})".format(_filter),
                                                      options=QFileDialog.DontUseNativeDialog)

            # only care about the filename itself (not regarding its path), to make it easier to handle
            filename = os.path.basename(filepath)
            if self.exists(filename):
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("The file\n{}\nalready exists.\nOverwrite?".format(filename))
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.accepted.connect(lambda: self.overwrite(filepath, filename, patient))
                msg.exec()
            elif filename:
                # TODO: Implement possibility to add several files at once
                self.files[filepath] = patient
                self.added_files.addItem(QListWidgetItem(filename))

    def check_path(self):
        """ this function verifies/rejects the project path which the user entered in the LineEdit"""
        project_path = self.enter_path.text()

        # check if user entered a non-empty directory
        if os.path.exists(project_path):
            content = os.listdir(project_path)
            if len(content) != 0:

                # confirmation dialog; directory will be cleared if user proceeds
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setText("The directory\n{}\nis not empty.".format(project_path))
                msg.setInformativeText("All existing files in that directory will be deleted.\nProceed?")
                msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msg.accepted.connect(lambda: self.create_project(project_path))
                msg.exec()
            else:
                self.project_path = project_path
                self.close()

        # if user entered a valid absolute path, create the project
        elif os.path.isabs(project_path):
            self.project_path = project_path
            self.close()

        # else do nothing
        else:
            msg = QMessageBox()
            msg.setText("Please enter a valid project location.")
            msg.exec()

    def create_project(self, project_path: str):
        """This function stores a valid path as class variable and closes the dialog"""
        self.project_path = project_path
        self.close()

    def exists(self, filename: str):
        """ check if a filename is already in the list
        also prevents name clashes when two files from different paths have the same name"""
        for i in range(self.added_files.count()):
            cur = self.added_files.item(i).text()
            if cur == filename:
                return True
        return False

    def overwrite(self, filepath: str, filename: str, patient: str):
        """overwrites an existing file in the file list"""

        # find and delete the corresponding item in the files list
        for fn in self.files.keys():
            cur = os.path.basename(fn)
            if cur == filename:
                self.files.pop(fn)
                break

        # append the new filepath
        self.files[filepath] = patient

    def select_path(self):
        """opens a dialog to let the user select a directory from its OS """

        # dialog to select a directory in the user's environment
        dialog = QFileDialog()
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setDirectory(str(Path.home()))

        # store selected path in the LineEdit
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            self.enter_path.setText(filename)


class CommentDialog(QDialog):
    """QDialog to let the user enter notes regarding a specific annotation"""

    def __init__(self, comment: str):
        super(CommentDialog, self).__init__()
        self.setWindowTitle("Notes")
        self.setFixedSize(500, 300)
        self.comment = comment

        # TextEdit where user can enter a comment
        self.enter_comment = QTextEdit(self)
        self.enter_comment.setText(self.comment)

        # Accept & cancel buttons
        self.confirmation = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.confirmation.accepted.connect(self.create_comment)
        self.confirmation.rejected.connect(self.close)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.enter_comment)
        self.layout.addWidget(self.confirmation)

    def create_comment(self):
        """stores the written notes in the class variable and closes the dialog"""
        self.comment = self.enter_comment.toPlainText()
        self.close()


def move_to_center(widget, parent_pos: QPoint, parent_size: QSize):
    r"""Moves the QDialog to the center of the parent Widget.
    As self.move moves the upper left corner to the place, one needs to subtract the own size of the window"""
    widget.move(parent_pos.x() + (parent_size.width() - widget.size().width())/2,
                parent_pos.y() + (parent_size.height() - widget.size().height())/2)
