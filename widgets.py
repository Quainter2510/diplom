import os
import shutil

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QBrush
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem, \
    QGraphicsView, QGraphicsScene

from models import *


class TableWidget(QTableWidget):
    image_changes = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cellDoubleClicked.connect(self.on_cell_double_clicked)

    def fill_table(self, file_names):
        self.setRowCount(len(file_names))  # Устанавливаем количество строк
        for i, file_name in enumerate(file_names):
            self.setItem(i, 0, QTableWidgetItem(file_name))
            self.setItem(i, 1, QTableWidgetItem("Не определено"))
            self.item(i, 0).setFlags(Qt.ItemIsEnabled)
            self.item(i, 1).setFlags(Qt.ItemIsEnabled)

    def update_value(self, file_name, value):
        row_count = self.rowCount()
        for i in range(row_count):
            current_file_name = self.item(i, 0).text()
            if current_file_name == file_name:
                self.setItem(i, 1, QTableWidgetItem(str(value)))
                return

    def on_cell_double_clicked(self, row, _):
        current_filename = self.item(row, 0).text()
        self.image_changes.emit(current_filename)


class MyGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

    def set_img(self, img_path):
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            self.scene.setBackgroundBrush(QBrush(pixmap))


class MainWindow(QMainWindow):
    models = {
        "nano960 9 classes": Nano960_9(),
        "nano960 10 classes": Nano960_10(),
        "medium960 10 classes": Medium960_10(),
        "nano1280 9 classes": Nano1280_9(),
        "medium960 9 classes": Medium960_9(),
        "ships": Medium_ships()
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
        self.model = self.models.get("nano960 9 classes")
        self.conf = self.horizontalSlider.value() / 100

        self.setAcceptDrops(True)

        # self.detect_btn_2.clicked.connect(self.detect_clicked)
        self.open_btn_2.clicked.connect(self.select_directory)
        self.save_btn_2.clicked.connect(self.saveFileNameDialog)
        self.horizontalSlider.valueChanged.connect(self.update_conf)
        self.buttonGroup.buttonClicked.connect(self.update_model)
        self.buttonGroup_2.buttonClicked.connect(self.swap_mode)

        self.tableWidget.image_changes.connect(self.show_image)

    # def detect_clicked(self):
    #     self.detected.setEnabled(True)
    #     for image_path in self.image_files:
    #         results = self.model.predict(image_path, self.conf)
    #         for r in results:
    #             img_bgr = r.plot(font_size=40, line_width=8)
    #             h, w, _ = img_bgr.shape
    #             self.current_pixmap = QPixmap(QImage(img_bgr.data, w, h, 3 * w, QImage.Format_RGB888))
    #             self.image_view.update_image(self.current_pixmap)
    #             self.file_table.update_value(os.path.basename(image_path), len(r.boxes))
    #             self.current_pixmap.save(f'tmp/detected_{os.path.basename(image_path)}')


    def update_conf(self, value):
        self.conf = value / 100
        self.slider_lbl_2.setText(f"Порог доверия: {value / 100}")

    def update_model(self, object):
        return self.models.get(object.text(), None)

    def swap_mode(self, object):
        self.image_mode_detected = (object.text() == 'detected')


    # def dragEnterEvent(self, event: QDragEnterEvent):
    #     if event.mimeData().hasUrls():
    #         event.accept()
    #     else:
    #         event.ignore()
    #
    # def dropEvent(self, event: QDropEvent):
    #     self.file_path = event.mimeData().urls()[0].toLocalFile()
    #     self.current_pixmap = QPixmap(self.file_path)
    #     self.image_view.update_image(self.current_pixmap)


    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Выберите директорию", "")
        if self.directory:
            self.image_files = self.get_images_in_directory(self.directory)
            self.tableWidget.fill_table([os.path.basename(image_name) for image_name in self.image_files])
            self.detected_2.setEnabled(False)
            self.no_detected_2.setChecked(True)

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
            self.graphicsView.set_img(f'tmp/detected_{msg}')
        else:
            for name in self.image_files:
                if name.endswith(msg):
                    self.graphicsView.set_img(name)
                    return

    def closeEvent(self, a0):
        abspath = os.path.abspath('tmp/')
        for elem in os.listdir('tmp'):
            os.remove(os.path.join(abspath, elem))
        super().closeEvent(a0)
