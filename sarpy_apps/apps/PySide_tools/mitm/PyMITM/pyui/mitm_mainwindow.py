# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mitm_mainwindow.ui'
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
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QSpinBox,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from pyqtgraph import PlotWidget


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        MainWindow.setStyleSheet("")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth()
        )
        self.centralwidget.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(6, 6, -1, 3)
        self.menuWidget = QWidget(self.centralwidget)
        self.menuWidget.setObjectName("menuWidget")
        sizePolicy.setHeightForWidth(self.menuWidget.sizePolicy().hasHeightForWidth())
        self.menuWidget.setSizePolicy(sizePolicy)
        self.menuWidget.setAcceptDrops(True)
        self.menuWidget.setStyleSheet("")
        self.horizontalLayout_2 = QHBoxLayout(self.menuWidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.directoryWidget = QWidget(self.menuWidget)
        self.directoryWidget.setObjectName("directoryWidget")
        self.directoryWidget.setStyleSheet("")
        self.directoryLayout = QHBoxLayout(self.directoryWidget)
        self.directoryLayout.setObjectName("directoryLayout")
        self.directoryLayout.setContentsMargins(0, 0, 0, 0)

        self.horizontalLayout_2.addWidget(self.directoryWidget)

        self.fileLineEdit = QLineEdit(self.menuWidget)
        self.fileLineEdit.setObjectName("fileLineEdit")

        self.horizontalLayout_2.addWidget(self.fileLineEdit)

        self.horizontalSpacer_3 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)

        self.newPlotButton = QPushButton(self.menuWidget)
        self.newPlotButton.setObjectName("newPlotButton")
        self.newPlotButton.setEnabled(True)

        self.horizontalLayout_2.addWidget(self.newPlotButton)

        self.verticalLayout.addWidget(self.menuWidget)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName("line")
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout.addWidget(self.line)

        self.controlsWidget = QWidget(self.centralwidget)
        self.controlsWidget.setObjectName("controlsWidget")
        sizePolicy.setHeightForWidth(
            self.controlsWidget.sizePolicy().hasHeightForWidth()
        )
        self.controlsWidget.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.controlsWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QLabel(self.controlsWidget)
        self.label.setObjectName("label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)

        self.horizontalLayout.addWidget(self.label)

        self.frameSpinBox = QSpinBox(self.controlsWidget)
        self.frameSpinBox.setObjectName("frameSpinBox")
        self.frameSpinBox.setMinimum(1)

        self.horizontalLayout.addWidget(self.frameSpinBox)

        self.decimationComboBox = QComboBox(self.controlsWidget)
        self.decimationComboBox.addItem("")
        self.decimationComboBox.addItem("")
        self.decimationComboBox.setObjectName("decimationComboBox")

        self.horizontalLayout.addWidget(self.decimationComboBox)

        self.remapOptionComboBox = QComboBox(self.controlsWidget)
        self.remapOptionComboBox.addItem("")
        self.remapOptionComboBox.addItem("")
        self.remapOptionComboBox.setObjectName("remapOptionComboBox")

        self.horizontalLayout.addWidget(self.remapOptionComboBox)

        self.remapButton = QPushButton(self.controlsWidget)
        self.remapButton.setObjectName("remapButton")

        self.horizontalLayout.addWidget(self.remapButton)

        self.verticalLayout.addWidget(self.controlsWidget)

        self.verticalSpacer = QSpacerItem(
            20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )

        self.verticalLayout.addItem(self.verticalSpacer)

        MainWindow.setCentralWidget(self.centralwidget)
        self.plotDockWidgetLeft = QDockWidget(MainWindow)
        self.plotDockWidgetLeft.setObjectName("plotDockWidgetLeft")
        sizePolicy2 = QSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred
        )
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(
            self.plotDockWidgetLeft.sizePolicy().hasHeightForWidth()
        )
        self.plotDockWidgetLeft.setSizePolicy(sizePolicy2)
        self.plotDockWidgetLeft.setAcceptDrops(False)
        self.plotDockWidgetLeft.setStyleSheet(
            "QDockWidget {\n"
            "    border: 1px solid lightgray;\n"
            "}\n"
            "QDockWidget::title {\n"
            "	border: 1px solid lightgray;\n"
            "}"
        )
        self.plotDockWidgetLeft.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.plotDockWidgetLeft.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.dockWidgetContents.setAcceptDrops(False)
        self.dockWidgetContents.setStyleSheet("background: lightgrey;")
        self.gridLayout = QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.plotWidgetLeft = PlotWidget(self.dockWidgetContents)
        self.plotWidgetLeft.setObjectName("plotWidgetLeft")
        self.plotWidgetLeft.setAcceptDrops(True)
        self.plotWidgetLeft.setStyleSheet("")

        self.gridLayout.addWidget(self.plotWidgetLeft, 0, 1, 1, 1)

        self.widget = QWidget(self.dockWidgetContents)
        self.widget.setObjectName("widget")
        self.widget.setEnabled(True)
        self.horizontalLayout_3 = QHBoxLayout(self.widget)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.widget)
        self.pushButton.setObjectName("pushButton")

        self.horizontalLayout_3.addWidget(self.pushButton)

        self.horizontalSpacer = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.labelLeft = QLabel(self.widget)
        self.labelLeft.setObjectName("labelLeft")
        self.labelLeft.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTrailing
            | Qt.AlignmentFlag.AlignVCenter
        )

        self.horizontalLayout_3.addWidget(self.labelLeft)

        self.gridLayout.addWidget(self.widget, 1, 1, 1, 1)

        self.plotDockWidgetLeft.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.plotDockWidgetLeft
        )
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)
        self.fileDialogDockWidget = QDockWidget(MainWindow)
        self.fileDialogDockWidget.setObjectName("fileDialogDockWidget")
        sizePolicy3 = QSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(
            self.fileDialogDockWidget.sizePolicy().hasHeightForWidth()
        )
        self.fileDialogDockWidget.setSizePolicy(sizePolicy3)
        self.fileDialogDockWidget.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.fileDialogDockWidget.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.dockWidgetContents_2 = QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.gridLayout_2 = QGridLayout(self.dockWidgetContents_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.fileDialogDockWidget.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.fileDialogDockWidget
        )
        self.plotDockWidgetRight = QDockWidget(MainWindow)
        self.plotDockWidgetRight.setObjectName("plotDockWidgetRight")
        sizePolicy2.setHeightForWidth(
            self.plotDockWidgetRight.sizePolicy().hasHeightForWidth()
        )
        self.plotDockWidgetRight.setSizePolicy(sizePolicy2)
        self.plotDockWidgetRight.setStyleSheet(
            "QDockWidget {\n"
            "	border: 1px solid lightgray;\n"
            "}\n"
            "QDockWidget::title {\n"
            "	border: 1px solid lightgray;\n"
            "}"
        )
        self.plotDockWidgetRight.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.plotDockWidgetRight.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.dockWidgetContents_3 = QWidget()
        self.dockWidgetContents_3.setObjectName("dockWidgetContents_3")
        self.dockWidgetContents_3.setStyleSheet("background: lightgrey")
        self.gridLayout_3 = QGridLayout(self.dockWidgetContents_3)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.plotWidgetRight = PlotWidget(self.dockWidgetContents_3)
        self.plotWidgetRight.setObjectName("plotWidgetRight")
        self.plotWidgetRight.setAcceptDrops(True)

        self.gridLayout_3.addWidget(self.plotWidgetRight, 0, 0, 1, 1)

        self.widget_2 = QWidget(self.dockWidgetContents_3)
        self.widget_2.setObjectName("widget_2")
        self.horizontalLayout_4 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.pushButton_2 = QPushButton(self.widget_2)
        self.pushButton_2.setObjectName("pushButton_2")

        self.horizontalLayout_4.addWidget(self.pushButton_2)

        self.horizontalSpacer_2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.labelRight = QLabel(self.widget_2)
        self.labelRight.setObjectName("labelRight")

        self.horizontalLayout_4.addWidget(self.labelRight)

        self.gridLayout_3.addWidget(self.widget_2, 1, 0, 1, 1)

        self.plotDockWidgetRight.setWidget(self.dockWidgetContents_3)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.BottomDockWidgetArea, self.plotDockWidgetRight
        )
        self.metaIconDock = QDockWidget(MainWindow)
        self.metaIconDock.setObjectName("metaIconDock")
        self.metaIconDock.setStyleSheet(
            "QDockWidget {\n"
            "  border: 1px solid lightgray;\n"
            "}\n"
            "QDockWidget::title {\n"
            "  border: 1px solid lightgray;\n"
            "}"
        )
        self.metaIconDock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.metaIconDock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.dockWidgetContents_5 = QWidget()
        self.dockWidgetContents_5.setObjectName("dockWidgetContents_5")
        self.dockWidgetContents_5.setStyleSheet("background: lightgrey;")
        self.gridLayout_4 = QGridLayout(self.dockWidgetContents_5)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.plotWidgetMetaIcon = PlotWidget(self.dockWidgetContents_5)
        self.plotWidgetMetaIcon.setObjectName("plotWidgetMetaIcon")

        self.gridLayout_4.addWidget(self.plotWidgetMetaIcon, 0, 0, 1, 1)

        self.metaIconDock.setWidget(self.dockWidgetContents_5)
        MainWindow.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.metaIconDock
        )

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", "MITM Viewer", None)
        )
        self.fileLineEdit.setText("")
        self.newPlotButton.setText(
            QCoreApplication.translate("MainWindow", "Add Plot", None)
        )
        self.label.setText(QCoreApplication.translate("MainWindow", "Index:", None))
        self.decimationComboBox.setItemText(
            0, QCoreApplication.translate("MainWindow", "Decimate", None)
        )
        self.decimationComboBox.setItemText(
            1, QCoreApplication.translate("MainWindow", "Mean", None)
        )

        self.remapOptionComboBox.setItemText(
            0, QCoreApplication.translate("MainWindow", "Density", None)
        )
        self.remapOptionComboBox.setItemText(
            1, QCoreApplication.translate("MainWindow", "NRL", None)
        )

        self.remapButton.setText(
            QCoreApplication.translate("MainWindow", "Remap", None)
        )
        self.plotDockWidgetLeft.setWindowTitle("")
        self.pushButton.setText(
            QCoreApplication.translate("MainWindow", "MetaIcon", None)
        )
        self.labelLeft.setText("")
        self.pushButton_2.setText(
            QCoreApplication.translate("MainWindow", "MetaIcon", None)
        )
        self.labelRight.setText("")

    # retranslateUi
