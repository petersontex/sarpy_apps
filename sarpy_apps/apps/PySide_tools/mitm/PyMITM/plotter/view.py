from PySide6.QtCore import Qt, Signal, QRect, QTimer, QPointF
from PySide6.QtWidgets import (
    QDockWidget,
    QProgressBar,
    QVBoxLayout,
    QSizePolicy,
    QWidget,
)
from PySide6.QtGui import (
    QGuiApplication,
    QAction,
    QResizeEvent,
    QMouseEvent,
    QCloseEvent,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
)

import pyqtgraph as pg

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.pyui.plot_widget_dock import \
    Ui_DockWidget
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.stylesheet import \
    MITMStyleSheet
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.tooltips import ToolTips
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.viewbox import \
    CustomViewBox
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.canvas import Canvas


class View(QDockWidget, Ui_DockWidget):
    """
    A specialized QDockWidget for displaying and manipulating images.

    The widget include an embedded PyQtGraph plot widget configured
    for image display. Enables the loading, viewing, and manipulation
    of SICD images.

    Attributes
    ----------
    image_size : int
        Size of the SICD image in bytes.
    plot_widget : PlotWidget
        Handles plotting the image.
    canvas : Canvas
        Keeps track of geometries drawn on the plot.
    img : ImageItem
        Displays the image.
    _current_cursor_position : list[float] or None
        The current coordinates of the mouse cursor.

    Signals
    -------
    plot_widget_resize_finished_signal
        Emitted when the user has finished resizing the dockwidget.
    emit_controller_instance_signal
        Emitted when the user interacts with the dock in any way
        to signal the Controller to emit the specified signal with
        the controller instance as the argument.

    Methods
    -------
    get_current_cursor_image_position()
        Retrieve the current position of the cursor within the image.
    set_current_cursor_image_position(current_pos)
        Set the current cursor position within the image.
    set_image_rect(x, y, w, h)
        Set view rectangle for img to occupy.
    copy_coordinates()
        Copy the current coordinates to the system clipboard.
    prepare_to_load_image(file)
        Update the GUI to reflect that a file has been loaded.
    get_plot_window_width()
        Get the current width of the plot window.
    get_plot_window_height()
        Get the current height of the plot window.
    change_color(is_selected, dark_mode):
        Switch between light mode and dark mode by updating the stylesheet.
    """

    plot_widget_resize_finished_signal = Signal(
        object, name="plot_widget_resize_signal"
    )
    emit_controller_instance_signal = Signal(
        str, name="emit_controller_instance_signal"
    )

    def __init__(
        self,
        add_geometry_action: QAction | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize a View.

        Sets up the UI components, event handling, and signal
        connections for image loading, viewing, and manipulation.

        Parameters
        ----------
        add_geometry_action : QAction, optional
            QAction to handle adding new geometries to the canvas.
            Default is None.
        parent : QWidget, optional
            The parent widget. Default is None.
        """
        super(View, self).__init__(parent, focusPolicy=Qt.WheelFocus)
        self.setupUi(self)

        self.image_size = 0  # this has to be in the viewer

        self.plot_widget = pg.PlotWidget(
            self.dockWidgetContents, viewBox=CustomViewBox(self)
        )
        self.gridLayout.addWidget(self.upperControlsWidget, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.plot_widget, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.controlsWidget, 2, 0, 1, 1)

        self.canvas = Canvas()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.plot_widget.setLayout(layout)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(200)
        self.plot_widget.layout().addWidget(self.progress_bar)
        self.progress_bar.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setRange(0, 0)

        self.progress_bar.setStyleSheet(MITMStyleSheet.Plotter.progress_bar)
        self.progress_bar.hide()

        self.plot_widget.setAspectLocked()
        self.plot_widget.setAcceptDrops(True)
        self.plot_widget.getPlotItem().getViewBox().suggestPadding = lambda *_: 0.0
        self.plot_widget.getPlotItem().hideAxis("bottom")
        self.plot_widget.getPlotItem().hideAxis("left")
        self.plot_widget.getPlotItem().setMenuEnabled(
            enableMenu=False, enableViewBoxMenu=None
        )

        if add_geometry_action is not None:
            self.plot_widget.getViewBox().menu.addAction(add_geometry_action)

        self.img = pg.ImageItem(axisOrder="row-major")
        self.plot_widget.addItem(self.img)

        self._current_cursor_position = None

        self.plot_widget.dragMoveEvent = self.drag_move_event
        self.plot_widget.dragEnterEvent = self.drag_enter_event
        self.plot_widget.dragLeaveEvent = self.drag_leave_event

        self.plot_widget.mousePressEvent = self.mouse_press_event

        self.metaIconButton.setToolTip(ToolTips.Plotter.meta_icon_button())
        self.metaIconButton.setVisible(False)

        self.downsampleMethodComboBox.activated.connect(self.downsample_method_changed)
        self.downsampleMethodComboBox.setToolTip(
            ToolTips.Plotter.downsample_method_combobox()
        )

        self.remapMethodComboBox.setToolTip(ToolTips.Plotter.remap_method_combobox())
        self.aspectRatioComboBox.setToolTip(ToolTips.Plotter.aspect_ratio_combobox())

        self.plot_widget.sigRangeChanged.connect(self.update_region)
        self.enhancePushButton.setEnabled(False)

        self.coordinatesButton.setText("")
        self.coordinatesButton.setVisible(False)
        self.coordinatesButton.setToolTip(ToolTips.Plotter.coordinates())

        self.visibilityChanged.connect(self.dock_visibility_changed)
        self.dockLocationChanged.connect(self.dock_location_changed)

        # Removed controls
        self.enhancePushButton.hide()
        self.coordinatesLabel.hide()

        # Hide these controls until implemented
        self.indexSpinBox.hide()
        self.indexLabel.hide()
        self.debugPushButton.hide()

        self.plot_widget.resize_timer = QTimer(self.plot_widget)
        self.plot_widget.resize_timer.setSingleShot(True)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handle resize events for the plot widget.

        Overrides the parent class resize event handler and sets up a timer to debounce
        multiple consecutive resize events, preventing excessive computation during
        window resizing operations.

        Parameters
        ----------
        event : QResizeEvent
            The resize event object.
        """
        super().resizeEvent(event)
        self.plot_widget.resize_timer.start(1000)

    def get_current_cursor_image_position(self) -> list[float] | None:
        """
        Get the current cursor position within the image.

        Returns the stored cursor position coordinates from the last mouse hover event.

        Returns
        -------
        list[float] | None
            The current cursor position as [x, y] coordinates in the image, or None if not set.
        """
        return self._current_cursor_position

    def set_current_cursor_image_position(
        self, current_cursor_position: list[float]
    ) -> None:
        """
        Set the current cursor position within the image.

        Stores the cursor position coordinates for later reference.

        Parameters
        ----------
        current_cursor_position : list
            The cursor position as [x, y] coordinates in the image.
        """
        self._current_cursor_position = current_cursor_position

    def set_image_rect(self, x: float, y: float, w: float, h: float) -> None:
        """
        Set view rectangle for img to occupy.

        Parameters
        ----------
        x : float
            Top left corner of the rectangle X.
        y : float
            Top left corner of the rectangle Y.
        w : float
            Width of the rectangle.
        h : float
            Height of the rectangle.
        """
        self.img.setRect(QRect(x, y, w, h))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events on the dock widget.

        Requests that the parent emit `widget_interacted_signal` before passing the
        event to the superclass for standard processing.

        Parameters
        ----------
        event : QMouseEvent
            The mouse press event object.
        """
        self.emit_controller_instance_signal.emit("widget_interacted_signal")
        super().mousePressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle close events for the dock widget.

        Requests that the parent emit `widget_closed_signal`  before passing the
        event to the superclass for standard processing.

        Parameters
        ----------
        event : QCloseEvent
            The close event object.
        """
        self.emit_controller_instance_signal.emit("widget_closed_signal")
        super().closeEvent(event)

    def reject_drops(self) -> None:
        """
        Disable drag and drop functionality during file loading operations.

        Called when a file load operation starts to prevent the user from dropping
        additional files while loading is in progress.
        """
        self.plot_widget.setAcceptDrops(False)

    def accept_drops(self) -> None:
        """
        Re-enable drag and drop functionality after file loading completes.

        Called when a file load operation finishes to allow the user to drop
        additional files again.
        """
        self.plot_widget.setAcceptDrops(True)

    def hide_progress_bar(self) -> None:
        """
        Hide the progress bar after an operation completes.

        Hides the progress bar widget that indicates file loading.
        """
        self.progress_bar.hide()

    def copy_coordinates(self) -> None:
        """
        Copy the current coordinates to the system clipboard.

        Copies the text from the coordinates button (which contains formatted
        geographic or pixel coordinates) to the system clipboard.
        """
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.coordinatesButton.text())

    def downsample_method_changed(self) -> None:
        """
        Handle changes to the downsample method.

        This is a placeholder method for future implementation.
        """
        pass

    def apply_aspect_ratio_to_image(self, aspectRatio: float) -> None:
        """
        Apply a specific aspect ratio to the image display.

        Sets the plot widget's aspect ratio locking to the specified value.

        Parameters
        ----------
        aspectRatio : float
            The aspect ratio value to apply.
        """
        self.plot_widget.setAspectLocked(ratio=aspectRatio)

    def update_region(self) -> None:
        """
        This is a placeholder method for future implementation.
        """
        pass

    def dock_visibility_changed(self, visible: bool) -> None:
        """
        Handle visibility changes of the dock widget.

        When the widget becomes visible, request that the parent emit
        `widget_interacted_signal` to indicate that this widget has been
        interacted with.

        Parameters
        ----------
        visible : bool
            Flag indicating whether the widget is now visible.
        """
        if visible:
            self.emit_controller_instance_signal.emit("widget_interacted_signal")

    def dock_location_changed(self) -> None:
        """
        Handle changes to the dock widget's location.

        Adjusts the widget's size when it becomes a floating window to prevent
        geometry-related errors in the Qt framework.
        """
        if self.isFloating():
            self.adjustSize()  # prevents "unable to set geometry" errors

    def handle_hover_event(self, pos: QPointF) -> None:
        """
        Update coordinate display when the mouse hovers over the image.

        Converts geographic coordinates to pixel and assignes them to the current
        mouse position. Also triggers resampling if the view has been zoomed.

        Parameters
        ----------
        pos : QPointF
            The geographic coordinates indicating mouse position
        """
        view_box = self.plot_widget.getPlotItem().getViewBox()
        if view_box.zoomed:
            view_box.auto_resample_signal.emit()
            view_box.zoomed = False
            self.emit_controller_instance_signal.emit("widget_interacted_signal")

        pixel_image_coord = self.img.mapToView(pos)
        self.set_current_cursor_image_position(
            [pixel_image_coord.x(), pixel_image_coord.y()]
        )

    def prepare_to_load_image(self, full_file_name: str) -> None:
        """
        Update the GUI to in preparation for loading a file.

        Sets the dockwidget title and shows the metaicon button.

        Parameters
        ----------
        full_file_name : str
            full path to the loaded file
        """
        self.setWindowTitle("  " + full_file_name.split("/")[-1])
        self.metaIconButton.setVisible(True)

    def drag_enter_event(self, e: QDragEnterEvent) -> None:
        """
        Handle drag enter events for the plot widget.

        Accepts drag enter events.

        Parameters
        ----------
        e : QDragEnterEvent
            The drag enter event
        """
        e.acceptProposedAction()

    def drag_leave_event(self, e: QDragLeaveEvent) -> None:
        """
        Handle drag leave events for the plot widget.

        Accepts drag leave events.

        Parameters
        ----------
        e : QDragLeaveEvent
            The drag leave event
        """
        e.accept()

    def drag_move_event(self, e: QDragMoveEvent) -> None:
        """
        Handle drag move events for the plot widget.

        Accepts drag move events.

        Parameters
        ----------
        e : QDragMoveEvent
            The drag leave event
        """
        e.acceptProposedAction()

    def mouse_press_event(self, e: QMouseEvent) -> None:
        """
        Handle mouse press events for the plot widget.

        Requests that the parent emit `widget_interacted_signal` with before
        delegating to the standard PyQtGraph mouse press event handler.

        Parameters
        ----------
        e : QMouseEvent
            The mouse press event.
        """
        self.emit_controller_instance_signal.emit("widget_interacted_signal")
        pg.PlotWidget.mousePressEvent(self.plot_widget, e)

    def get_plot_window_width(self) -> float:
        """
        Get the current width of the plot window.

        Calculates the width of the plot_widget's bounding rectangle in device
        coordinates, with a small margin adjustment.

        Returns
        -------
        float
            The width of the plot window in pixels.
        """
        width = (
            self.plot_widget.getPlotItem()
            .mapRectToDevice(self.plot_widget.getPlotItem().boundingRect())
            .width()
            - 5.0
        )
        return width

    def get_plot_window_height(self) -> float:
        """
        Get the current height of the plot window.

        Calculates the height of the plot_widget's bounding rectangle in device
        coordinates, with a small margin adjustment.

        Returns
        -------
        float
            The height of the plot window in pixels.
        """
        height = (
            self.plot_widget.getPlotItem()
            .mapRectToDevice(self.plot_widget.getPlotItem().boundingRect())
            .height()
            - 5.0
        )
        return height

    def change_color(self, is_selected: bool, dark_mode: bool) -> None:
        """
        Switch between light mode and dark mode by updating the stylesheet.

        Changes the colors used in the QDockWidget and ViewBox based on whether
        this plotter is selected, and whether the appearance is light mode or
        dark mode.

        Parameters
        ----------
        is_selected : bool
            Whether or not this plotter is selected.
        dark_mode : bool
            Whether or not the current appearance is dark mode.
        """
        self.setStyleSheet(
            MITMStyleSheet.Plotter.Widget.selected_style_sheet(dark_mode)
            if is_selected
            else ""
        )
        self.plot_widget.getPlotItem().getViewBox().setBackgroundColor(
            MITMStyleSheet.Plotter.ViewBox.get_color(is_selected, dark_mode)
        )
        self.plot_widget.getPlotItem().getViewBox().setBorder(
            color=MITMStyleSheet.Plotter.ViewBox.get_color(is_selected, dark_mode),
            width=2,
        )
