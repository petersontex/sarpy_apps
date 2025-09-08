import sys

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.wrapper import Controller as WrapperController

def is_package_installed(package_name):

    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main(reader=None):
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    tool_list = []

    from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.controller.aperture_controller import ApertureController
    tool_list.append(ApertureController(1))

    from sarpy_apps.apps.PySide_tools.rcs.src.PyRCS.rcs_controller import Controller as RCSController
    tool_list.append(RCSController(1))

    controller = WrapperController(tool_list)
    window = controller.viewer
    window.show()

    result = app.exec()
    sys.exit(result)

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    tool_list = []

    from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.controller.aperture_controller import ApertureController
    tool_list.append(ApertureController(1))

    from sarpy_apps.apps.PySide_tools.rcs.src.PyRCS.rcs_controller import Controller as RCSController
    tool_list.append(RCSController(1))

    controller = WrapperController(tool_list)
    window = controller.viewer
    window.show()

    result = app.exec()
    sys.exit(result)
