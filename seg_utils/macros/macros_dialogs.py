from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont

from pathlib import Path
from seg_utils.utils.stylesheets import BUTTON_STYLESHEET


class ExampleProjectDialog(QDialog):
    def __init__(self):
        super(ExampleProjectDialog, self).__init__()
        self.setFixedSize(QSize(300,200))
        self.setLayout(QVBoxLayout())
        self.accepted = False

        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setText("Welcome to your first project. \n "
                          "Click the button below to open up an example project")
        self.info.setFont(QFont("Helvetica", 15, QFont.Bold))

        self.button = QPushButton("SHow me an example project")
        self.button.setStyleSheet(BUTTON_STYLESHEET)
        self.button.clicked.connect(self.finish)

        self.layout().addWidget(self.info)
        self.layout().setSpacing(10)
        self.layout().addWidget(self.button)

    def finish(self):
        """closes the dialog and accepts it"""
        self.accepted = True
        self.close()


class ExampleProjectMessageBox(QMessageBox):
    """informs the user about the example project"""

    def __init__(self, location: str):
        super(ExampleProjectMessageBox, self).__init__()

        self.setText("Welcome to your first project!\n It is stored under \n {}".format(location))
        self.setInformativeText("To your right, you can see the information displays, showing your project files. \n"
                                "To your left, you can open up the drawing tools. \n \n "
                                "Feel free to click around and see what can be done.")
        self.setIcon(QMessageBox.Information)

