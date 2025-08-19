# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'annoation_dock.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (
    QCoreApplication,
    QDate,
    QDateTime,
    QLocale,
    QMetaObject,
    QObject,
    QPoint,
    QRect,
    QSize,
    QTime,
    QUrl,
    Qt,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QConicalGradient,
    QCursor,
    QFont,
    QFontDatabase,
    QGradient,
    QIcon,
    QImage,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPalette,
    QPixmap,
    QRadialGradient,
    QTransform,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDockWidget,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation import view as \
    annotation_view


class Ui_Annotation(object):
    def setupUi(self, DockWidget):
        if not DockWidget.objectName():
            DockWidget.setObjectName("DockWidget")
        DockWidget.resize(446, 467)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.geometry_view_layout = QVBoxLayout()
        self.geometry_view_layout.setObjectName("geometry_view_layout")
        self.geometry_view = annotation_view.GeometryViewWidget()
        self.geometry_view.setObjectName("geometry_view")

        self.geometry_view_layout.addWidget(self.geometry_view)

        self.verticalLayout_2.addLayout(self.geometry_view_layout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.geometry_table = annotation_view.GeometryTableWidget(
            self.dockWidgetContents
        )
        if self.geometry_table.columnCount() < 1:
            self.geometry_table.setColumnCount(1)
        __qtablewidgetitem = QTableWidgetItem()
        self.geometry_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        self.geometry_table.setObjectName("geometry_table")

        self.horizontalLayout.addWidget(self.geometry_table)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.add_geometry_button = QPushButton(self.dockWidgetContents)
        self.add_geometry_button.setObjectName("add_geometry_button")

        self.horizontalLayout_2.addWidget(self.add_geometry_button)

        self.import_button = QPushButton(self.dockWidgetContents)
        self.import_button.setObjectName("import_button")

        self.horizontalLayout_2.addWidget(self.import_button)

        self.export_button = QPushButton(self.dockWidgetContents)
        self.export_button.setObjectName("export_button")

        self.horizontalLayout_2.addWidget(self.export_button)

        self.voids_toggle = QCheckBox(self.dockWidgetContents)
        self.voids_toggle.setObjectName("voids_toggle")

        self.horizontalLayout_2.addWidget(self.voids_toggle)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.verticalLayout_2.setStretch(0, 65)
        self.verticalLayout_2.setStretch(1, 30)
        self.verticalLayout_2.setStretch(2, 5)
        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)

        QMetaObject.connectSlotsByName(DockWidget)

    # setupUi

    def retranslateUi(self, DockWidget):
        DockWidget.setWindowTitle(
            QCoreApplication.translate("DockWidget", "DockWidget", None)
        )
        ___qtablewidgetitem = self.geometry_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(
            QCoreApplication.translate("DockWidget", "Geometry", None)
        )
        self.add_geometry_button.setText(
            QCoreApplication.translate("DockWidget", "Geometry", None)
        )
        self.import_button.setText(
            QCoreApplication.translate("DockWidget", "Import", None)
        )
        self.export_button.setText(
            QCoreApplication.translate("DockWidget", "Export", None)
        )
        self.voids_toggle.setText(
            QCoreApplication.translate("DockWidget", "Include Voids", None)
        )

    # retranslateUi
