# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'aperture_tool.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDockWidget,
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLayout, QLineEdit, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_ApertureTool(object):
    def setupUi(self, ApertureTool):
        if not ApertureTool.objectName():
            ApertureTool.setObjectName(u"ApertureTool")
        ApertureTool.resize(1610, 880)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout_2 = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.dock_widget_contents = QHBoxLayout()
        self.dock_widget_contents.setObjectName(u"dock_widget_contents")
        self.dock_widget_contents.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.layout_fft = QVBoxLayout()
        self.layout_fft.setObjectName(u"layout_fft")
        self.fft_view = QFrame(self.dockWidgetContents)
        self.fft_view.setObjectName(u"fft_view")
        self.fft_view.setFrameShape(QFrame.StyledPanel)
        self.fft_view.setFrameShadow(QFrame.Raised)

        self.layout_fft.addWidget(self.fft_view)


        self.dock_widget_contents.addLayout(self.layout_fft)

        self.layout_animation = QVBoxLayout()
        self.layout_animation.setObjectName(u"layout_animation")
        self.animation_view = QFrame(self.dockWidgetContents)
        self.animation_view.setObjectName(u"animation_view")
        self.animation_view.setFrameShape(QFrame.StyledPanel)
        self.animation_view.setFrameShadow(QFrame.Raised)

        self.layout_animation.addWidget(self.animation_view)


        self.dock_widget_contents.addLayout(self.layout_animation)

        self.dock_widget_contents.setStretch(0, 50)
        self.dock_widget_contents.setStretch(1, 50)

        self.verticalLayout_2.addLayout(self.dock_widget_contents)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.frame_layout = QHBoxLayout()
        self.frame_layout.setObjectName(u"frame_layout")
        self.frame_count_label = QLabel(self.dockWidgetContents)
        self.frame_count_label.setObjectName(u"frame_count_label")

        self.frame_layout.addWidget(self.frame_count_label)

        self.frame_count = QLineEdit(self.dockWidgetContents)
        self.frame_count.setObjectName(u"frame_count")

        self.frame_layout.addWidget(self.frame_count)

        self.frame_rate_label = QLabel(self.dockWidgetContents)
        self.frame_rate_label.setObjectName(u"frame_rate_label")

        self.frame_layout.addWidget(self.frame_rate_label)

        self.frame_rate = QLineEdit(self.dockWidgetContents)
        self.frame_rate.setObjectName(u"frame_rate")

        self.frame_layout.addWidget(self.frame_rate)


        self.gridLayout.addLayout(self.frame_layout, 0, 1, 1, 1)

        self.label = QLabel(self.dockWidgetContents)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setBold(True)
        self.label.setFont(font)
        self.label.setTextFormat(Qt.AutoText)

        self.gridLayout.addWidget(self.label, 1, 0, 1, 1)

        self.frame_label = QLabel(self.dockWidgetContents)
        self.frame_label.setObjectName(u"frame_label")
        self.frame_label.setFont(font)
        self.frame_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.gridLayout.addWidget(self.frame_label, 0, 0, 1, 1)

        self.aperture_layout = QHBoxLayout()
        self.aperture_layout.setObjectName(u"aperture_layout")
        self.aperture_min_label = QLabel(self.dockWidgetContents)
        self.aperture_min_label.setObjectName(u"aperture_min_label")

        self.aperture_layout.addWidget(self.aperture_min_label)

        self.aperture_min = QLineEdit(self.dockWidgetContents)
        self.aperture_min.setObjectName(u"aperture_min")

        self.aperture_layout.addWidget(self.aperture_min)

        self.aperture_max_label = QLabel(self.dockWidgetContents)
        self.aperture_max_label.setObjectName(u"aperture_max_label")

        self.aperture_layout.addWidget(self.aperture_max_label)

        self.aperture_max = QLineEdit(self.dockWidgetContents)
        self.aperture_max.setObjectName(u"aperture_max")

        self.aperture_layout.addWidget(self.aperture_max)

        self.aperture_fraction_label = QLabel(self.dockWidgetContents)
        self.aperture_fraction_label.setObjectName(u"aperture_fraction_label")
        self.aperture_fraction_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.aperture_layout.addWidget(self.aperture_fraction_label)

        self.aperture_fraction = QLineEdit(self.dockWidgetContents)
        self.aperture_fraction.setObjectName(u"aperture_fraction")

        self.aperture_layout.addWidget(self.aperture_fraction)


        self.gridLayout.addLayout(self.aperture_layout, 1, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.cycle_continuously_toggle = QCheckBox(self.dockWidgetContents)
        self.cycle_continuously_toggle.setObjectName(u"cycle_continuously_toggle")
        self.cycle_continuously_toggle.setEnabled(True)

        self.horizontalLayout_3.addWidget(self.cycle_continuously_toggle)

        self.reverse_toggle = QCheckBox(self.dockWidgetContents)
        self.reverse_toggle.setObjectName(u"reverse_toggle")
        self.reverse_toggle.setEnabled(True)

        self.horizontalLayout_3.addWidget(self.reverse_toggle)

        self.weighting_toggle = QCheckBox(self.dockWidgetContents)
        self.weighting_toggle.setObjectName(u"weighting_toggle")
        self.weighting_toggle.setEnabled(True)

        self.horizontalLayout_3.addWidget(self.weighting_toggle)

        self.deskew_toggle = QCheckBox(self.dockWidgetContents)
        self.deskew_toggle.setObjectName(u"deskew_toggle")
        self.deskew_toggle.setEnabled(True)

        self.horizontalLayout_3.addWidget(self.deskew_toggle)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.gridLayout_4 = QGridLayout()
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.selectionFilterLabel = QLabel(self.dockWidgetContents)
        self.selectionFilterLabel.setObjectName(u"selectionFilterLabel")

        self.gridLayout_4.addWidget(self.selectionFilterLabel, 0, 0, 1, 1)

        self.directionLabel = QLabel(self.dockWidgetContents)
        self.directionLabel.setObjectName(u"directionLabel")

        self.gridLayout_4.addWidget(self.directionLabel, 1, 0, 1, 1)

        self.window_filter_combo_box = QComboBox(self.dockWidgetContents)
        self.window_filter_combo_box.addItem("")
        self.window_filter_combo_box.addItem("")
        self.window_filter_combo_box.addItem("")
        self.window_filter_combo_box.addItem("")
        self.window_filter_combo_box.addItem("")
        self.window_filter_combo_box.setObjectName(u"window_filter_combo_box")

        self.gridLayout_4.addWidget(self.window_filter_combo_box, 0, 1, 1, 1)

        self.direction_combo_box = QComboBox(self.dockWidgetContents)
        self.direction_combo_box.addItem("")
        self.direction_combo_box.addItem("")
        self.direction_combo_box.addItem("")
        self.direction_combo_box.addItem("")
        self.direction_combo_box.addItem("")
        self.direction_combo_box.setObjectName(u"direction_combo_box")

        self.gridLayout_4.addWidget(self.direction_combo_box, 1, 1, 1, 1)


        self.verticalLayout_3.addLayout(self.gridLayout_4)

        self.playbackGridLayout = QGridLayout()
        self.playbackGridLayout.setObjectName(u"playbackGridLayout")
        self.play_button = QPushButton(self.dockWidgetContents)
        self.play_button.setObjectName(u"play_button")
        icon = QIcon()
        iconThemeName = u"media-playback-start"
        if QIcon.hasThemeIcon(iconThemeName):
            icon = QIcon.fromTheme(iconThemeName)
        else:
            icon.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.play_button.setIcon(icon)

        self.playbackGridLayout.addWidget(self.play_button, 2, 2, 1, 1)

        self.pause_button = QPushButton(self.dockWidgetContents)
        self.pause_button.setObjectName(u"pause_button")
        icon1 = QIcon()
        iconThemeName = u"media-playback-pause"
        if QIcon.hasThemeIcon(iconThemeName):
            icon1 = QIcon.fromTheme(iconThemeName)
        else:
            icon1.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.pause_button.setIcon(icon1)

        self.playbackGridLayout.addWidget(self.pause_button, 2, 3, 1, 1)

        self.step_end_frame_button = QPushButton(self.dockWidgetContents)
        self.step_end_frame_button.setObjectName(u"step_end_frame_button")
        icon2 = QIcon()
        iconThemeName = u"media-skip-forward"
        if QIcon.hasThemeIcon(iconThemeName):
            icon2 = QIcon.fromTheme(iconThemeName)
        else:
            icon2.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.step_end_frame_button.setIcon(icon2)

        self.playbackGridLayout.addWidget(self.step_end_frame_button, 2, 6, 1, 1)

        self.total_frames = QLineEdit(self.dockWidgetContents)
        self.total_frames.setObjectName(u"total_frames")
        self.total_frames.setReadOnly(True)

        self.playbackGridLayout.addWidget(self.total_frames, 1, 5, 1, 2)

        self.step_forward_frame_button = QPushButton(self.dockWidgetContents)
        self.step_forward_frame_button.setObjectName(u"step_forward_frame_button")
        icon3 = QIcon()
        iconThemeName = u"media-seek-forward"
        if QIcon.hasThemeIcon(iconThemeName):
            icon3 = QIcon.fromTheme(iconThemeName)
        else:
            icon3.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.step_forward_frame_button.setIcon(icon3)

        self.playbackGridLayout.addWidget(self.step_forward_frame_button, 2, 5, 1, 1)

        self.step_back_frame_button = QPushButton(self.dockWidgetContents)
        self.step_back_frame_button.setObjectName(u"step_back_frame_button")
        icon4 = QIcon()
        iconThemeName = u"media-seek-backward"
        if QIcon.hasThemeIcon(iconThemeName):
            icon4 = QIcon.fromTheme(iconThemeName)
        else:
            icon4.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.step_back_frame_button.setIcon(icon4)

        self.playbackGridLayout.addWidget(self.step_back_frame_button, 2, 1, 1, 1)

        self.ofLabel = QLabel(self.dockWidgetContents)
        self.ofLabel.setObjectName(u"ofLabel")
        self.ofLabel.setAlignment(Qt.AlignCenter)

        self.playbackGridLayout.addWidget(self.ofLabel, 1, 3, 1, 1)

        self.current_frame = QLineEdit(self.dockWidgetContents)
        self.current_frame.setObjectName(u"current_frame")
        self.current_frame.setReadOnly(True)

        self.playbackGridLayout.addWidget(self.current_frame, 1, 1, 1, 2)

        self.step_start_frame_button = QPushButton(self.dockWidgetContents)
        self.step_start_frame_button.setObjectName(u"step_start_frame_button")
        icon5 = QIcon()
        iconThemeName = u"media-skip-backward"
        if QIcon.hasThemeIcon(iconThemeName):
            icon5 = QIcon.fromTheme(iconThemeName)
        else:
            icon5.addFile(u".", QSize(), QIcon.Mode.Normal, QIcon.State.Off)

        self.step_start_frame_button.setIcon(icon5)

        self.playbackGridLayout.addWidget(self.step_start_frame_button, 2, 0, 1, 1)

        self.frameLabel = QLabel(self.dockWidgetContents)
        self.frameLabel.setObjectName(u"frameLabel")
        self.frameLabel.setAlignment(Qt.AlignCenter)

        self.playbackGridLayout.addWidget(self.frameLabel, 1, 0, 1, 1)


        self.verticalLayout_3.addLayout(self.playbackGridLayout)

        self.export_animation_layout = QHBoxLayout()
        self.export_animation_layout.setObjectName(u"export_animation_layout")
        self.include_annotations_toggle = QCheckBox(self.dockWidgetContents)
        self.include_annotations_toggle.setObjectName(u"include_annotations_toggle")

        self.export_animation_layout.addWidget(self.include_annotations_toggle)

        self.include_kspace_toggle = QCheckBox(self.dockWidgetContents)
        self.include_kspace_toggle.setObjectName(u"include_kspace_toggle")

        self.export_animation_layout.addWidget(self.include_kspace_toggle)

        self.animation_export_button = QPushButton(self.dockWidgetContents)
        self.animation_export_button.setObjectName(u"animation_export_button")

        self.export_animation_layout.addWidget(self.animation_export_button)

        self.export_chip_button = QPushButton(self.dockWidgetContents)
        self.export_chip_button.setObjectName(u"export_chip_button")

        self.export_animation_layout.addWidget(self.export_chip_button)


        self.verticalLayout_3.addLayout(self.export_animation_layout)

        self.verticalLayout_3.setStretch(0, 20)
        self.verticalLayout_3.setStretch(1, 10)
        self.verticalLayout_3.setStretch(2, 25)
        self.verticalLayout_3.setStretch(3, 35)
        self.verticalLayout_3.setStretch(4, 10)

        self.horizontalLayout_2.addLayout(self.verticalLayout_3)

        self.meta_icon_layout = QHBoxLayout()
        self.meta_icon_layout.setObjectName(u"meta_icon_layout")

        self.horizontalLayout_2.addLayout(self.meta_icon_layout)

        self.horizontalLayout_2.setStretch(0, 50)
        self.horizontalLayout_2.setStretch(1, 50)

        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.verticalLayout_2.setStretch(0, 70)
        self.verticalLayout_2.setStretch(1, 25)
        ApertureTool.setWidget(self.dockWidgetContents)

        self.retranslateUi(ApertureTool)

        QMetaObject.connectSlotsByName(ApertureTool)
    # setupUi

    def retranslateUi(self, ApertureTool):
        ApertureTool.setWindowTitle(QCoreApplication.translate("ApertureTool", u"Aperture Tool", None))
        self.frame_count_label.setText(QCoreApplication.translate("ApertureTool", u"Count", None))
        self.frame_count.setText(QCoreApplication.translate("ApertureTool", u"7", None))
        self.frame_rate_label.setText(QCoreApplication.translate("ApertureTool", u"Rate", None))
        self.frame_rate.setText(QCoreApplication.translate("ApertureTool", u"5", None))
        self.label.setText(QCoreApplication.translate("ApertureTool", u"Aperture:", None))
        self.frame_label.setText(QCoreApplication.translate("ApertureTool", u"Frame:", None))
        self.aperture_min_label.setText(QCoreApplication.translate("ApertureTool", u"Min", None))
        self.aperture_min.setText(QCoreApplication.translate("ApertureTool", u"0.1", None))
        self.aperture_max_label.setText(QCoreApplication.translate("ApertureTool", u"Max", None))
        self.aperture_max.setText(QCoreApplication.translate("ApertureTool", u"1", None))
        self.aperture_fraction_label.setText(QCoreApplication.translate("ApertureTool", u"Fraction", None))
        self.aperture_fraction.setText(QCoreApplication.translate("ApertureTool", u"0.25", None))
        self.cycle_continuously_toggle.setText(QCoreApplication.translate("ApertureTool", u"Cycle Continuously", None))
        self.reverse_toggle.setText(QCoreApplication.translate("ApertureTool", u"Reverse", None))
        self.weighting_toggle.setText(QCoreApplication.translate("ApertureTool", u"Apply Uniform Weighting", None))
        self.deskew_toggle.setText(QCoreApplication.translate("ApertureTool", u"Deskew", None))
        self.selectionFilterLabel.setText(QCoreApplication.translate("ApertureTool", u"Selection Filter", None))
        self.directionLabel.setText(QCoreApplication.translate("ApertureTool", u"Mode", None))
        self.window_filter_combo_box.setItemText(0, QCoreApplication.translate("ApertureTool", u"None", None))
        self.window_filter_combo_box.setItemText(1, QCoreApplication.translate("ApertureTool", u"Gaussian", None))
        self.window_filter_combo_box.setItemText(2, QCoreApplication.translate("ApertureTool", u"1/x^4", None))
        self.window_filter_combo_box.setItemText(3, QCoreApplication.translate("ApertureTool", u"Hamming", None))
        self.window_filter_combo_box.setItemText(4, QCoreApplication.translate("ApertureTool", u"Cosine on Pedestal", None))

        self.direction_combo_box.setItemText(0, QCoreApplication.translate("ApertureTool", u"Slow-Time", None))
        self.direction_combo_box.setItemText(1, QCoreApplication.translate("ApertureTool", u"Fast-Time", None))
        self.direction_combo_box.setItemText(2, QCoreApplication.translate("ApertureTool", u"Aperture-Percent", None))
        self.direction_combo_box.setItemText(3, QCoreApplication.translate("ApertureTool", u"Full-Range-Bandwidth", None))
        self.direction_combo_box.setItemText(4, QCoreApplication.translate("ApertureTool", u"Full-Azimuth-Bandwidth", None))

        self.play_button.setText("")
        self.pause_button.setText("")
        self.step_end_frame_button.setText("")
        self.total_frames.setText(QCoreApplication.translate("ApertureTool", u"6", None))
        self.step_forward_frame_button.setText("")
        self.step_back_frame_button.setText("")
        self.ofLabel.setText(QCoreApplication.translate("ApertureTool", u"of", None))
        self.current_frame.setText(QCoreApplication.translate("ApertureTool", u"0", None))
        self.step_start_frame_button.setText("")
        self.frameLabel.setText(QCoreApplication.translate("ApertureTool", u"Frame", None))
        self.include_annotations_toggle.setText(QCoreApplication.translate("ApertureTool", u"Include Annotations", None))
        self.include_kspace_toggle.setText(QCoreApplication.translate("ApertureTool", u"Include K-Space", None))
        self.animation_export_button.setText(QCoreApplication.translate("ApertureTool", u"Export Animation", None))
        self.export_chip_button.setText(QCoreApplication.translate("ApertureTool", u"Export Chip", None))
    # retranslateUi

