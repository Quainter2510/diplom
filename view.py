import os
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QProgressBar, QMessageBox
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPixmap, QWheelEvent, QMouseEvent


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('untitled.ui', self)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)

        self.image_mode_detected = False
        self.current_worker = None
        
        self.splitter.setStretchFactor(0, 1) 
        self.splitter.setStretchFactor(1, 0)
        
    def set_ui_enabled(self, enabled):
        self.detect_btn_2.setEnabled(enabled)
        self.open_btn_2.setEnabled(enabled)
        self.save_btn_2.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.horizontalSlider.setEnabled(enabled)
        for btn in self.buttonGroup.buttons():
            btn.setEnabled(enabled)
        self.detected_chbox.setEnabled(enabled)
        
    def update_progress(self, progress: int, filename: str):
        self.progress_bar.setValue(progress)
        if filename:
            self.statusBar().showMessage(f"Обработка: {filename}")
        else:
            self.statusBar().showMessage("Обработка завершена")

    def toggle_image_mode(self):
        self.image_mode_detected = not self.image_mode_detected
        self.detected_chbox.setChecked(self.image_mode_detected)

    def get_images_in_directory(self, directory):
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}
        return [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if os.path.splitext(file)[1].lower() in image_extensions
        ]

    def show_error(self, message):
        QMessageBox.warning(self, "Ошибка", message)

    def closeEvent(self, a0):
        for elem in os.listdir('tmp'):
            os.remove(os.path.join(os.path.abspath('tmp/'), elem))
        super().closeEvent(a0)


class TableWidget(QTableWidget):
    image_changes = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.setEditTriggers(QTableWidget.NoEditTriggers)

    def fill_table(self, file_names):
        for file_name in file_names:
            self.add_row(file_name)
            
    def add_row(self, file_name, value="Не определено"):
        row = self.rowCount()
        self.insertRow(row)
        print(file_name)
        self.setItem(row, 0, QTableWidgetItem(file_name))
        self.setItem(row, 1, QTableWidgetItem(str(value)))
        self.item(row, 0).setFlags(Qt.ItemIsEnabled)
        self.item(row, 1).setFlags(Qt.ItemIsEnabled)

    def update_value(self, file_name, value):
        row_count = self.rowCount()
        for i in range(row_count):
            current_file_name = self.item(i, 0).text()
            if current_file_name == file_name:
                self.setItem(i, 1, QTableWidgetItem(str(value)))
                return

    def on_cell_double_clicked(self, row, col):
        current_filename = self.item(row, 0).text()
        self.image_changes.emit(current_filename)


class MyGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self._pan_start = QPointF()
        self._panning = False
        
        # Настройки масштабирования
        self.zoom_factor = 1.25
        self.min_zoom = 0.1
        self.max_zoom = 20.0
        self.current_scale = 1.0

    def set_image(self, image_path):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Ошибка загрузки изображения")
            return
            
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))  
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        self.current_scale = 1.0

    def wheelEvent(self, event: QWheelEvent):
        zoom_in = event.angleDelta().y() > 0
        
        if zoom_in and self.current_scale < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.current_scale *= self.zoom_factor
        elif not zoom_in and self.current_scale > self.min_zoom:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            self.current_scale /= self.zoom_factor

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self._pan_start = event.pos()
            self._panning = True
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.RightButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

