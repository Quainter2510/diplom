from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QScrollArea
from PyQt5.QtCore import Qt

class ImageView(QWidget):
    def __init__(self):
        super().__init__()
        self.scroll_area = QScrollArea()
        self.img_label = QLabel()
        self.zoom_factor = 1
        self.last_pos_x = 0
        self.last_pos_y = 0
        self.lbl_pos_x = 0
        self.lbl_pos_y = 0
        
        # self.setStyleSheet('border-style: solid; border-width: 3px; border-color: black;')
        # self.img_label.setStyleSheet('border-style: solid; border-width: 1px; border-color: blue;')
        self.box_layout = QHBoxLayout()
        self.box_layout.addWidget(self.scroll_area)
        self.setLayout(self.box_layout)
        self.scroll_area.setWidget(self.img_label)
        self.box_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        
        self.img_label.resize(self.width(), self.height())

        
    def mousePressEvent(self, ev) -> None:
        new_pos = ev.globalPos()
        self.last_pos_x, self.last_pos_y = new_pos.x(), new_pos.y()
        
    def mouseMoveEvent(self, ev):
        new_pos = ev.globalPos()
        self.lbl_pos_x += new_pos.x() - self.last_pos_x
        self.lbl_pos_y += new_pos.y() - self.last_pos_y
        self.img_label.move(self.lbl_pos_x, self.lbl_pos_y)
        self.last_pos_x, self.last_pos_y = new_pos.x(), new_pos.y()

        
    def update_image(self, current_pixmap):
        self.zoom_factor = 1
        self.last_pos_x = 0
        self.last_pos_y = 0
        self.lbl_pos_x = 0
        self.lbl_pos_y = 0
        self.current_pixmap = current_pixmap
        self.scaled_image()
        self.img_label.setPixmap(self.scaled_qimage)
        
    def scaled_image(self):
        # self.current_pixmap.getScaledInstance(self.width(), self.height())
        if self.height() / self.width() > self.current_pixmap.height() / self.current_pixmap.width():
            self.scaled_qimage = self.current_pixmap.scaledToWidth(self.width())
        else:
            self.scaled_qimage = self.current_pixmap.scaledToHeight(self.height())
        self.resize_image()
 
        
        
    def wheelEvent(self,event):
        valueDelta = event.angleDelta().y()
        self._zoomInOut(valueDelta)
        self.resize_image()

    def _zoomInOut(self, deltaIncrease: int):
        if deltaIncrease > 0:
            self.zoom_factor *= 1.1
        else:
            self.zoom_factor /= 1.1     
        
    def resize_image(self):      
        self.img_label.setPixmap(self.current_pixmap.scaled(
            int(self.scaled_qimage.width() * self.zoom_factor), 
            int(self.scaled_qimage.height() * self.zoom_factor),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.img_label.resize(int(self.scaled_qimage.width() * self.zoom_factor), 
            int(self.scaled_qimage.height() * self.zoom_factor))
        