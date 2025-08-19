from PySide6.QtCore import (
    Qt,
)
from PySide6.QtWidgets import (
    QWidget,
    QStyle,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QMouseEvent,
    QMoveEvent,
)
import pyqtgraph as pg
from typing import Any

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.metaicon.model import ArrowData
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.pyui.metaicon_widget import \
    Ui_MetaIcon
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.stylesheet import \
    MITMStyleSheet


class View(QWidget, Ui_MetaIcon):
    """
    The GUI for the MetaIcon.

    A frameless, translucent widget used for displaying metadata icons and
    information tables. Configures window behavior, buttons, plot widgets, and
    styling according to the application's style guidelines.

    Enables NITF metadata visualization.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the View object.

        Parameters
        ----------
        parent : QWidget, optional
            The parent widget. Default is None.
        """
        super(View, self).__init__(parent, focusPolicy=Qt.WheelFocus)
        self.setupUi(self)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.closeButton.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
        )
        self.closeButton.clicked.connect(self.close)
        self.minimizeButton.setIcon(
            self.style().standardIcon(QStyle.SP_TitleBarMinButton)
        )
        self.minimizeButton.clicked.connect(self.showMinimized)

        self.setStyleSheet(MITMStyleSheet.MetaIcon.stylesheet)

        self.metaicon_plot.getPlotItem().hideAxis("bottom")
        self.metaicon_plot.getPlotItem().hideAxis("left")
        self.metaicon_plot.setFixedSize(150, 170)
        self.metaicon_plot.hideButtons()
        self.metaicon_plot.getViewBox().setMouseEnabled(False, False)
        self.metaicon_plot.setAspectLocked(lock=True, ratio=1)
        self.metaicon_plot.setXRange(-75, 75, padding=0)
        self.metaicon_plot.setYRange(-95, 75, padding=0)
        self.metaicon_plot.setBackground(MITMStyleSheet.MetaIcon.plot_background_color)
        self.metaicon_plot.getPlotItem().getViewBox().setBorder(
            color=MITMStyleSheet.MetaIcon.view_box_border_color, width=2
        )

        self.lower_table.item(2, 0).setForeground(
            QBrush(QColor(MITMStyleSheet.MetaIcon.layover_color))
        )
        self.lower_table.item(3, 0).setForeground(
            QBrush(QColor(MITMStyleSheet.MetaIcon.shadow_color))
        )
        self.lower_table.item(4, 0).setForeground(
            QBrush(QColor(MITMStyleSheet.MetaIcon.multipath_color))
        )

        for i in range(4):
            self.upper_table.item(i, 0).setFont(
                QFont(
                    MITMStyleSheet.MetaIcon.font,
                    pointSize=MITMStyleSheet.MetaIcon.font_size,
                )
            )

        for j in range(5):
            self.lower_table.item(j, 0).setFont(
                QFont(
                    MITMStyleSheet.MetaIcon.font,
                    pointSize=MITMStyleSheet.MetaIcon.font_size,
                )
            )

        self.upper_table.mousePressEvent = self.mousePressEvent
        self.lower_table.mousePressEvent = self.mousePressEvent

        self.upper_table.mouseMoveEvent = self.mouseMoveEvent
        self.lower_table.mouseMoveEvent = self.mouseMoveEvent

    def draw_arrows(
        self,
        metadata: list[Any],
        d1: ArrowData,
        d2: ArrowData,
        d3: ArrowData,
        d4: ArrowData,
        d5: ArrowData,
    ) -> None:
        """
        Draw arrows onto the plot object.

        Parameters
        ----------
        metadata : list[any]
            Metadata from the file reader object.
        d1 : ArrowData
            Angle and position data for the green arrow.
        d2 : ArrowData
            Angle and position data for the orange arrow.
        d3 : ArrowData
            Angle and position data for the blue arrow.
        d4 : ArrowData
            Angle and position data for the red arrow.
        d5 : ArrowData
            Angle and position data for the yellow arrow.
        """
        # Green
        a1 = pg.ArrowItem(
            angle=d1.angle,
            tipAngle=30,
            baseAngle=0,
            headLen=15,
            tailLen=50,
            tailWidth=2,
            pen=None,
            brush="#8ED15A",
            pxMode=False,
        )
        a1.setPos(d1.x, d1.y)
        # Orange
        a2 = pg.ArrowItem(
            angle=d2.angle,
            tipAngle=30,
            baseAngle=0,
            headLen=15,
            tailLen=50,
            tailWidth=2,
            pen=None,
            brush="#FF8C00",
            pxMode=False,
        )
        a2.setPos(d2.x, d2.y)
        # Blue
        a3 = pg.ArrowItem(
            angle=d3.angle,
            tipAngle=30,
            baseAngle=0,
            headLen=15,
            tailLen=50,
            tailWidth=2,
            pen=None,
            brush="#00A6FB",
            pxMode=False,
        )
        a3.setPos(d3.x, d3.y)
        # Red
        a4 = pg.ArrowItem(
            angle=d4.angle,
            tipAngle=30,
            baseAngle=0,
            headLen=15,
            tailLen=50,
            tailWidth=2,
            pen=None,
            brush="#FF031C",
            pxMode=False,
        )
        a4.setPos(d4.x, d4.y)
        # Yellow
        a5 = pg.ArrowItem(
            angle=d5.angle,
            tipAngle=30,
            baseAngle=0,
            headLen=15,
            tailLen=95,
            tailWidth=2,
            pen=None,
            brush="#FFFF00",
            pxMode=False,
        )
        a5.setPos(d5.x, d5.y)

        side_of_track_text = pg.TextItem(metadata[13], color="#FFFF00")
        side_of_track_text.setParentItem(a5)

        northText = pg.TextItem("N", color="#8ED15A")
        northText.setParentItem(a1)

        self.upper_table.item(0, 0).setText(metadata[0])
        self.upper_table.item(1, 0).setText(metadata[1])
        self.upper_table.item(2, 0).setText(metadata[2])
        self.upper_table.item(3, 0).setText(metadata[3])

        self.lower_table.item(0, 0).setText(metadata[4])
        self.lower_table.item(1, 0).setText(metadata[5])
        self.lower_table.item(2, 0).setText(metadata[6])
        self.lower_table.item(3, 0).setText(metadata[7])
        self.lower_table.item(4, 0).setText(metadata[8])

        self.upper_table.resizeColumnsToContents()
        self.lower_table.resizeColumnsToContents()

        self.metaicon_plot.addItem(a1)
        self.metaicon_plot.addItem(a2)
        self.metaicon_plot.addItem(a3)
        self.metaicon_plot.addItem(a4)
        self.metaicon_plot.addItem(a5)

        self.show()
        self.activateWindow()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events for dragging the widget.

        Captures the initial position when the left mouse button is pressed
        to support dragging the frameless window.

        Parameters
        ----------
        event : QMouseEvent
            The mouse press event.
        """
        if event.button() == Qt.LeftButton:
            self.dragPosition = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse move events for dragging the widget.

        Moves the frameless window when dragged with the left mouse button.

        Parameters
        ----------
        event : QMouseEvent
            The mouse move event.
        """
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPosition)
            event.accept()

    def moveEvent(self, e: QMoveEvent) -> None:
        """
        Handle move events for the widget.

        Ensures the widget size is properly adjusted when moved to prevent
        geometry-related errors in the Qt framework.

        Parameters
        ----------
        e : QMoveEvent
            The move event.
        """
        self.adjustSize()  # prevents "unable to set geometry" errors and other weirdness
        super().moveEvent(e)
