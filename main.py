from PyQt5.QtGui import QIcon
import sys
from PyQt5.QtWidgets import QApplication
from view import MainWindow
from controller import AppController

app = QApplication(sys.argv)
app.setWindowIcon(QIcon("Vega_radio.ico"))
window = MainWindow()
controller = AppController(window)
window.show()
sys.exit(app.exec_())