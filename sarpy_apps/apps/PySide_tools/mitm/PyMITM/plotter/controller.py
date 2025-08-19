from PySide6.QtCore import (
    QObject,
    QPointF,
)
from PySide6.QtGui import (
    QAction,
    QDropEvent,
)
from PySide6.QtWidgets import (
    QWidget,
    QGraphicsSceneHoverEvent,
)

from typing import Callable
from numpy import ndarray
from sarpy.io.complex.converter import SICDTypeReader

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.canvas import \
    GeometryROI
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.model import Model
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.view import View


class Controller(QObject):
    """
    Main controller class that connects the viewer UI and data model for Plotter.

    Plotter is designed to handle display, loading, and processing of image data in MITM. 
    It is capable of loading SICD images, decimating them according to the display window 
    size and remapping them, and displaying them to the user.

    Features include:
        - Progress bar for loading operations
        - Image display with pan/zoom capabilities
        - Coordinate display with multiple format options (DMS, DD, XY)
        - Drag and drop support for loading image files
        - Image remapping options (Density, Brightness, Contrast, etc.)
        - Aspect ratio control
        - Efficient image decimation for handling large images

    Attributes
    ----------
    model : Model
        The object that contains and manipulates data.
    viewer : View
        The object that handles the GUI.
        
    """

    def __init__(
        self,
        add_geometry_action: QAction | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize a Controller object.

        Parameters
        ----------
        add_geometry_action : QAction, optional
            Action to add geometries to the plot. Default is None.
        parent : QWidget, optional
            The parent widget. Default is None.
        """
        self.model = Model()
        self.viewer = View(add_geometry_action=add_geometry_action, parent=parent)

        # connections
        self.viewer.plot_widget.getPlotItem().getViewBox().auto_resample_signal.connect(
            self.resample_image
        )
        self.viewer.plot_widget.resize_timer.timeout.connect(
            self.__emit_resize_finished
        )
        self.viewer.remapMethodComboBox.currentTextChanged.connect(
            self.remap_method_changed
        )
        self.viewer.coordinatesButton.clicked.connect(self.switch_coordinate_mode)
        self.viewer.aspectRatioComboBox.currentTextChanged.connect(
            self.aspect_ratio_changed
        )
        self.viewer.emit_controller_instance_signal.connect(
            self.emit_controller_instance_handler
        )
        self.viewer.metaIconButton.clicked.connect(self.metaicon_button_pressed)

        # overriding methods
        self.viewer.img.hoverEvent = self.image_hover_event
        self.viewer.plot_widget.dropEvent = self.drop_event

    def set_size(self, size: int) -> None:
        """
        Set the size of the loaded image in bytes.

        Parameters
        ----------
        size : int
            The size of the image in bytes.
        """
        self.viewer.image_size = size

    def get_file_name(self) -> str:
        """
        Get the name of the loaded SICD file.

        Returns
        -------
        str
            The name of the loaded SICD file.
        """
        return self.model.get_file_name()

    def threaded_display_image(self, reader: SICDTypeReader) -> None:
        """
        Load and display an image using a worker thread to prevent UI freezing.

        Creates a worker thread to handle the potentially time-consuming operation of
        loading and displaying a large image file. Sets up signal connections to manage
        the UI state during loading and after completion.

        Parameters
        ----------
        reader : SICDTypeReader
            The file reader object that provides access to the image data.
        """
        worker, thread = self.model.threaded_display_image(reader, self.load_image)

        worker.started_signal.connect(self.viewer.reject_drops)
        worker.finished_signal.connect(self.viewer.accept_drops)
        worker.finished_signal.connect(self.update_aspect_ratio)

        thread.finished.connect(self.viewer.hide_progress_bar)
        thread.start()

        self.viewer.progress_bar.show()

    def load_image(self, reader: SICDTypeReader) -> None:
        """
        Load the SICD image onto the plot.

        Loads the image data, calculates appropriate decimation factors based
        on image and window size, and updates the plot widget with the processed data.

        Parameters
        ----------
        reader : SICDTypeReader
            The file reader object that provides access to the image data.
        """
        remapped_data = self.model.load_image(reader)

        self.viewer.img.setImage(remapped_data)
        self.viewer.enhancePushButton.setEnabled(True)
        self.viewer.plot_widget.getPlotItem().getViewBox().autoRange()

    def resample_image(self) -> None:
        """
        Resample the image data based on the current view and window size.

        Calculates appropriate decimation factors and view bounds to efficiently
        display large images at the current zoom level and window size. Only resamples
        if the window dimensions have changed or if the view range has changed.
        Uses adaptive sampling to balance detail level with performance.

        Does nothing if no image is loaded.
        """
        if not self.model.image_loaded:
            return

        # determine window size
        window_width = self.viewer.get_plot_window_width()
        window_height = self.viewer.get_plot_window_height()

        # if window size has changed since last resample, handle that
        if (
            self.model.window_width != window_width
            or self.model.window_height != window_height - 5.0
        ):
            width, height = self.model.fix_window_size(window_width, window_height)
            self.viewer.set_image_rect(0, 0, width - 1, height - 1)

        xmin_view_box = self.viewer.plot_widget.getViewBox().viewRange()[0][0]
        xmax_view_box = self.viewer.plot_widget.getViewBox().viewRange()[0][1]
        ymin_view_box = self.viewer.plot_widget.getViewBox().viewRange()[1][0]
        ymax_view_box = self.viewer.plot_widget.getViewBox().viewRange()[1][1]

        # do the resample
        try:
            remappedData, x, y, w, h = self.model.get_decimated_image(
                xmin_view_box, xmax_view_box, ymin_view_box, ymax_view_box
            )
            self.viewer.img.setImage(remappedData)
            self.viewer.set_image_rect(x, y, w, h)
        except:
            pass

    def __emit_resize_finished(self) -> None:
        """
        Handle the completion of a resize operation after the debounce period.

        Triggered when the resize timer expires, indicating that resizing has finished.
        Resamples the displayed image to match the new dimensions and notifies
        listeners that the resize operation is complete.
        """
        self.resample_image()
        self.model.resize_event = 1
        self.viewer.plot_widget_resize_finished_signal.emit(self)

    def remap_method_changed(self, method: Callable) -> None:
        """
        Update the image remapping function based on the selected method.

        Changes the remapping function used to display the image data based on the
        selected method name, and applies the new function to the current image data.
        Supports various remapping methods like Density, Brighter, Darker, etc.

        Parameters
        ----------
        method : str
            The name of the remapping method to use.
        """
        remapped_data = self.model.change_remap_method(method)
        if remapped_data is not None:
            self.viewer.img.setImage(remapped_data)
        self.viewer.parent().widget_interacted_signal.emit(self)

    def switch_coordinate_mode(self) -> None:
        """
        Toggle between different coordinate display formats.

        Cycles through three coordinate display modes:
        - DMS (Degrees, Minutes, Seconds)
        - DD (Decimal Degrees)
        - XY (Pixel Coordinates)
        Updates the coordinate button text to show the appropriate format.
        """
        text = self.model.switch_coordinate_mode()
        self.viewer.coordinatesButton.setText(text)

    def update_aspect_ratio(self) -> None:
        """
        Update the aspect ratio based on the current selection in the combo box.

        Calls aspect_ratio_changed with the currently selected aspect ratio option.
        """
        self.aspect_ratio_changed(self.viewer.aspectRatioComboBox.currentText())

    def aspect_ratio_changed(self, ratio: str) -> None:
        """
        Change the image aspect ratio based on the selected option.

        Updates the aspect ratio locking of the plot widget based on the selected ratio.
        Supports 'Square' for 1:1 aspect ratio or 'Aspect' for requesting the actual
        image aspect ratio from the parent.

        Parameters
        ----------
        ratio : str
            The aspect ratio option to apply ('Square' or 'Aspect').
        """
        if self.model.reader:
            if ratio == "Square":
                self.viewer.plot_widget.setAspectLocked(ratio=1)
            elif ratio == "Aspect":
                self.viewer.parent().request_aspect_ratio_signal.emit(self)
        self.viewer.parent().widget_interacted_signal.emit(self)

    def image_hover_event(self, event: QGraphicsSceneHoverEvent) -> None:
        """
        Update coordinate display when the mouse hovers over the image.

        Calculates the corresponding coordinates (both pixel and geographic) for the
        current mouse position and updates the coordinate display. Also triggers
        resampling if the view has been zoomed.

        Parameters
        ----------
        event : QGraphicsSceneHoverEvent
            The hover event containing the mouse position.
        """
        if event.isExit():
            return
        pos = event.pos()

        self.viewer.handle_hover_event(pos)

        try:
            self.viewer.coordinatesButton.setVisible(True)
            lat, lon = self.model.get_coordinates_under_mouse(pos.x(), pos.y())
            self.viewer.coordinatesButton.setText(lat + ", " + lon)
        except:
            pass

    def setup_file(self, full_file_name: str, file_is_dropped: bool) -> None:
        """
        Get the model and viewer ready to load a file and request that a file be loaded.

        Perform necessary setup in the model and viewer, then emit a signal indicating that
        the plotter object is ready to load the image file. Also emits a signal indicating 
        that the widget is being interacted with.

        Parameters
        ----------
        full_file_name : str
            The full path to the file.
        file_is_dropped : bool
            Bool indicating if the file was dropped onto the plot or double-clicked
            in MITM's file dialog.
        """
        window_width = self.viewer.get_plot_window_width()
        window_height = self.viewer.get_plot_window_height()
        file_name = full_file_name.split("/")[-1]

        self.model.prepare_to_load_image(file_name, window_width, window_height)
        self.viewer.prepare_to_load_image(full_file_name)
        self.viewer.parent().file_load_requested_signal.emit(
            full_file_name, self, file_is_dropped
        )
        self.viewer.parent().widget_interacted_signal.emit(self)

    def drop_event(self, e: QDropEvent) -> None:
        """
        Handle file drop events onto the plot widget.

        Processes dropped NITF/NTF files by updating the widget's dimensions,
        emitting signals to load the file, and updating the widget title with
        the file name. Only handles files with .nitf or .ntf extensions.

        Parameters
        ----------
        e : QDropEvent
            The drop event containing the file information.
        """
        droppedFile = e.mimeData().text()

        if droppedFile.endswith(".nitf") or droppedFile.endswith(".ntf"):
            self.setup_file(droppedFile, True)
            e.acceptProposedAction()

    def change_color(self, is_selected: bool, dark_mode: bool) -> None:
        """ 
        Update the widget stylesheet based on MITM's appearance and whether or not
        the widget is selected.

        Parameters
        ----------
        is_selected
            Whether or not the widget MITM's currently selected widget.
        dark_mode
            Whether or not MITM's appearance is set to dark mode.
        """
        self.viewer.change_color(is_selected, dark_mode)

    def emit_controller_instance_handler(self, signal_name: str) -> None:
        signal = getattr(self.viewer.parent(), signal_name)
        signal.emit(self)

    def metaicon_button_pressed(self) -> None:
        """
        Handle meta-icon button press events.

        Emits signals to open the meta-icon display for the current file and
        to indicate that this widget has been interacted with.
        """
        self.viewer.parent().open_meta_icon_signal.emit(self.model.get_file_name())
        self.viewer.parent().widget_interacted_signal.emit(self)

    ## Begin API for Annotation

    @property
    def image_loaded(self) -> bool:
        """Get whether or not an image is loaded"""
        return self.model.image_loaded

    @property
    def decimation_factor(self) -> int:
        """Get the decimation factor"""
        return self.model.decimation_factor

    @property
    def resize_event(self) -> int:
        """Get the resize event flag"""
        return self.model.resize_event

    @property
    def remap_function(self) -> Callable:
        """Get the current remap function"""
        return self.model.remap_function

    @property
    def reader(self) -> SICDTypeReader:
        """
        Get the SICD file reader

        Raises
        ------
        RuntimeError
            Cannot access the reader if no image is loaded.
        """
        if not self.image_loaded:
            raise Model.image_loaded_exception

        return self.model.reader

    def update_geometry_ordering(self) -> None:
        """
        Update the Z-ordering of geometries.

        Sets the current geometry to the lowest Z-value and orders other geometries above it.
        """
        self.viewer.canvas.update_geometry_ordering()

    def update_current_geometry(self, geometry: GeometryROI|None) -> None:
        """
        Set the current geometry.

        Parameters
        ----------
        geometry : GeometryROI or None
            The geometry to set as current.
        """
        self.viewer.canvas.set_current_geometry(geometry)
        self.viewer.canvas.render_geometry_selection()

    def get_geometries(self) -> list[GeometryROI]:
        """
        Get all geometries on the canvas.

        Returns
        -------
        List[GeometryROI]
            List of all geometries.
        """
        return self.viewer.canvas.get_geometries()

    def add_geometry(self, new_geometry: GeometryROI) -> None:
        """ 
        Add a new geometry to the plot and canvas, then set it as current.

        Parameters
        ----------
        new_geometry : GeometryROI
            The geometry to add.
        """
        self.viewer.plot_widget.addItem(new_geometry)
        self.viewer.canvas.add_geometry(new_geometry)
        self.viewer.canvas.set_current_geometry(new_geometry)

    def get_current_geometry(self) -> GeometryROI | None:
        """
        Get the current geometry.

        Returns
        -------
        GeometryROI or None
            The current geometry.
        """
        return self.viewer.canvas.get_current_geometry()

    def render_geometry_selection(self) -> None:
        """
        Update the visual appearance of geometries based on selection state.

        The selected geometry gets a solid line, while others get dashed lines.
        """
        self.viewer.canvas.render_geometry_selection()

    def remove_geometry(self, geometry : GeometryROI) -> None:
        """
        Remove a geometry from the plot and canvas.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to remove.
        """
        self.viewer.plot_widget.removeItem(geometry)
        self.viewer.canvas.remove_geometry(geometry)

    def get_plot_center_coordinates(self) -> tuple[float, float]:
        """
        Get the center coordinates of the plot window.

        Returns
        -------
        tuple[float, float]
            The (x, y) coordinates of the plot center.
        """
        x = self.viewer.plot_widget.getViewBox().viewRect().center().x()
        y = self.viewer.plot_widget.getViewBox().viewRect().center().y()
        return x, y

    def get_current_cursor_image_position(self) -> list[float] | None:
        """
        Get the current cursor position within the image.

        Returns the stored cursor position coordinates from the last mouse hover event.

        Returns
        -------
        list[float] | None
            The current cursor position as [x, y] coordinates in the image, or None if not set.
        """
        return self.viewer.get_current_cursor_image_position()

    def project_image_to_ground_geo(self, coord: list[float], type: str) -> ndarray:
        """
        Transforms image coordinates to ground plane WGS-84 coordinate via the algorithm(s)
        described in SICD Image Projections document.

        Parameters
        ----------
        im_points : numpy.ndarray|list|tuple
            the image coordinate array
        projection_type : str
            One of `['PLANE', 'HAE', 'DEM']`. Type `DEM` is a work in progress.
        
        Returns
        -------
        numpy.ndarray
            Ground Plane Point (in ECF coordinates) corresponding to the input image coordinates.
        
        Raises
        ------
        RuntimeError
            Raised if no image is loaded. 
        """
        if not self.model.image_loaded:
            raise Model.image_loaded_exception

        return self.model.reader.sicd_meta.project_image_to_ground_geo(
            coord, projection_type=type
        )

    def project_ground_to_image_geo(
        self, coord: list[float], ordering: str
    ) -> tuple[ndarray, ndarray | float, ndarray | int]:
        """
        Transforms a 3D Lat/Lon/HAE point to pixel (row/column) coordinates. This is
        implemented in accordance with the SICD Image Projections Description Document.
        **Really Scene-To-Image projection.**"

        Parameters
        ----------
        coords : numpy.ndarray|tuple|list
            ECF coordinate to map to scene coordinates, of size `N x 3`.
        ordering : str
            If 'longlat', then the input is `[longitude, latitude, hae]`.
            Otherwise, the input is `[latitude, longitude, hae]`. Passed through
            to :func:`sarpy.geometry.geocoords.geodetic_to_ecf`.

        Returns
        -------
        image_points: numpy.ndarray
            The determined image point array, of size `N x 2`. Following the
            SICD convention, he upper-left pixel is [0, 0].
        delta_gpn: numpy.ndarray|float
            Residual ground plane displacement (m).
        iterations: numpy.ndarray|int
            The number of iterations performed.

        Raises
        ------
        RuntimeError
            Raised if no image is loaded. 
        """
        if not self.model.image_loaded:
            raise Model.image_loaded_exception

        return self.model.reader.sicd_meta.project_ground_to_image_geo(
            coord, ordering=ordering
        )

    def get_view_range(self) -> list[list[float]]:
        """
        Get the viewbox’s visible range.
        
        Returns
        -------
        list[list[float]]
            Coordinates of the visible range in the form `[[xmin, xmax], [ymin, ymax]]`.
        """
        return self.viewer.plot_widget.getViewBox().viewRange()

    def get_aspect_ratio(self) -> float:
        """
        Get the aspect ratio of plot viewbox.
        
        Returns 
        -------
        float
            The aspect ratio.
        """
        return self.viewer.plot_widget.getViewBox().getAspectRatio()

    def get_undecimated_pixel_coordinates(
        self, coords_list: list[QPointF]
    ) -> list[list[int]] | list[int]:     
        """
        Converts QPointF coordinates to undecimated pixel coordinates.

        Parameters
        ----------
        coords_list : list[QPointF]
            List of coordinates to convert.

        Returns
        -------
        list[list[int]] | list[int]
            If `len(coords_list) > 1` returns coordinates in the form `[[x1, y1], [x2, y2],...]`;
            Else, returns coordinates in the form `[x1, y1]`.
        """
        pixel_coords = []
        for coord in coords_list:
            pixel_coords.append(self.viewer.img.mapFromScene(coord))
        return self.model.undecimate_pixel_coordinates(pixel_coords)

    def clear_resize_event_flag(self) -> None:
        """Clears the flag indicating that a resize event occurred."""
        self.model.resize_event = 0
