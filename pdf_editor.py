import sys
from collections import defaultdict
import logging

import fitz  # PyMuPDF
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QGraphicsView,
    QGraphicsScene,
    QAction,
    QToolBar,
)
from PyQt5.QtGui import QImage, QPixmap, QPen
from PyQt5.QtCore import Qt, QPointF, QRectF


logging.basicConfig(
    filename="pdf_editor.log",
    level=logging.DEBUG,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PDFGraphicsView(QGraphicsView):
    """Graphics view that supports drawing shapes."""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self._parent = parent
        self._drawing = False
        self._start = QPointF()
        self._temp_item = None

    def mousePressEvent(self, event):
        if self._parent.current_tool is None:
            return super().mousePressEvent(event)
        self._drawing = True
        self._start = self.mapToScene(event.pos())
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drawing:
            end = self.mapToScene(event.pos())
            if self._temp_item:
                self.scene().removeItem(self._temp_item)
            pen = QPen(Qt.red, 2)
            tool = self._parent.current_tool
            if tool == "line":
                self._temp_item = self.scene().addLine(
                    self._start.x(), self._start.y(), end.x(), end.y(), pen
                )
            elif tool == "rect":
                rect = QRectF(self._start, end).normalized()
                self._temp_item = self.scene().addRect(rect, pen)
            elif tool == "ellipse":
                rect = QRectF(self._start, end).normalized()
                self._temp_item = self.scene().addEllipse(rect, pen)
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drawing:
            end = self.mapToScene(event.pos())
            pen = QPen(Qt.red, 2)
            tool = self._parent.current_tool
            if self._temp_item:
                self.scene().removeItem(self._temp_item)
            if tool == "line":
                self.scene().addLine(
                    self._start.x(), self._start.y(), end.x(), end.y(), pen
                )
                self._parent.add_shape(
                    "line", (self._start.x(), self._start.y(), end.x(), end.y())
                )
            elif tool == "rect":
                rect = QRectF(self._start, end).normalized()
                self.scene().addRect(rect, pen)
                self._parent.add_shape(
                    "rect",
                    (rect.left(), rect.top(), rect.right(), rect.bottom()),
                )
            elif tool == "ellipse":
                rect = QRectF(self._start, end).normalized()
                self.scene().addEllipse(rect, pen)
                self._parent.add_shape(
                    "ellipse",
                    (rect.left(), rect.top(), rect.right(), rect.bottom()),
                )
        self._drawing = False
        self._temp_item = None
        return super().mouseReleaseEvent(event)


class PDFEditor(QMainWindow):
    """Minimal PDF viewer/editor supporting basic drawing."""

    def __init__(self):
        super().__init__()
        self.doc = None
        self.current_page = 0
        self.current_tool = None
        self.shapes = defaultdict(list)  # page number -> list of shapes

        self.scene = QGraphicsScene()
        self.view = PDFGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self._create_actions()
        logger.debug("PDFEditor initialized")

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _create_actions(self):
        open_act = QAction("Open", self)
        open_act.triggered.connect(self.open_file)

        save_act = QAction("Save As", self)
        save_act.triggered.connect(self.save_file)

        prev_act = QAction("Prev", self)
        prev_act.triggered.connect(self.prev_page)

        next_act = QAction("Next", self)
        next_act.triggered.connect(self.next_page)

        line_act = QAction("Line", self, checkable=True)
        line_act.triggered.connect(lambda: self.set_tool("line"))

        rect_act = QAction("Rectangle", self, checkable=True)
        rect_act.triggered.connect(lambda: self.set_tool("rect"))

        ell_act = QAction("Ellipse", self, checkable=True)
        ell_act.triggered.connect(lambda: self.set_tool("ellipse"))

        toolbar = QToolBar()
        toolbar.addAction(open_act)
        toolbar.addAction(save_act)
        toolbar.addAction(prev_act)
        toolbar.addAction(next_act)
        toolbar.addAction(line_act)
        toolbar.addAction(rect_act)
        toolbar.addAction(ell_act)
        self.addToolBar(toolbar)

        self.tool_actions = [line_act, rect_act, ell_act]

    def set_tool(self, name):
        self.current_tool = name
        for action in self.tool_actions:
            action.setChecked(action.text().lower() == name)
        logger.debug("Tool set to %s", name)

    # ------------------------------------------------------------------
    # Core functionality
    # ------------------------------------------------------------------
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if not path:
            logger.info("Open file cancelled")
            return
        try:
            self.doc = fitz.open(path)
            self.current_page = 0
            logger.info("Opened PDF '%s' with %d pages", path, self.doc.page_count)
            self.load_page()
        except Exception:
            logger.exception("Failed to open PDF %s", path)

    def load_page(self):
        if self.doc is None:
            logger.warning("load_page called with no document")
            return
        try:
            page = self.doc[self.current_page]
            pix = page.get_pixmap()
            image_format = (
                QImage.Format_RGBA8888 if pix.n >= 4 else QImage.Format_RGB888
            )
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, image_format)
            if image_format == QImage.Format_RGB888:
                img = img.rgbSwapped()
            pixmap = QPixmap.fromImage(img)
            self.scene.clear()
            self.scene.setSceneRect(0, 0, pix.width, pix.height)
            self.scene.addPixmap(pixmap)
            logger.debug("Loaded page %d", self.current_page + 1)
        except Exception:
            logger.exception("Failed to load page %d", self.current_page)
            return

        # redraw existing shapes for page
        for typ, data in self.shapes[self.current_page]:
            pen = QPen(Qt.red, 2)
            if typ == "line":
                x1, y1, x2, y2 = data
                self.scene.addLine(x1, y1, x2, y2, pen)
            elif typ == "rect":
                x1, y1, x2, y2 = data
                rect = QRectF(x1, y1, x2 - x1, y2 - y1)
                self.scene.addRect(rect, pen)
            elif typ == "ellipse":
                x1, y1, x2, y2 = data
                rect = QRectF(x1, y1, x2 - x1, y2 - y1)
                self.scene.addEllipse(rect, pen)

        self.setWindowTitle(f"PDF Editor - Page {self.current_page + 1}/{self.doc.page_count}")

    def add_shape(self, typ, data):
        self.shapes[self.current_page].append((typ, data))
        logger.debug(
            "Added shape %s with data %s on page %d",
            typ,
            data,
            self.current_page + 1,
        )

    def next_page(self):
        if self.doc and self.current_page + 1 < self.doc.page_count:
            self.current_page += 1
            logger.debug("Navigated to next page %d", self.current_page + 1)
            self.load_page()
        else:
            logger.info("Next page requested but at end or no document")

    def prev_page(self):
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            logger.debug("Navigated to previous page %d", self.current_page + 1)
            self.load_page()
        else:
            logger.info("Previous page requested but at beginning or no document")

    def save_file(self):
        if self.doc is None:
            logger.warning("save_file called with no document")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF Files (*.pdf)")
        if not path:
            logger.info("Save file cancelled")
            return
        try:
            for page_number, shapes in self.shapes.items():
                page = self.doc[page_number]
                for typ, data in shapes:
                    if typ == "line":
                        x1, y1, x2, y2 = data
                        page.draw_line((x1, y1), (x2, y2), color=(1, 0, 0), width=2)
                    elif typ == "rect":
                        x1, y1, x2, y2 = data
                        page.draw_rect([x1, y1, x2, y2], color=(1, 0, 0), width=2)
                    elif typ == "ellipse":
                        x1, y1, x2, y2 = data
                        page.draw_oval([x1, y1, x2, y2], color=(1, 0, 0), width=2)
            self.doc.save(path)
            logger.info("Saved PDF as %s", path)
        except Exception:
            logger.exception("Failed to save PDF %s", path)


def main():
    logger.info("Application started")
    app = QApplication(sys.argv)
    editor = PDFEditor()
    editor.resize(800, 600)
    editor.show()
    exit_code = app.exec_()
    logger.info("Application exited with code %s", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
