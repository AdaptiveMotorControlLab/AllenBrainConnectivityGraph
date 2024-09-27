# main.py

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from modules.gui import MainWindow, global_exception_handler

def main():
    # Set the global exception handler
    sys.excepthook = global_exception_handler

    app = QApplication(sys.argv)
    
    # Create the main window
    window = MainWindow()
    
    # Show the main window immediately
    window.show()

    # Use QTimer to defer initialization of advanced UI components
    QTimer.singleShot(0, window.init_advanced_ui)

    # Use timer to allow for proper shutdown
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()