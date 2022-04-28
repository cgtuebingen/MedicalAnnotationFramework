COMMENT_LIST = """QListWidget {
                  color: rgb(0, 102, 204);
                  selection-color: blue;
                  selection-background-color: white;
                  }
                  QListWidget::item:hover {
                  color: blue;
                  } """

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
