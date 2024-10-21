# tests/test_main_window.py
import sys, os, pytest
os.chdir("C:\\Luck\\src")
sys.path.append("C:\\Luck\\src")

from MyPackages.MainWindow import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt

@pytest.fixture(scope="module")
def app():
    app = QApplication([])
    main_window = MainWindow()
    yield main_window
    app.quit()

def testTitle(app):
    assert app.windowTitle() == "Luck"

def testButtonClick_no_Error(app, qtbot):
    button = app.findChild(QPushButton, 'bt_file')
    assert button is not None
    try:
        qtbot.mouseClick(button, Qt.LeftButton)
    except Exception as e:
        pytest.fail(f"Error al hacer clic en el botón: {e}")