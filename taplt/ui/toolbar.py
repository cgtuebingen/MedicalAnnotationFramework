from PyQt6.QtWidgets import *
from PyQt6.QtCore import *

from typing import *

from taplt.src.actions import Action


class Toolbar(QToolBar):

    sCreateNewProject = pyqtSignal(str, dict)
    sOpenProject = pyqtSignal(str)
    sRequestPatients = pyqtSignal()

    def __init__(self, parent):
        super(Toolbar, self).__init__(parent)
        self.actionsDict = {}  # This is a lookup table to match the buttons to the numbers they got added

        self.setMinimumSize(QSize(80, 100))
        self.setMaximumSize(QSize(80, 16777215))
        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color: rgb(186, 189, 182);")
        self.setMovable(False)
        self.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.setObjectName("toolBar")
        self.button_group = QButtonGroup()
        self.button_group.setExclusive(True)
        self.button_group.buttonToggled.connect(self.exclusive_optional)
        self.modality_dict = {}
        self.current_modality = ""

    def disable_drawing(self, disable: bool):
        [btn.setDisabled(disable) for btn in self.button_group.buttons()]

    def exclusive_optional(self, btn: QToolButton):
        [x.setChecked(False) for x in self.button_group.buttons() if x != btn]

    def addAction(self, action: Action):
        r"""Because I want a physical button in the toolbar, i need to create a widget"""
        if isinstance(action, QWidgetAction):
            return super(Toolbar, self).addAction(action)
        btn = QToolButton()
        # btn.setAutoRaise(True)
        btn.setCheckable(action.isCheckable())
        if action.isCheckable():
            self.button_group.addButton(btn)
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        btn.setMinimumSize(80, 70)
        btn.setMaximumSize(80, 70)
        self.addWidget(btn)

        action_text = action.text().replace('\n', '')
        self.actionsDict[action_text] = len(self.actionsDict)

    def addActions(self, actions: Iterable[Action]) -> None:
        for action in actions:
            if action is None:
                self.addSeparator()
            else:
                self.addAction(action)

    def contextMenuEvent(self, event) -> None:
        if "DrawPolygon" in self.actionsDict:
            if self.actionGeometry(self.actions()[self.actionsDict["DrawPolygon"]]).contains(event.pos()):
                # TODO: raise own context menu with options for drawing a circle or a rectangle
                pass

    def init_actions(self, modality_name: str, actions: list[Action]):
        """Initialise all actions present which can be connected to buttons or menu items"""
        self.modality_dict[modality_name] = actions


    def get_action(self, action_str: str) -> Action:
        if action_str not in self.actionsDict:
            raise AttributeError(f"Action '{action_str}' not available. Available actions are"
                                 f"\n{[act for act in self.actionsDict.keys()]}")
        else:
            return self.widgetForAction(self.actions()[self.actionsDict[action_str]]).defaultAction()

    def get_widget_for_action(self, action_str: str):
        if action_str not in self.actionsDict:
            raise AttributeError(f"Action '{action_str}' not available. Available actions are"
                                 f"\n{[act for act in self.actionsDict.keys()]}")
        else:
            return self.widgetForAction(self.actions()[self.actionsDict[action_str]])

    def init_margins(self):
        """This function is necessary because the call to addToolBar in label_ui.py alters the alignment
        for some reason. Therefore, this method will be called AFTER the toolbar is added to the main window"""
        m = (0, 0, 0, 0)
        self.setContentsMargins(*m)
        self.layout().setSpacing(2)
        self.layout().setContentsMargins(*m)

    def switch_modality(self, modality_name: str):
        """
        This method is called, when the modality of the viewing widget is changed. All current actions will be removed
        from the toolbar and all actions that are stored in the ``modality_dict`` at the given ``modality_name`` are
        initialized.

        :param modality_name: Is a string that has the name of the modality that we want to switch to.

        :returns: Nothing or an error, if the modality does not exist/was not initialized.
        """
        # print('switching')
        if self.current_modality != modality_name:
            self.clear_actions()

            if modality_name not in self.modality_dict:
                RuntimeError("The modality does not exist/was not initialized yet.")

            self.current_modality = modality_name
            self.addActions(self.modality_dict[modality_name])

    def clear_actions(self):
        """
        This method removes all actions that are currently active, from the toolbar.
        """
        while self.button_group.buttons():
            button = self.button_group.buttons()[0]
            self.button_group.removeButton(button)
            button.deleteLater()

        self.actionsDict.clear()
