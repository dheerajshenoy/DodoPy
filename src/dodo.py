from re import A
from PyQt6.QtWidgets import (QFileDialog, QInputDialog, QMainWindow, QApplication,
                            QLabel, QMessageBox, QScrollArea, QScrollBar, QVBoxLayout, QWidget)
from PyQt6.QtGui import (QImage, QColor, QPen, QBrush, QPainter, QPixmap, QShortcut, QKeySequence)
from PyQt6.QtCore import Qt, QFileInfo, QLocale, QRectF

from statusbar import StatusBar
from commandbar import CommandBar

import pymupdf as mupdf
import sys
import os

class Dodo(QMainWindow):

    cur_page_num = -1
    total_page_count = -1
    rotate = 0
    zoom = 1.0
    searchText = ""
    searchIndex = -1
    searchCount = 0


    def __init__(self, *args, **kwargs) -> None:
        super().__init__(**kwargs)

        self.arg = args[0]

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.scrollArea = QScrollArea()
        self.widget = QWidget()
        self.statusbar = StatusBar()
        self.commandbar = CommandBar()

        self.image = None


        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.label)
        self.layout.addWidget(self.scrollArea)
        self.layout.addWidget(self.statusbar)
        self.layout.addWidget(self.commandbar)
        self.widget.setLayout(self.layout)
        self.setCentralWidget(self.widget)

        self.__handle_shortcuts()
        self.commandbar.searchSignal.connect(lambda text: self.search(text))
        self.show()
        
        if len(self.arg) > 1:
            self.Open(self.arg[1])

    def Open(self, filename: str = ""):
        filename = filename.replace("~", os.getenv("HOME"))
        if filename == "":
            filename, _ = QFileDialog.getOpenFileName(self, "Open File")
            if filename == "":
                QMessageBox.information(self, "OOPS", "Could not open file")
                return
        else:
            self.__readFile(filename)
        self.statusbar.setFileName(filename)
        locale = self.locale()
        self.statusbar.setFileSize(locale.formattedDataSize(QFileInfo(filename).size()));

    def __handle_shortcuts(self):

        # Next Page
        self.kb_next_page = QShortcut(QKeySequence("Shift+j"), self)
        self.kb_next_page.activated.connect(lambda: self.nextPage())

        # Prev Page
        self.kb_prev_page = QShortcut(QKeySequence("Shift+k"), self)
        self.kb_prev_page.activated.connect(lambda: self.prevPage())

        # Zoom In
        self.kb_zoom_in = QShortcut(QKeySequence("="), self)
        self.kb_zoom_in.activated.connect(lambda: self.zoomIn(0.3))

        # Zoom Out
        self.kb_zoom_out = QShortcut(QKeySequence("-"), self)
        self.kb_zoom_out.activated.connect(lambda: self.zoomOut(0.3))

        # Search
        self.kb_search = QShortcut(QKeySequence("/"), self)
        self.kb_search.activated.connect(lambda: self.commandbar.search())

        # Rotate clock
        self.kb_rotate_clock = QShortcut(QKeySequence("."), self)
        self.kb_rotate_clock.activated.connect(lambda: self.rotatePage(90))

        # Rotate aclock
        self.kb_rotate_clock = QShortcut(QKeySequence(","), self)
        self.kb_rotate_clock.activated.connect(lambda: self.rotatePage(-90))

    def __readFile(self, filename: str):
        self.doc = mupdf.open(filename)

        if self.doc.needs_pass:
            # passwdDialog = QInputDialog(self)
            # passwd = passwdDialog.exec()
            # if not self.doc.authenticate(passwd):
            #     QMessageBox.information(self, "Error", "Wrong password")
            return

        self.total_page_count = self.doc.page_count
        self.gotoPage(0)

    def nextPage(self) -> None:
        self.gotoPage(self.getCurrentPageNumber() + 1)

    def prevPage(self) -> None:
        self.gotoPage(self.getCurrentPageNumber() - 1)

    def gotoPage(self, p: int) -> None:

        if p > self.total_page_count - 1 or p < 0:
            return

        self.statusbar.setCurrentPage(str(p))

        self.cur_page_num = p
        self.render()

    def getCurrentPageNumber(self) -> int:
        return self.cur_page_num

    def render(self) -> None:
        self.page = self.doc[self.getCurrentPageNumber()]
        self.page.set_rotation(self.rotate)
        pix = self.page.get_pixmap(matrix = mupdf.Matrix(self.zoom, self.zoom))
        fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
        self.image = QImage(pix.samples_ptr, pix.width, pix.height, pix.stride, fmt)

        if self.searchText != "":
            self.search(self.searchText)

        self.label.setPixmap(QPixmap.fromImage(self.image))

    def setZoom(self, scale: float) -> None:
        self.zoom = scale

    def zoomIn(self, factor: float) -> None:
        self.zoom += factor
        self.render()

    def zoomOut(self, factor: float) -> None:
        if self.zoom - factor < 0:
            return
        self.zoom -= factor
        self.render()

    def search(self, text: str) -> None:
        self.searchText = text
        self.gimage = self.image
        hit_box = self.page.search_for(text, quads=True)

        if hit_box == None:
            return

        if len(hit_box) == 0:
            return

        quads = hit_box


        for quad in quads:

            self.painter = QPainter(self.gimage)

            pen = QPen()
            pen.setStyle(Qt.PenStyle.NoPen)
            self.painter.setPen(pen)

            width = quad.lr.x - quad.ul.x;
            height = quad.lr.y - quad.ul.y;

            print(self.rotate)
            match(self.rotate):
                case 0:
                    label_x = quad.ll.x * self.zoom
                    label_y = quad.ul.y * self.zoom
                    label_width = width * self.zoom
                    label_height = height * self.zoom

                case 90 | -270:
                    label_width = height * self.zoom
                    label_height = width * self.zoom
                    label_x = self.label.width() - quad.ul.y * self.zoom - label_width
                    label_y = quad.ul.x * self.zoom

                case 180 | -180:
                    label_x = self.label.width() - quad.ul.x * self.zoom - width * self.zoom
                    label_y = self.label.height() - quad.ul.y * self.zoom - height * self.zoom
                    label_width = width * self.zoom
                    label_height = height  * self.zoom

                case 270 | -90:
                    label_width= height * self.zoom
                    label_height = width * self.zoom
                    label_x = quad.ul.y * self.zoom
                    label_y = self.label.height() - quad.ul.x * self.zoom - label_height

            rect = QRectF(label_x, label_y, label_width, label_height)

            self.painter.drawRect(rect)
            self.painter.fillRect(rect, QBrush(QColor(255, 0, 0, 128)))
            self.painter.end()

        self.label.setPixmap(QPixmap.fromImage(self.gimage))

    def searchReset(self) -> None:
        self.searchText = ""
        self.searchCount = 0
        self.searchIndex = -1
        self.render()

    def rotatePage(self, angle: float) -> None:
        self.rotate += angle
        self.rotate = int(self.rotate) % 360
        self.render()



