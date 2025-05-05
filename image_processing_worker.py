from PyQt5.QtCore import QThread, pyqtSignal
import os

class ImageProcessingWorker(QThread):
    progress_updated = pyqtSignal(int, str)  
    file_processed = pyqtSignal(str, int)   
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, model, image_files, conf):
        super().__init__()
        self.model = model
        self.image_files = image_files
        self.conf = conf

    def run(self):
        try:
            total_files = len(self.image_files)
            for i, image_path in enumerate(self.image_files):                
                filename = os.path.basename(image_path)
                self.progress_updated.emit(int(100 * i / total_files), filename)
                
                try:
                    _, detections = self.model.process_image(image_path, self.conf)
                    self.file_processed.emit(filename, detections)
                except Exception as e:
                    self.error_occurred.emit(f"Ошибка обработки {filename}: {str(e)}")
            
            self.progress_updated.emit(100, "")
            self.finished.emit()
        except Exception as e:
            self.error_occurred.emit(f"Критическая ошибка: {str(e)}")
            self.finished.emit()