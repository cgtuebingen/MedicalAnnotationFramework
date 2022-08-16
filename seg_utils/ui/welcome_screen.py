from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt


class WelcomeScreen(QWidget):
    def __init__(self):
        super(WelcomeScreen, self).__init__()

        self.label = QLabel()
        self.label.setText("Welcome to the \n \n"
                           "All-Purpose Labeling Tool \n \n \n"
                           "Create or open a project to get started")
        self.label.setFont(QFont("Helvetica", 20, QFont.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("background-image: url(icons/welcome.jpg); "
                                 "background-repeat: no-repeat;"
                                 "background-position: center;")

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.label)
