import sys
import os
from PyQt5.QtWidgets import QApplication

# Añadir el directorio gui al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()