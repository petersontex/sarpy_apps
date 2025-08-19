import sys

from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtWidgets import QApplication
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.wrapper import Controller as WrapperController
from sarpy_apps.apps.PySide_tools.apertureTool.PyAperture.controller.aperture_controller import ApertureController

if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    controller = WrapperController([ApertureController(1)])
    window = controller.viewer
    window.show()

    result = app.exec()
    sys.exit(result)
