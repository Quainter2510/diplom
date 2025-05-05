import os
import shutil

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QRectF
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem, \
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPixmap, QWheelEvent, QMouseEvent

from client import *
from tiled_processor import *


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
        self.max_zoom = 10.0
        self.current_scale = 1.0

    def set_image(self, image_path):
        """Установка изображения из файла"""
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Ошибка загрузки изображения")
            return
            
        self.pixmap_item.setPixmap(pixmap)
        # Исправлено: преобразование QRect в QRectF
        self.scene.setSceneRect(QRectF(pixmap.rect()))  
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
        self.current_scale = 1.0

    def wheelEvent(self, event: QWheelEvent):
        """Масштабирование при прокрутке колесика мыши"""
        zoom_in = event.angleDelta().y() > 0
        
        if zoom_in and self.current_scale < self.max_zoom:
            self.scale(self.zoom_factor, self.zoom_factor)
            self.current_scale *= self.zoom_factor
        elif not zoom_in and self.current_scale > self.min_zoom:
            self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            self.current_scale /= self.zoom_factor

    def mousePressEvent(self, event: QMouseEvent):
        """Начало перемещения при зажатой правой кнопке мыши"""
        if event.button() == Qt.RightButton:
            self._pan_start = event.pos()
            self._panning = True
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Перемещение изображения при зажатой правой кнопке"""
        if self._panning:
            delta = event.pos() - self._pan_start
            self._pan_start = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Окончание перемещения при отпускании правой кнопки"""
        if event.button() == Qt.RightButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    models = {
        "vvkr": TiledYOLOProcessor(model_weights='weights/nano960-9.pt',
                                                tile_size=4000,
                                                imgsz=960,
                                                overlap=100),
        "ships": TiledYOLOProcessor(model_weights='weights/medium_ships.pt',
                                                tile_size=800,
                                                imgsz=800,
                                                overlap=100),
        "bkr": TiledYOLOProcessor(model_weights='weights/medium_ships.pt',
                                        tile_size=256,
                                        imgsz=256,
                                        overlap=50)
    }
    conf: float
    file_path: str
    current_pixmap: str
    image_mode_detected: bool = False
    working_directory: str
    image_files: list

    def __init__(self):
        super().__init__()
        uic.loadUi('untitled.ui', self)
        self.model = self.models.get("vvkr")
        self.conf = self.horizontalSlider.value() / 100

        self.setAcceptDrops(True)
        
        self.client = RLIClient()

        self.detect_btn_2.clicked.connect(self.detect_clicked)
        self.open_btn_2.clicked.connect(self.select_directory)
        self.save_btn_2.clicked.connect(self.saveFileNameDialog)
        self.start_btn.clicked.connect(self.start_client)
        self.horizontalSlider.valueChanged.connect(self.update_conf)
        self.buttonGroup.buttonClicked.connect(self.update_model)
        self.detected_chbox.clicked.connect(self.on_checkbox_clicked)
        
        self.mode_0_rbtn.toggled.connect(lambda: self.on_radio_toggled(0))
        self.mode_1_rbtn.toggled.connect(lambda: self.on_radio_toggled(1))
        self.mode_2_rbtn.toggled.connect(lambda: self.on_radio_toggled(2))
        self.mode_4_rbtn.toggled.connect(lambda: self.on_radio_toggled(4))
        
        self.tableWidget.image_changes.connect(self.show_image)
        
        
    def on_checkbox_clicked(self):
        self.image_mode_detected = not self.image_mode_detected
        self.detected_chbox.setChecked(self.image_mode_detected)
       
    def on_radio_toggled(self, mode):
        if mode == 0:
            self.client.set_mode(ModeRLI.CHAR)
        elif mode == 1:
            self.client.set_mode(ModeRLI.UCHAR)
        elif mode == 2:
            self.client.set_mode(ModeRLI.USHORT)
        elif mode == 4:
            self.client.set_mode(ModeRLI.FLOAT)
        
    def set_radiobutton_enabled(self, is_enabled):
        self.mode_0_rbtn.setEnabled(is_enabled)
        self.mode_1_rbtn.setEnabled(is_enabled)
        self.mode_2_rbtn.setEnabled(is_enabled)
        self.mode_4_rbtn.setEnabled(is_enabled)
            
        
    def start_client(self):
        try:
            self.client.set_connect(self.host_label.text(), int(self.port_label.text()))
            if not self.client.connect():
                return
            if not self.client.send_mode(int(self.size_x_label.text()), int(self.size_y_label.text())):
                return
            self.set_radiobutton_enabled(False)
            result = self.client.receive_data()
            if result:
                params, raw_file = result
                print(f"\nData received successfully and saved to {raw_file}")
                print(f"Image parameters: {params}")
            
                tiff_file = Path(raw_file).with_suffix('.tiff')
                file_name = self.client.raw_to_tiff(raw_file, str(tiff_file), params.size_x, params.mode_rli)
                if file_name:
                    print(f"TIFF image saved to {file_name}")
                    _, detections = self.model.process_image(f'client_image/{file_name}')  
                    self.detected_2.setEnabled(True)
                    self.directory = os.getcwd() + '/client_image/' 
                    self.image_files = self.get_images_in_directory(self.directory)
                    self.tableWidget.add_row(file_name, detections)
                else:
                    print("Failed to convert RAW to TIFF")            
        finally:
            self.set_radiobutton_enabled(True)
            self.client.disconnect()
        

    def detect_clicked(self):
        self.detected_chbox.setEnabled(True)
        for image_path in self.image_files:
            _, detections = self.model.process_image(image_path, self.conf)
            self.tableWidget.update_value(os.path.basename(image_path), detections)

    def update_conf(self, value):
        self.conf = value / 100
        self.slider_lbl_2.setText(f"Порог доверия: {value / 100}")

    def update_model(self, object):
        return self.models.get(object.text(), None)


    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Выберите директорию", "")
        if self.directory:
            self.image_files = self.get_images_in_directory(self.directory)
            self.tableWidget.fill_table([os.path.basename(image_name) for image_name in self.image_files])
            self.detected_chbox.setEnabled(False)

    def get_images_in_directory(self, directory):
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"}
        return [
            os.path.join(directory, file)
            for file in os.listdir(directory)
            if os.path.splitext(file)[1].lower() in image_extensions
        ]

    def saveFileNameDialog(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите директорию", "")
        if directory:
            for file in os.listdir('tmp'):
                shutil.copy2(f'tmp/{file}', directory)

    def show_image(self, msg):
        if self.image_mode_detected:
            self.graphicsView.set_image(f'tmp/detected_{msg}')
        else:
            for name in self.image_files:
                if name.endswith(msg):
                    self.graphicsView.set_image(name)
                    return

    def closeEvent(self, a0):
        abspath = os.path.abspath('tmp/')
        for elem in os.listdir('tmp'):
            os.remove(os.path.join(abspath, elem))
        super().closeEvent(a0)
