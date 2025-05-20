import os, shutil
from pathlib import Path
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from model import RLIClient, ImageProcessingWorker, ImageFetchWorker
from view import MainWindow
from tiled_processor import TiledYOLOProcessor  


class AppController:
    def __init__(self, view: MainWindow):
        self.view = view
        self.client = RLIClient()
        self.models = {
            "наземные объекты": TiledYOLOProcessor('weights/nano960-9.pt', tile_size=4000, imgsz=960, overlap=100),
            "большие надводные объекты": TiledYOLOProcessor('weights/medium_ships.pt', tile_size=800, imgsz=800, overlap=100),
            "малые надводные объекты": TiledYOLOProcessor('weights/bkr.pt', tile_size=256, imgsz=256, overlap=50),
        }
        self.model = self.models["наземные объекты"]
        self.conf = self.view.horizontalSlider.value() / 100
        self.image_files = []
        self._connect_signals()

    def _connect_signals(self):
        self.view.detect_btn_2.clicked.connect(self.detect_clicked)
        self.view.open_btn_2.clicked.connect(self.select_directory)
        self.view.save_btn_2.clicked.connect(self.save_file)
        self.view.start_btn.clicked.connect(self.start_client)
        self.view.horizontalSlider.valueChanged.connect(self.update_conf)
        self.view.buttonGroup.buttonClicked.connect(self.update_model)
        self.view.detected_chbox.clicked.connect(self.view.toggle_image_mode)
        self.view.tableWidget.image_changes.connect(self.show_image)
        self.client.receive_data_percent.connect(self.view.update_progress)

    def start_client(self):
        try:
            self.view.set_ui_enabled(False)
            self.view.progress_bar.setVisible(True)
            self.view.progress_bar.setValue(0)
            self.view.statusBar().showMessage("Подключение к серверу...")

            self.fetch_worker = ImageFetchWorker(
                self.client,
                self.view.host_label.text(),
                int(self.view.port_label.text()),
                int(self.view.size_x_label.text()),
                int(self.view.size_y_label.text())
            )

            self.fetch_worker.finished.connect(self.on_fetch_finished)
            self.fetch_worker.finished.connect(self.cleanup_worker)
            self.fetch_worker.error.connect(self.view.show_error)

            self.fetch_worker.finished.connect(self.fetch_worker.deleteLater)
            self.fetch_worker.start()

        except Exception as e:
            self.view.show_error(f"Ошибка: {str(e)}")
            self.view.set_ui_enabled(True)
            self.view.progress_bar.setVisible(False)

    def on_fetch_finished(self, file_name):
        self.view.statusBar().showMessage("Обработка изображения...")

        self.worker = ImageProcessingWorker(
            self.model,
            [f'client_image/{file_name}'],
            self.conf
        )
        self.worker.file_processed.connect(lambda f, d: self.view.tableWidget.add_row(f, d))
        self.worker.finished.connect(self.on_client_processing_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()
        
    def cleanup_worker(self):
        if self.fetch_worker:
            self.fetch_worker.quit()
            self.fetch_worker.wait()   
            self.fetch_worker.deleteLater()
            self.fetch_worker = None

    def _run_client_connection(self):
        try:
            self.client.set_connect(self.view.host_label.text(), int(self.view.port_label.text()))
            if not self.client.connect():
                self.view.show_error("Не удалось подключиться к серверу")
                return
            if not self.client.send_mode(int(self.view.size_x_label.text()), int(self.view.size_y_label.text())):
                self.view.show_error("Ошибка отправки параметров")
                return

            result = self.client.receive_data()
            if not result:
                self.view.show_error("Ошибка получения данных")
                return

            params, raw_file = result

            tiff_file = Path(raw_file).with_suffix('.tiff')
            file_name = self.client.raw_to_tiff(raw_file, str(tiff_file), params.size_x, params.mode_rli)
            if not file_name:
                self.view.show_error("Ошибка конвертации")
                return


            worker = ImageProcessingWorker(self.model, [f'client_image/{file_name}'], self.conf)
            worker.file_processed.connect(lambda f, d: self.view.tableWidget.add_row(f, d))
            worker.finished.connect(self.on_client_processing_finished)
            worker.start()
        finally:
            self.client.disconnect()

    def on_client_processing_finished(self):
        self.view.detect_btn_2.setEnabled(True)
        self.image_files = self.view.get_images_in_directory(os.getcwd() + '/client_image/')
        self.view.set_ui_enabled(True)
        self.view.progress_bar.setVisible(False)
        self.view.statusBar().showMessage("Готово", 3000)

    def detect_clicked(self):
        if not hasattr(self, 'image_files') or not self.image_files:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите директорию с изображениями")
            return

        self.view.detected_chbox.setEnabled(True)
        self.view.set_ui_enabled(False)

        self.current_worker = ImageProcessingWorker(
            self.model, 
            self.image_files, 
            self.conf
        )

        self.current_worker.progress_updated.connect(self.view.update_progress)
        self.current_worker.file_processed.connect(self.view.tableWidget.update_value)
        self.current_worker.finished.connect(self.on_processing_finished)
        self.current_worker.error_occurred.connect(self.view.show_error)

        self.current_worker.finished.connect(self.current_worker.deleteLater)

        self.view.progress_bar.setVisible(True)
        self.view.progress_bar.setValue(0)

        self.current_worker.start()


    def on_processing_finished(self):
        self.view.set_ui_enabled(True)
        self.view.progress_bar.setVisible(False)
        self.view.statusBar().showMessage("Обработка завершена", 3000)

    def save_file(self):
        directory = QFileDialog.getExistingDirectory(self.view, "Выберите директорию", "")
        if directory:
            for file in os.listdir('tmp'):
                shutil.copy2(f'tmp/{file}', directory)

    def show_image(self, msg):
        if self.view.image_mode_detected:
            self.view.graphicsView.set_image(f'tmp/detected_{msg}')
        else:
            for name in self.image_files:
                if name.endswith(msg):
                    self.view.graphicsView.set_image(name)
                    return

    def update_model(self, btn):
        self.model = self.models.get(btn.text(), self.model)

    def update_conf(self, value):
        self.conf = value / 100
        self.view.slider_lbl_2.setText(f"Порог доверия: {value / 100}")

    def select_directory(self):
        directory = QFileDialog.getExistingDirectory(self.view, "Выберите директорию", "")
        if directory:
            self.view.tableWidget.clearContents()
            self.view.tableWidget.setRowCount(0)
            self.view.detected_chbox.setChecked(False)
            self.view.image_mode_detected = False
            self.image_files = self.view.get_images_in_directory(directory)
            self.view.tableWidget.fill_table([os.path.basename(f) for f in self.image_files])
            self.view.detected_chbox.setEnabled(False)
