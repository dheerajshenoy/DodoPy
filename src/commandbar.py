from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import QTimer, pyqtSignal

class CommandBar(QWidget):

    searchSignal = pyqtSignal(str)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = QHBoxLayout()

        self.label_prompt = QLabel()
        self.input = QLineEdit()

        self.setLayout(self.layout)
        
        self.layout.addWidget(self.label_prompt)
        self.layout.addWidget(self.input)

        self.hide()

        self.setFixedHeight(30)

        self.input.returnPressed.connect(lambda: self.returnPressed())

    def returnPressed(self) -> None:
        self.searchSignal.emit(self.input.text())
        self.hide()

    def search(self) -> None:
        self.show()
        self.input.selectAll()
        self.label_prompt.setText("Search: ")
        self.input.setFocus()
