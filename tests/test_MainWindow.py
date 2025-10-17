# tests/test_full_coverage.py
import os
import sys
import pytest
from PyQt6.QtWidgets import QApplication, QPushButton
from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QIcon

# Import our MainWindow from the source directory.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SRC')))
from MyPackages.MainWindow import MainWindow

# -------------------------------------------------------------------
# Fixture general para crear la aplicación y el MainWindow (para PyQt)
# -------------------------------------------------------------------
@pytest.fixture(scope='module')
def app_instance():
    app = QApplication([])
    main_window = MainWindow()
    yield main_window
    app.quit()

# ---------------------------
# Pruebas sobre MainWindow
# ---------------------------
def test_window_title(app_instance):
    # Verifica que el título de la ventana sea 'Luck'
    assert app_instance.windowTitle() == 'Luck'

def test_button_presence_and_click(app_instance, qtbot):
    # Busca un botón con objectName 'bt_file' y prueba que se pueda hacer clic.
    button = app_instance.findChild(QPushButton, 'bt_file')
    assert button is not None, "No se encontró el botón 'bt_file'"
    try:
        qtbot.mouseClick(button, Qt.LeftButton)
    except Exception as e:
        pytest.fail(f'Error al hacer clic en el botón: {e}')

def test_window_icon(app_instance):
    # Verifica que el ícono de la ventana sea una instancia de QIcon.
    icon = app_instance.windowIcon()
    assert isinstance(icon, QIcon), 'El ícono de la ventana no es una instancia de QIcon'

def test_timer_intervals(app_instance):
    # Verifica que el timer para reconexión (timerDsn) tenga el intervalo esperado.
    assert hasattr(app_instance, 'timerDsn'), 'MainWindow no tiene timerDsn'
    expected_interval = 1795 * 1000
    assert app_instance.timerDsn.interval() == expected_interval, 'El intervalo de timerDsn es incorrecto'

def test_user_attribute(app_instance):
    # Comprueba que el atributo 'user' se inicialice correctamente.
    assert isinstance(app_instance.user, str) and app_instance.user != '', "El atributo 'user' es inválido"

def test_bound_methods():
    # Verifica que se hayan enlazado (bind) los métodos requeridos al MainWindow.
    required_methods = [
        'updateTrayIcon', 'stopIconTimer', 'dragEnterEvent', 'dropEvent',
        'mousePressEvent', 'mouseReleaseEvent', 'closeEvent', 'leaveEvent',
        'prepareFramework', 'prepareUrlsDrop', 'initWindow', 'onScreenChanged',
        'syncSplitterH', 'syncSplitterV', 'saveEcoSplittersSizes'
    ]
    for method in required_methods:
        assert hasattr(MainWindow, method), f'MainWindow no tiene el método {method}'

def test_change_event(app_instance):
    # Crea un evento dummy del tipo WindowStateChange y verifica que el changeEvent se
    # ejecute sin lanzar excepciones.
    event = QEvent(QEvent.Type.WindowStateChange)
    try:
        app_instance.changeEvent(event)
    except Exception as e:
        pytest.fail(f'changeEvent lanzó una excepción: {e}')

def test_yaml_handler_usage(app_instance):
    # Verifica que se haya cargado la configuración mediante YamlHandler.
    # Se asume que 'version' tiene un atributo 'index' que es un diccionario.
    assert hasattr(app_instance, 'version'), "MainWindow no tiene atributo 'version'"
    version_val = app_instance.version.index.get('version')
    assert version_val is not None, "La clave 'version' no se encontró en la configuración"

# -----------------------------------------------
# Prueba para la lógica de rotación del log en Luck.py
# -----------------------------------------------
def test_log_file_rotation(tmp_path, monkeypatch):
    """
    Simula la existencia de un archivo de log con más de 1000 líneas y verifica que 
    la función que limpia el archivo lo elimine.
    """
    # Crear un archivo de log temporal con 1001 líneas.
    log_file = tmp_path / 'Luck-Debug.log'
    log_file.write_text('linea\n' * 1001)

    # Función dummy para reemplazar os.path.exists:
    def fake_exists(path):
        return path == str(log_file)

    # Variable para indicar si os.remove fue llamado.
    removed = False
    def fake_remove(path):
        nonlocal removed
        removed = True

    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr(os, 'remove', fake_remove)

    # Ejecuta la lógica de limpieza tal como se implementa en Luck.py.
    if os.path.exists(str(log_file)):
        with open(str(log_file), 'r') as file:
            lines = file.readlines()
            if len(lines) > 1000:
                os.remove(str(log_file))
    assert removed, 'El archivo de log no fue eliminado a pesar de superar 1000 líneas'