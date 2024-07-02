from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer

class StatusBar(QWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = QHBoxLayout()

        self.setLayout(self.layout)

        self.label_msg = QLabel()
        self.label_msg.hide()

        self.label_filename = QLabel()
        self.label_filesize = QLabel()
        self.label_file_page_count = QLabel()
        self.label_current_page = QLabel()

        self.layout.addWidget(self.label_msg)
        self.layout.addWidget(self.label_filename, 1)
        self.layout.addWidget(self.label_filesize)
        self.layout.addWidget(self.label_current_page)
        self.layout.addWidget(self.label_file_page_count)

        self.setFixedHeight(30)

    def message(self, msg: str, sec: int) -> None:
        self.label_msg.show()
        self.label_msg.setText(msg)

        QTimer.singleShot(sec * 1000, lambda: self.label_msg.hide())

    def setFileName(self, filename: str) -> None:
        self.label_filename.setText(filename)

    def setFileSize(self, filesize: str) -> None:
        self.label_filesize.setText(filesize)

    def setFilePageCount(self, pagen: str) -> None:
        self.label_file_page_count.setText(pagen)

    def setCurrentPage(self, pagen: str) -> None:
        self.label_current_page.setText(pagen)
