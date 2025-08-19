# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'plot_widget_dock.ui'
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
    QComboBox,
    QDockWidget,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QWidget,
)


class Ui_DockWidget(object):
    def setupUi(self, DockWidget):
        if not DockWidget.objectName():
            DockWidget.setObjectName("DockWidget")
        DockWidget.resize(506, 300)
        DockWidget.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.controlsWidget = QWidget(self.dockWidgetContents)
        self.controlsWidget.setObjectName("controlsWidget")
        self.horizontalLayout = QHBoxLayout(self.controlsWidget)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.metaIconButton = QPushButton(self.controlsWidget)
        self.metaIconButton.setObjectName("metaIconButton")

        self.horizontalLayout.addWidget(self.metaIconButton)

        self.debugPushButton = QPushButton(self.controlsWidget)
        self.debugPushButton.setObjectName("debugPushButton")

        self.horizontalLayout.addWidget(self.debugPushButton)

        self.horizontalSpacer = QSpacerItem(
            20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.coordinatesLabel = QLabel(self.controlsWidget)
        self.coordinatesLabel.setObjectName("coordinatesLabel")

        self.horizontalLayout.addWidget(self.coordinatesLabel)

        self.coordinatesButton = QPushButton(self.controlsWidget)
        self.coordinatesButton.setObjectName("coordinatesButton")

        self.horizontalLayout.addWidget(self.coordinatesButton)

        self.gridLayout.addWidget(self.controlsWidget, 1, 0, 1, 1)

        self.upperControlsWidget = QWidget(self.dockWidgetContents)
        self.upperControlsWidget.setObjectName("upperControlsWidget")
        self.gridLayout_2 = QGridLayout(self.upperControlsWidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.remapMethodComboBox = QComboBox(self.upperControlsWidget)
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.addItem("")
        self.remapMethodComboBox.setObjectName("remapMethodComboBox")

        self.gridLayout_2.addWidget(self.remapMethodComboBox, 0, 3, 1, 1)

        self.enhancePushButton = QPushButton(self.upperControlsWidget)
        self.enhancePushButton.setObjectName("enhancePushButton")

        self.gridLayout_2.addWidget(self.enhancePushButton, 0, 6, 1, 1)

        self.indexLabel = QLabel(self.upperControlsWidget)
        self.indexLabel.setObjectName("indexLabel")

        self.gridLayout_2.addWidget(self.indexLabel, 0, 0, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(
            20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.gridLayout_2.addItem(self.horizontalSpacer_2, 0, 5, 1, 1)

        self.indexSpinBox = QSpinBox(self.upperControlsWidget)
        self.indexSpinBox.setObjectName("indexSpinBox")

        self.gridLayout_2.addWidget(self.indexSpinBox, 0, 1, 1, 1)

        self.downsampleMethodComboBox = QComboBox(self.upperControlsWidget)
        self.downsampleMethodComboBox.addItem("")
        self.downsampleMethodComboBox.setObjectName("downsampleMethodComboBox")

        self.gridLayout_2.addWidget(self.downsampleMethodComboBox, 0, 2, 1, 1)

        self.aspectRatioComboBox = QComboBox(self.upperControlsWidget)
        self.aspectRatioComboBox.addItem("")
        self.aspectRatioComboBox.addItem("")
        self.aspectRatioComboBox.setObjectName("aspectRatioComboBox")

        self.gridLayout_2.addWidget(self.aspectRatioComboBox, 0, 4, 1, 1)

        self.gridLayout.addWidget(self.upperControlsWidget, 0, 0, 1, 1)

        DockWidget.setWidget(self.dockWidgetContents)

        self.retranslateUi(DockWidget)

        QMetaObject.connectSlotsByName(DockWidget)

    # setupUi

    def retranslateUi(self, DockWidget):
        DockWidget.setWindowTitle("")
        self.metaIconButton.setText(
            QCoreApplication.translate("DockWidget", "MetaIcon", None)
        )
        self.debugPushButton.setText(
            QCoreApplication.translate("DockWidget", "Debug", None)
        )
        self.coordinatesLabel.setText("")
        self.coordinatesButton.setText(
            QCoreApplication.translate("DockWidget", "PushButton", None)
        )
        self.remapMethodComboBox.setItemText(
            0, QCoreApplication.translate("DockWidget", "Density", None)
        )
        self.remapMethodComboBox.setItemText(
            1, QCoreApplication.translate("DockWidget", "Brighter", None)
        )
        self.remapMethodComboBox.setItemText(
            2, QCoreApplication.translate("DockWidget", "Darker", None)
        )
        self.remapMethodComboBox.setItemText(
            3, QCoreApplication.translate("DockWidget", "High Contrast", None)
        )
        self.remapMethodComboBox.setItemText(
            4, QCoreApplication.translate("DockWidget", "Linear", None)
        )
        self.remapMethodComboBox.setItemText(
            5, QCoreApplication.translate("DockWidget", "Logarithmic", None)
        )
        self.remapMethodComboBox.setItemText(
            6, QCoreApplication.translate("DockWidget", "PEDF", None)
        )
        self.remapMethodComboBox.setItemText(
            7, QCoreApplication.translate("DockWidget", "NRL", None)
        )

        self.enhancePushButton.setText(
            QCoreApplication.translate("DockWidget", "Enhance", None)
        )
        self.indexLabel.setText(
            QCoreApplication.translate("DockWidget", "Index:", None)
        )
        self.downsampleMethodComboBox.setItemText(
            0, QCoreApplication.translate("DockWidget", "Decimate", None)
        )

        self.aspectRatioComboBox.setItemText(
            0, QCoreApplication.translate("DockWidget", "Square", None)
        )
        self.aspectRatioComboBox.setItemText(
            1, QCoreApplication.translate("DockWidget", "Aspect", None)
        )

    # retranslateUi
