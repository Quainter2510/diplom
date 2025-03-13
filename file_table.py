import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt


class FileTable(QWidget):
    image_changes = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.init_ui()
        

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)  
        self.table.setHorizontalHeaderLabels(["Имя файла", "колво объектов"])
        self.layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)

 
        self.table.setColumnWidth(0, 280)  
        self.table.setColumnWidth(1, 100)
        self.setMaximumWidth(450)
        
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, False)  
        self.table.horizontalHeader().setSectionResizeMode(1, False) 

        

        self.setLayout(self.layout)

        

    def fill_table(self, file_names):
        self.table.setRowCount(len(file_names))  # Устанавливаем количество строк
        for i, file_name in enumerate(file_names):
            self.table.setItem(i, 0, QTableWidgetItem(file_name))
            self.table.setItem(i, 1, QTableWidgetItem("Не определено"))
            self.table.item(i, 0).setFlags(Qt.ItemIsEnabled)
            self.table.item(i, 1).setFlags(Qt.ItemIsEnabled)



    def update_value(self, file_name, value):
        row_count = self.table.rowCount()
        for i in range(row_count):
            current_file_name = self.table.item(i, 0).text()
            if current_file_name == file_name:
                self.table.setItem(i, 1, QTableWidgetItem(str(value)))
                return
            
            
    def on_cell_double_clicked(self, row, column):
        current_filename = self.table.item(row, 0).text()
        self.image_changes.emit(current_filename)
        

            
    