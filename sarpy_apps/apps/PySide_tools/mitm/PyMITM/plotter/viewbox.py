from PySide6.QtCore import (
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QMouseEvent,
    QWheelEvent,
)

from PySide6.QtWidgets import (
    QDockWidget,
)

import pyqtgraph as pg


class CustomViewBox(pg.ViewBox):
    """
    Custom pg.ViewBox for image display with enhanced zoom and pan behavior.

    A specialized ViewBox that inverts the Y-axis and adds custom context menu
    options for coordinate copying. Signals when view changes to trigger image
    resampling and optimizes behavior for large images.

    Attributes
    ----------
    parent_plotter_viewer : PlotterView or None
        The View of the Plotter object to which the CustomViewBox belongs.
    zoomed : bool
        A flag used to indicate that resampling should be deferred until
        explicitly triggered. Prevents freezing when zooming in and out
        on very large images.

    Signals
    -------
    auto_resample_signal
        Emitted when the image in the viewbox is zoomed or panned;
        indicates that the image needs to be resampled.
    """

    auto_resample_signal = Signal()

    def __init__(self, parent: QDockWidget | None = None) -> None:
        """
        Constructs a CustomViewBox object.

        Parameters
        ----------
        parent : PlotterView, optional
            The View of the Plotter object to which this object belongs.
        """
        super(CustomViewBox, self).__init__(invertY=True)
        self.parent_plotter_viewer = parent
        self.custom_menu_edit()
        self.zoomed = False

    def custom_menu_edit(self) -> None:
        """
        Customize the context menu for the ViewBox.

        Removes standard menu items that aren't needed for image viewing and
        adds a custom option to copy the current coordinates to the clipboard.
        """
        hidden_menus = ["View All", "X axis", "Y axis", "Mouse Mode"]
        actions = self.menu.actions()
        for action in actions:
            for menu_item in hidden_menus:
                if action.text().startswith(menu_item):
                    action.setVisible(False)
                    break

        # Add custom menu options
        copy_coords = QAction("Copy Coordinates", self.menu)
        copy_coords.triggered.connect(self.parent_plotter_viewer.copy_coordinates)
        self.menu.addAction(copy_coords)

    def wheelEvent(self, e: QWheelEvent) -> None:
        """
        Handle mouse wheel events for zooming the image.

        Delegates to the parent ViewBox wheel event handler, then determines whether
        to immediately resample the image based on the image size. For very large
        images (over 5 GiB), sets a flag to defer resampling until explicitly triggered.

        Parameters
        ----------
        e : QWheelEvent
            The wheel event.
        """
        super().wheelEvent(e)
        if self.parent_plotter_viewer.image_size > 5368709120:  # 5 GiB
            self.zoomed = True
        else:
            self.auto_resample_signal.emit()
            self.parent_plotter_viewer.emit_controller_instance_signal.emit(
                "widget_interacted_signal"
            )

    def mouseDragEvent(self, e: QMouseEvent) -> None:
        """
        Handle mouse drag events for panning the image.

        Accepts all drag events and emits a signal to trigger image resampling
        when the drag operation finishes.

        Parameters
        ----------
        e : QMouseEvent
            The mouse drag event.
        """
        e.accept()
        if e.isFinish():
            self.auto_resample_signal.emit()
        super().mouseDragEvent(e)
