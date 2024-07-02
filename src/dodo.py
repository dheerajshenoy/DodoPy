from PyQt6.QtWidgets import (QFileDialog, QInputDialog, QMainWindow, QApplication, QStyle, QLineEdit,
                            QLabel, QMessageBox, QScrollArea, QScrollBar, QVBoxLayout, QWidget, 
                            QMenuBar, QMenu)
from PyQt6.QtGui import (QImage, QColor, QPen, QBrush, QPainter, QPixmap, QShortcut, QKeySequence, QAction,
                        QActionGroup)
from PyQt6.QtCore import Qt, QFileInfo, QLocale, QRectF

from statusbar import StatusBar
from commandbar import CommandBar

from enum import Enum

import pymupdf as mupdf
import sys
import os

# Direction enum
class Direction(Enum):
    DOWN = 0
    UP = 1
    LEFT = 2
    RIGHT = 3

class AnnotationType(Enum):
    UNDERLINE = 0,
    SQUIGGLE = 1,
    STRIKETHROUGH = 2,
    HIGHLIGHT = 3,

class Dodo(QMainWindow):

    cur_page_num = -1
    total_page_count = -1
    rotate = 0
    zoom = 1.0
    searchText = ""
    searchIndex = -1
    searchCount = 0
    annotType = AnnotationType.HIGHLIGHT
    annotColor = (255, 255, 0)



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
        
        self.vscroll = self.scrollArea.verticalScrollBar()
        self.hscroll = self.scrollArea.horizontalScrollBar()

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
        self.__handle_menubar()
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
                self.statusbar.setFileName(filename)
                locale = self.locale()
                self.statusbar.setFilePageCount(str(self.total_page_count))
                self.statusbar.setFileSize(locale.formattedDataSize(QFileInfo(filename).size()));
                self.__readFile(filename)
        else:
            self.__readFile(filename)
        self.statusbar.setFileName(filename)
        locale = self.locale()
        self.statusbar.setFilePageCount(str(self.total_page_count))
        self.statusbar.setFileSize(locale.formattedDataSize(QFileInfo(filename).size()));

    def __handle_shortcuts(self):

        # TOC
        self.kb_toc = QShortcut(QKeySequence("Tab"), self)
        self.kb_toc.activated.connect(lambda: self.toggleTOC())

        # First Page
        self.kb_first_page = QShortcut(QKeySequence("g,g"), self)
        self.kb_first_page.activated.connect(lambda: self.gotoPage(0))

        # Last Page
        self.kb_last_page = QShortcut(QKeySequence("Shift+g"), self)
        self.kb_last_page.activated.connect(lambda: self.gotoPage(self.total_page_count - 1))

        # Scroll Down
        self.kb_scroll_down = QShortcut(QKeySequence("j"), self)
        self.kb_scroll_down.activated.connect(lambda: self.scrollVertical(Direction.DOWN, 30))

        # Scroll More Down
        self.kb_scroll_more_down = QShortcut(QKeySequence("Ctrl+d"), self)
        self.kb_scroll_more_down.activated.connect(lambda: self.scrollVertical(Direction.DOWN, 300))

        # Scroll Up
        self.kb_scroll_up = QShortcut(QKeySequence("k"), self)
        self.kb_scroll_up.activated.connect(lambda: self.scrollVertical(Direction.UP, 30))

        # Scroll More Up
        self.kb_scroll_more_up = QShortcut(QKeySequence("Ctrl+u"), self)
        self.kb_scroll_more_up.activated.connect(lambda: self.scrollVertical(Direction.UP, 300))


        # Scroll Left
        self.kb_scroll_left = QShortcut(QKeySequence("h"), self)
        self.kb_scroll_left.activated.connect(lambda: self.scrollHorizontal(Direction.LEFT, 30))

        # Scroll Right
        self.kb_scroll_right = QShortcut(QKeySequence("l"), self)
        self.kb_scroll_right.activated.connect(lambda: self.scrollHorizontal(Direction.RIGHT, 30))

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
            passwd, ok = QInputDialog(self).getText(self, "Document Encrypted", "Enter password: ")
            if ok and passwd:
                self.doc.authenticate(passwd)
            else:
                QMessageBox.information(self, "Error opening file", "Provided password was incorrect")
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

        self.statusbar.setCurrentPage(str(p + 1))

        self.cur_page_num = p
        self.render()

    def getCurrentPageNumber(self) -> int:
        return self.cur_page_num

    def render(self) -> None:
        self.page = self.doc[self.getCurrentPageNumber()]
        self.page.set_rotation(self.rotate)
        self.pix = self.page.get_pixmap(matrix = mupdf.Matrix(self.zoom, self.zoom))
        fmt = QImage.Format.Format_RGBA8888 if self.pix.alpha else QImage.Format.Format_RGB888
        self.image = QImage(self.pix.samples_ptr, self.pix.width, self.pix.height, self.pix.stride, fmt)

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
        quads = self.page.search_for(text, quads=True)

        if quads == None:
            return

        if len(quads) == 0:
            return

        for quad in quads:

            self.painter = QPainter(self.gimage)

            pen = QPen()
            pen.setStyle(Qt.PenStyle.NoPen)
            self.painter.setPen(pen)

            width = quad.lr.x - quad.ul.x;
            height = quad.lr.y - quad.ul.y;

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
                    label_height = height * self.zoom

                case 270 | -90:
                    label_width = height * self.zoom
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

    def scrollVertical(self, direction: Direction, amount: float) -> None:

        match(direction):
            case Direction.UP:
                self.vscroll.setValue(self.vscroll.value() - amount)

            case Direction.DOWN:
                self.vscroll.setValue(self.vscroll.value() + amount)

    def scrollHorizontal(self, direction: Direction, amount: float) -> None:
        if direction == Direction.LEFT:
            self.hscroll.setValue(self.hscroll.value() - amount)
        elif direction == Direction.RIGHT:
            self.hscroll.setValue(self.hscroll.value() + amount)

    def toggleTOC(self):
        if (self.doc):
            self.toc = self.doc.get_toc()

    def annotate(self, quad):
        self.page.add_squiggly_annot(quad)

    def __handle_menubar(self):
        self.menubar = QMenuBar()
        self.setMenuBar(self.menubar)

        self.menu_file = QMenu("File")
        self.menu_edit = QMenu("Edit")
        self.menu_view = QMenu("View")

        self.action_open_file = QAction("Open")
        self.menu_open_recent_file = QMenu("Open Recent")
        self.action_exit = QAction("Exit")

        self.menu_file.addAction(self.action_open_file)
        self.menu_file.addMenu(self.menu_open_recent_file)
        self.menu_file.addAction(self.action_exit)

        self.menu_fit = QMenu("Fit")

        self.menu_fit_action_group = QActionGroup(self)

        self.action_fit_width = QAction("Width")
        self.action_fit_height = QAction("Height")

        self.action_fit_width.setCheckable(True)
        self.action_fit_height.setCheckable(True)

        self.menu_fit.addAction(self.action_fit_width)
        self.menu_fit.addAction(self.action_fit_height)

        self.menu_view.addMenu(self.menu_fit)

        self.menu_fit_action_group.addAction(self.action_fit_width)
        self.menu_fit_action_group.addAction(self.action_fit_height)

        self.action_fit_width.triggered.connect(lambda: self.fitToWidth())
        self.action_fit_height.triggered.connect(lambda: self.fitToHeight())

        self.action_open_file.triggered.connect(lambda: self.Open())

        self.action_pref = QAction("Preferences")

        self.menu_edit.addAction(self.action_pref)

        self.menubar.addMenu(self.menu_file)
        self.menubar.addMenu(self.menu_edit)
        self.menubar.addMenu(self.menu_view)

    def fitToWidth(self) -> None:
        self.zoom = self.label.width() / self.pix.w
        self.render()

    def fitToHeight(self) -> None:
        self.zoom = self.label.height() / self.pix.h
        self.render()
