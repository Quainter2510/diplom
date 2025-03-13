import sys
import os
import shutil
from image_view import ImageView
from file_table import FileTable
from models import *
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QButtonGroup, QFileDialog
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QImage, QIcon

class DropWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('practic_ui.ui', self) 
        self.model = Nano960_9()
        self.conf = self.conf_slider.value() / 100
        self.file_path = None
        self.current_pixmap = None
        self.image_mode_detected = False
        self.working_directory = ''
        self.image_files = [] 
        self.setAcceptDrops(True)
        
        
        self.buttonGroup = QButtonGroup(exclusive=True)
        self.buttonGroup.addButton(self.nano960_9, 1)
        self.buttonGroup.addButton(self.nano_960_10, 2)
        self.buttonGroup.addButton(self.medium_960_10, 3)
        self.buttonGroup.addButton(self.nano_1280_9, 4)
        self.buttonGroup.addButton(self.medium_960_9, 5)
        self.buttonGroup.addButton(self.medium_ships, 6)

        self.detected_buttonGroup = QButtonGroup(exclusive=True)
        self.detected_buttonGroup.addButton(self.detected, 1)
        self.detected_buttonGroup.addButton(self.no_detected, 2)
        self.detected.setEnabled(False)
        
        self.detect_btn.clicked.connect(self.detect_clicked)
        self.open_btn.clicked.connect(self.select_directory)
        self.save_btn.clicked.connect(self.saveFileNameDialog)
        self.conf_slider.valueChanged.connect(self.update_conf)
        self.buttonGroup.buttonClicked.connect(self.update_model) 
        self.detected_buttonGroup.buttonClicked.connect(self.swap_mode) 
        
        self.image_view = ImageView()
        self.file_table = FileTable()
        self.file_table.image_changes.connect(self.show_image) 
        
        self.image_layout.addWidget(self.image_view, 0)
        self.image_layout.addWidget(self.file_table, 1)
        self.image_layout.setStretch(0, 2)
        self.image_layout.setStretch(1, 1)
        
        
        title = "Object detector"
        self.setWindowTitle(title)     
    
    def detect_clicked(self):
        self.detected.setEnabled(True)
        for image_path in self.image_files:
            results = self.model.predict(image_path, self.conf)
            for r in results:
                img_bgr = r.plot(font_size=40, line_width=8)
                h,w,_ = img_bgr.shape
                self.current_pixmap = QPixmap(QImage(img_bgr.data, w, h, 3*w, QImage.Format_RGB888))
                self.image_view.update_image(self.current_pixmap)
                self.file_table.update_value(os.path.basename(image_path), len(r.boxes))
                self.current_pixmap.save(f'tmp/detected_{os.path.basename(image_path)}')
                
            
    def update_conf(self, value):
        self.conf = value / 100
        self.slider_lbl.setText(f"Порог доверия: {value / 100}")
           
    def update_model(self, object):
        if self.buttonGroup.id(object) == 1:
            self.model = Nano960_10()
        elif self.buttonGroup.id(object) == 2:
            self.model = Nano1280_9()
        elif self.buttonGroup.id(object) == 3:
            self.model = Medium960_10()
        elif self.buttonGroup.id(object) == 4:
            self.model = Nano1280_9()
        elif self.buttonGroup.id(object) == 5:
            self.model = Medium960_9()
        elif self.buttonGroup.id(object) == 6:
            self.model = Medium_ships()


    def swap_mode(self, object):
        if self.detected_buttonGroup.id(object) == 1:
            self.image_mode_detected = True
        elif self.detected_buttonGroup.id(object) == 2:
            self.image_mode_detected = False

            
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        self.file_path = event.mimeData().urls()[0].toLocalFile()
        self.current_pixmap = QPixmap(self.file_path)
        self.image_view.update_image(self.current_pixmap)
            

        
    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Выберите директорию", "")
        if self.directory:
            self.image_files = self.get_images_in_directory(self.directory)
            self.file_table.fill_table([os.path.basename(image_name) for image_name in self.image_files])
            self.detected.setEnabled(False)
            self.no_detected.setChecked(True)
        
        
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
            self.image_view.update_image(QPixmap(f'tmp/detected_{msg}'))
        else:
            for name in self.image_files:
                if name.endswith(msg):
                    self.image_view.update_image(QPixmap(name))
                    return
           
    def closeEvent(self, a0):
        abspath = os.path.abspath('tmp/')
        for elem in os.listdir('tmp'):
            os.remove(os.path.join(abspath, elem))
        super().closeEvent(a0)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("Vega_radio.ico"))
    widget = DropWidget()
    widget.show()
    sys.exit(app.exec_())