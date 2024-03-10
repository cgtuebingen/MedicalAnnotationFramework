from PySide6.QtGui import *
from taplt.utils.qt import get_icon


class Action(QAction):
    """Create an Action"""
    def __init__(self,
                 parent,
                 text,
                 event=None,
                 shortcut=None,
                 icon=None,
                 tip=None,
                 checkable=False,
                 checked=False,
                 ):
        super(Action, self).__init__(text, parent)
        if icon is not None:
            self.setIconText(text.replace(" ", "\n"))
            self.setIcon(get_icon(icon))
        if shortcut is not None:
            if isinstance(shortcut, (list, tuple)):
                self.setShortcuts(shortcut)
            else:
                self.setShortcut(shortcut)
        if tip is not None:
            self.setToolTip(tip)
            self.setStatusTip(tip)
        if event is not None:
            self.triggered.connect(event)
        if checkable:
            self.setCheckable(True)
            self.setChecked(checked)
