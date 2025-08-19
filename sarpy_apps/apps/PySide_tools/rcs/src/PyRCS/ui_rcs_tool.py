# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'rcs_tool.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QComboBox, QDockWidget,
    QHBoxLayout, QHeaderView, QLabel, QLayout,
    QSizePolicy, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)
from . import rcs_viewer
class Ui_RCSTool(object):
    def setupUi(self, RCSTool):
        if not RCSTool.objectName():
            RCSTool.setObjectName(u"RCSTool")
        RCSTool.resize(745, 331)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.rcs_data_layout = QVBoxLayout()
        self.rcs_data_layout.setObjectName(u"rcs_data_layout")
        self.tabWidget_2 = QTabWidget(self.dockWidgetContents)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        self.tab_1 = QWidget()
        self.tab_1.setObjectName(u"tab_1")
        self.horizontalLayout_2 = QHBoxLayout(self.tab_1)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.rcs_table_view = rcs_viewer.RCSTableWidget(self.tab_1)
        if (self.rcs_table_view.columnCount() < 6):
            self.rcs_table_view.setColumnCount(6)
        __qtablewidgetitem = QTableWidgetItem()
        self.rcs_table_view.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.rcs_table_view.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.rcs_table_view.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.rcs_table_view.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.rcs_table_view.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.rcs_table_view.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        if (self.rcs_table_view.rowCount() < 5):
            self.rcs_table_view.setRowCount(5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.rcs_table_view.setVerticalHeaderItem(0, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.rcs_table_view.setVerticalHeaderItem(1, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.rcs_table_view.setVerticalHeaderItem(2, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.rcs_table_view.setVerticalHeaderItem(3, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.rcs_table_view.setVerticalHeaderItem(4, __qtablewidgetitem10)
        self.rcs_table_view.setObjectName(u"rcs_table_view")
        self.rcs_table_view.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)

        self.horizontalLayout_2.addWidget(self.rcs_table_view)

        self.tabWidget_2.addTab(self.tab_1, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.horizontalLayout_3 = QHBoxLayout(self.tab_2)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.rcs_slow_plot_view = QVBoxLayout()
        self.rcs_slow_plot_view.setObjectName(u"rcs_slow_plot_view")

        self.horizontalLayout_3.addLayout(self.rcs_slow_plot_view)

        self.tabWidget_2.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.horizontalLayout = QHBoxLayout(self.tab_3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.rcs_fast_plot_view = QVBoxLayout()
        self.rcs_fast_plot_view.setObjectName(u"rcs_fast_plot_view")

        self.horizontalLayout.addLayout(self.rcs_fast_plot_view)

        self.tabWidget_2.addTab(self.tab_3, "")

        self.rcs_data_layout.addWidget(self.tabWidget_2)


        self.verticalLayout_3.addLayout(self.rcs_data_layout)

        self.rcs_button_layout = QHBoxLayout()
        self.rcs_button_layout.setObjectName(u"rcs_button_layout")
        self.label_2 = QLabel(self.dockWidgetContents)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setScaledContents(True)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.rcs_button_layout.addWidget(self.label_2)

        self.rcs_slow_time_units_combo_box = QComboBox(self.dockWidgetContents)
        self.rcs_slow_time_units_combo_box.addItem("")
        self.rcs_slow_time_units_combo_box.addItem("")
        self.rcs_slow_time_units_combo_box.addItem("")
        self.rcs_slow_time_units_combo_box.addItem("")
        self.rcs_slow_time_units_combo_box.addItem("")
        self.rcs_slow_time_units_combo_box.setObjectName(u"rcs_slow_time_units_combo_box")

        self.rcs_button_layout.addWidget(self.rcs_slow_time_units_combo_box)

        self.label = QLabel(self.dockWidgetContents)
        self.label.setObjectName(u"label")
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)

        self.rcs_button_layout.addWidget(self.label)

        self.rcs_measure_units_combo_box = QComboBox(self.dockWidgetContents)
        self.rcs_measure_units_combo_box.addItem("")
        self.rcs_measure_units_combo_box.addItem("")
        self.rcs_measure_units_combo_box.addItem("")
        self.rcs_measure_units_combo_box.addItem("")
        self.rcs_measure_units_combo_box.addItem("")
        self.rcs_measure_units_combo_box.setObjectName(u"rcs_measure_units_combo_box")

        self.rcs_button_layout.addWidget(self.rcs_measure_units_combo_box)

        self.rcs_button_layout.setStretch(1, 5)
        self.rcs_button_layout.setStretch(3, 5)

        self.verticalLayout_3.addLayout(self.rcs_button_layout)

        self.verticalLayout_3.setStretch(0, 90)
        self.verticalLayout_3.setStretch(1, 10)

        self.verticalLayout_2.addLayout(self.verticalLayout_3)

        RCSTool.setWidget(self.dockWidgetContents)

        self.retranslateUi(RCSTool)

        self.tabWidget_2.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(RCSTool)
    # setupUi

    def retranslateUi(self, RCSTool):
        RCSTool.setWindowTitle(QCoreApplication.translate("RCSTool", u"RCS Tool", None))
        ___qtablewidgetitem = self.rcs_table_view.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("RCSTool", u"Polarization", None));
        ___qtablewidgetitem1 = self.rcs_table_view.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("RCSTool", u"Mean Power [dB]", None));
        ___qtablewidgetitem2 = self.rcs_table_view.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("RCSTool", u"Mean Power", None));
        ___qtablewidgetitem3 = self.rcs_table_view.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("RCSTool", u"STD Power", None));
        ___qtablewidgetitem4 = self.rcs_table_view.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("RCSTool", u"Min Power", None));
        ___qtablewidgetitem5 = self.rcs_table_view.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("RCSTool", u"Max Power", None));
        ___qtablewidgetitem6 = self.rcs_table_view.verticalHeaderItem(0)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("RCSTool", u"RCS", None));
        ___qtablewidgetitem7 = self.rcs_table_view.verticalHeaderItem(1)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("RCSTool", u"Pixel Power", None));
        ___qtablewidgetitem8 = self.rcs_table_view.verticalHeaderItem(2)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("RCSTool", u"Beta Zero", None));
        ___qtablewidgetitem9 = self.rcs_table_view.verticalHeaderItem(3)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("RCSTool", u"Gamma Zero", None));
        ___qtablewidgetitem10 = self.rcs_table_view.verticalHeaderItem(4)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("RCSTool", u"Sigma Zero", None));
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_1), QCoreApplication.translate("RCSTool", u"RCS Table", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_2), QCoreApplication.translate("RCSTool", u"Slow Time Response", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_3), QCoreApplication.translate("RCSTool", u"Fast Time Response", None))
        self.label_2.setText(QCoreApplication.translate("RCSTool", u"Slow Time Units:", None))
        self.rcs_slow_time_units_combo_box.setItemText(0, QCoreApplication.translate("RCSTool", u"Collect Time", None))
        self.rcs_slow_time_units_combo_box.setItemText(1, QCoreApplication.translate("RCSTool", u"Polar Angle", None))
        self.rcs_slow_time_units_combo_box.setItemText(2, QCoreApplication.translate("RCSTool", u"Azimuth Angle", None))
        self.rcs_slow_time_units_combo_box.setItemText(3, QCoreApplication.translate("RCSTool", u"Aperture Relative", None))
        self.rcs_slow_time_units_combo_box.setItemText(4, QCoreApplication.translate("RCSTool", u"Target Relative", None))

        self.label.setText(QCoreApplication.translate("RCSTool", u"Measure:", None))
        self.rcs_measure_units_combo_box.setItemText(0, QCoreApplication.translate("RCSTool", u"RCS", None))
        self.rcs_measure_units_combo_box.setItemText(1, QCoreApplication.translate("RCSTool", u"Pixel Power", None))
        self.rcs_measure_units_combo_box.setItemText(2, QCoreApplication.translate("RCSTool", u"Beta Zero", None))
        self.rcs_measure_units_combo_box.setItemText(3, QCoreApplication.translate("RCSTool", u"Gamma Zero", None))
        self.rcs_measure_units_combo_box.setItemText(4, QCoreApplication.translate("RCSTool", u"Sigma Zero", None))

    # retranslateUi

