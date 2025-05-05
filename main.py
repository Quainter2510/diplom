import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from widgets import MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("Vega_radio.ico"))
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec_())
