from PySide6.QtCore import (
    QThread,
    QPointF,
)

import math
import numpy as np
from typing import Callable

from sarpy.visualization import remap
from sarpy.io.complex.converter import SICDTypeReader

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.fileworker import \
    FileOpenWorker
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.log_remap import Logarithmic


class Model:
    """
    The data model component of Plotter.

    Manages reading data from the file, decimation / undecimation,
    data remapping, and coordinates calculations.

    Attributes
    ----------
    coordinate_mode : str
        String indicating how coordinates are represented.
    data_shape_height : int
        The number of rows in the 2D array read from the SICD file.
    data_shape_width : int
        The number of columns in the 2D array read from the SICD file.
    decimation_factor : int
        Factor by which the data has been decimated to be displayed in the given window.
    file_name : str
        The name of the SICD file being loaded.
    image_loaded : bool
        Whether or not a SICD image has been loaded.
    max_decimated_image_height : int
        The number of rows in the decimated data 2D array.
    max_decimated_image_width : int
        The number of columns in the decimated data 2D array.
    pre_remapped_data : list or np.ndarray
        Data that has been decimated, but not remapped.
    reader : SICDTypeReader or None
        Object that reads SICD data into a numpy array.
    remap_function : Callable
        Function dictating how to remap the data.
    resize_event : bool
        A flag indicating whether a resize event has occurred.
    step_size : int
        Decimation factor adjusted for zoom.
    thread : QThread
        Thread to handle opening a file without freezing the UI.
    window_height : float
        Height of the display window in pixels.
    window_width : float
        Width of the display window in pixels.
    worker : FileOpenWorker
        Object to handle running functions in a thread.
    xmin_map_to_full_image : int
        TODO: add
    ymin_map_to_full_image : int
        TODO: add
    """

    image_loaded_exception = RuntimeError(
        "function may not be called before an image is loaded onto the plot"
    )

    def __init__(self) -> None:
        """
        Construct a plotter.Model object.

        Assigns reasonable values to all attributes.
        """
        self.resize_event = 0  # Note: required by Annotation
        self.reader = None
        self.remap_function = remap.Density()
        self.pre_remapped_data = []
        self.decimation_factor = 1
        self.xmin_map_to_full_image = 0
        self.ymin_map_to_full_image = 0
        self.file_name = ""
        self.coordinate_mode = "DMS"
        self.window_width = 0
        self.window_height = 0

        # threading vars
        self.thread = None
        self.worker = None

        # post image loaded vars
        self.max_decimated_image_width = 0
        self.max_decimated_image_height = 0
        self.data_shape_height = 0
        self.data_shape_width = 0
        self.step_size = 1

    @property
    def image_loaded(self) -> bool:
        """
        Cast `reader` to bool to provide a more readable way of 
        determining whether an image is loaded.

        Returns
        -------
        bool
            Whether or not an image is loaded.
        """
        return bool(self.reader)

    def set_file_name(self, file_name: str) -> None:
        """
        Set the file name for the current plot widget.

        Stores the file name for later reference.

        Parameters
        ----------
        file_name : str
            The name of the file being displayed.
        """
        self.file_name = file_name

    def get_file_name(self) -> str:
        """
        Retrieve the file name of the current plot widget.

        Returns the stored file name associated with this widget.

        Returns
        -------
        str
            The name of the file being displayed.
        """
        return self.file_name

    def prepare_to_load_image(
        self, file_name: str, window_width: float, window_height: float
    ) -> None:
        """
        Set necessary attributes in preparation for loading an image.

        Parameters
        ----------
        file_name : str
            The name of the file to be loaded.
        window_width : float
            The width of the display window in pixels.
        window_height : float
            The height of the display window in pixels.
        """
        self.file_name = file_name
        self.window_width = window_width
        self.window_height = window_height

    def threaded_display_image(
        self, reader: SICDTypeReader, run_function: Callable
    ) -> tuple[FileOpenWorker, QThread]:
        """
        Load and display an image using a worker thread to prevent UI freezing.

        Creates a worker thread to handle the potentially time-consuming operation of
        loading and displaying a large image file. Sets up signal connections to manage
        the UI state during loading and after completion.

        Parameters
        ----------
        reader : SICDTypeReader
            The file reader object that provides access to the image data.
        run_function : Callable
            The function to be run in the thread.
        """
        self.thread = QThread()

        self.worker = FileOpenWorker(reader, run_function)

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished_signal.connect(self.thread.quit)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        return self.worker, self.thread

    def load_image(self, reader: SICDTypeReader) -> np.ndarray:
        """
        Load an image, process it, and return its processed data.

        Reads the data from the file, decimates it based on the size of the 
        display window, and remaps it according to the remap function. Returns 
        the resulting data for display.

        Parameters
        ----------
        reader : SICDTypeReader
            The file reader object that provides access to the image data.
        
        Returns
        -------
        np.ndarray
            The decimated and remapped data. A two-dimensonal array of bytes.
        """
        image_width = reader.get_data_size_as_tuple()[0][1]
        image_height = reader.get_data_size_as_tuple()[0][0]

        decimation_factor = max(
            image_width / self.window_width, image_height / self.window_height
        )

        decimated_data = reader[
            :: int(math.ceil(decimation_factor)), :: int(math.ceil(decimation_factor))
        ]
        self.pre_remapped_data = decimated_data

        self.max_decimated_image_width = len(decimated_data[0])
        self.max_decimated_image_height = len(decimated_data)

        remapped_data = self.remap_function(decimated_data)

        self.reader = reader
        self.data_shape_height = image_height
        self.data_shape_width = image_width
        self.decimation_factor = int(math.ceil(decimation_factor))
        self.step_size = self.decimation_factor

        return remapped_data

    def fix_window_size(
        self, window_width: float, window_height: float
    ) -> tuple[int, int]:
        """
        Update image dimensions following a change to the viewing window size.

        Recalculates the decimation factor and display window dimensions based on the 
        new window width and height. Calculates and returns the new dimensions of the 
        decimated image.

        Parameters
        ----------
        window_width : float
            The width of the display window in pixels.
        window_height : float
            The height of the display window in pixels.

        Returns
        -------
        x_width : int
            The new width of the decimated image.
        y_height : int
            The new height of the decimated image

        Raises
        ------
        RuntimeError
            Raised if no image is loaded. 
        """
        if not self.image_loaded:
            raise Model.image_loaded_exception

        self.window_width = window_width
        self.window_height = window_height

        stepW = self.data_shape_width / self.window_width
        stepH = self.data_shape_height / self.window_height

        self.decimation_factor = int(max(math.ceil(stepW), math.ceil(stepH)))

        x_width = int(math.ceil(self.data_shape_width / self.decimation_factor))
        y_height = int(math.ceil(self.data_shape_height / self.decimation_factor))
        return x_width, y_height

    def get_decimated_image(
        self,
        xmin_view_box: float,
        xmax_view_box: float,
        ymin_view_box: float,
        ymax_view_box: float,
    ) -> tuple[np.ndarray, int, int, int, int]:
        """
        Decimate and remap image data.

        TODO: elaborate

        Parameters
        ----------
        xmin_view_box : float
            The X minimum of the image viewbox.
        xmax_view_box : float
            The X maximum of the image viewbox.
        ymin_view_box : float
            The Y minimum of the image viewbox.
        ymax_view_box : float
            The Y maximum of the image viewbox.

        Returns
        -------
        np.ndarray
            The decimated and remapped data. A two-dimensonal array of bytes.
        int
            X coordinate for the viewing rect of the image.
        int
            Y coordinate for the viewing rect of the image.
        int
            Width of the viewing rect for the image.
        int
            Height of the viewing rect for the image.

        Raises
        ------
        RuntimeError
            Raised if no image is loaded. 
        """
        if not self.image_loaded:
            raise Model.image_loaded_exception

        # Calculate the max decimated image width and height
        self.max_decimated_image_width = int(
            math.ceil(
                self.data_shape_width
                / max(
                    int(math.ceil(self.data_shape_width / self.window_width)),
                    int(math.ceil(self.data_shape_height / self.window_height)),
                )
            )
        )
        self.max_decimated_image_height = int(
            math.ceil(
                self.data_shape_height
                / max(
                    int(math.ceil(self.data_shape_width / self.window_width)),
                    int(math.ceil(self.data_shape_height / self.window_height)),
                )
            )
        )

        xmin = np.clip(math.floor(xmin_view_box), 0, self.max_decimated_image_width - 1)
        ymin = np.clip(
            math.floor(ymin_view_box), 0, self.max_decimated_image_height - 1
        )

        xmax = np.clip(math.ceil(xmax_view_box), 0, self.max_decimated_image_width - 1)
        ymax = np.clip(math.ceil(ymax_view_box), 0, self.max_decimated_image_height - 1)

        xmin_map_to_full_image = xmin * self.decimation_factor
        ymin_map_to_full_image = ymin * self.decimation_factor

        xmax_map_to_full_image = xmax * self.decimation_factor
        ymax_map_to_full_image = ymax * self.decimation_factor

        self.xmin_map_to_full_image = xmin_map_to_full_image
        self.ymin_map_to_full_image = ymin_map_to_full_image

        step_size = int(
            math.ceil(
                max(
                    (xmax_map_to_full_image - xmin_map_to_full_image)
                    / self.window_width,
                    (ymax_map_to_full_image - ymin_map_to_full_image)
                    / self.window_height,
                )
            )
        )
        step_size = max(step_size, 1)

        self.step_size = step_size
        decimated_data = self.reader[
            ymin_map_to_full_image:ymax_map_to_full_image:step_size,
            xmin_map_to_full_image:xmax_map_to_full_image:step_size,
        ]
        self.pre_remapped_data = decimated_data
        remappedData = self.remap_function(decimated_data)

        return remappedData, xmin, ymin, xmax - xmin, ymax - ymin

    def change_remap_method(self, method: str) -> np.ndarray | None:
        """
        Change the function used to remap data. 
        
        Remaps and returns the data if possible, otherwise returns None.

        Parameters
        ----------
        method : str
            The name of the new remap method.

        Returns
        -------
        np.ndarray or None
            The decimated and remapped data. A two-dimensonal array of bytes.
        """
        if method == "Density":
            self.remap_function = remap.Density()
        elif method == "Brighter":
            self.remap_function = remap.Brighter()
        elif method == "Darker":
            self.remap_function = remap.Darker()
        elif method == "High Contrast":
            self.remap_function = remap.High_Contrast()
        elif method == "Linear":
            self.remap_function = remap.Linear()
        elif method == "Logarithmic":
            self.remap_function = Logarithmic()
        elif method == "PEDF":
            self.remap_function = remap.PEDF()
        elif method == "NRL":
            self.remap_function = remap.NRL()

        if len(self.pre_remapped_data) > 0:
            return self.remap_function(self.pre_remapped_data)

        return None

    def switch_coordinate_mode(self) -> str:
        """
        Change the display format of the coordinates. 

        Returns
        -------
        str
            The new coordinate format.
        """
        if self.coordinate_mode == "DMS":
            self.coordinate_mode = "DD"
            return "0.0000000°, 0.00000000°"
        elif self.coordinate_mode == "DD":
            self.coordinate_mode = "XY"
            return "0, 0"
        elif self.coordinate_mode == "XY":
            self.coordinate_mode = "DMS"
            return "0° 0′ 0.00000″ N, 0° 0′ 0.00000″ E"
        else:
            return "ERROR"

    def get_coordinates_under_mouse(self, x: float, y: float) -> tuple[str, str]:
        """
        Retrive the coordinates under the mouse in the chosen format.

        Converts from window coordinates to image coordinates, and then to geographic coordinates.
        Returns coordinates in the desired format.

        Params
        ------
        x : float
            X-axis window coordinate.
        y : float
            Y-axis window coordinate.

        Returns
        -------
        str
            Latitude coordinate in the desired format.
        str
            Longitude coordinate in the desried format.

        Raises
        ------
        RuntimeError
            Raised if no image is loaded. 
        """
        if not self.image_loaded:
            raise Model.image_loaded_exception

        i = int(
            np.clip(
                x * math.ceil(self.step_size) + self.xmin_map_to_full_image,
                0,
                self.data_shape_width - 1,
            )
        )
        j = int(
            np.clip(
                y * math.ceil(self.step_size) + self.ymin_map_to_full_image,
                0,
                self.data_shape_height - 1,
            )
        )

        geoCoords = self.reader.sicd_meta.project_image_to_ground_geo(
            (j, i), projection_type="HAE"
        )
        if self.coordinate_mode == "DMS":
            lat = self._deg_to_dms(geoCoords[0], "latitude", 5)
            lon = self._deg_to_dms(geoCoords[1], "longitude", 5)
        elif self.coordinate_mode == "DD":
            lat = "{d:.8f}°".format(d=geoCoords[0])
            lon = "{d:.8f}°".format(d=geoCoords[1])
        elif self.coordinate_mode == "XY":
            lat = str(i)
            lon = str(j)

        return lat, lon

    def _deg_to_dms(
        self, deg: float, axis: str | None = None, ndp: int = 6
    ) -> str | tuple[int, int, float]:
        """
        Convert decimal degrees to degrees-minutes-seconds format.

        Transforms a decimal degree value into the traditional DMS format with
        appropriate hemisphere designation for geographic coordinates.

        Parameters
        ----------
        deg : float
            The angle in decimal degrees.
        axis : str, optional
            Specifies whether this is a 'latitude' or 'longitude' value for
            determining the hemisphere designation. If None, returns the
            components as a tuple.
        ndp : int, optional
            Number of decimal places for the seconds component. Default is 6.

        Returns
        -------
        str or tuple
            If axis is specified: Formatted string in DMS format with hemisphere.
            If axis is None: tuple of (degrees, minutes, seconds).
        """
        m, s = divmod(np.abs(deg) * 3600, 60)
        d, m = divmod(m, 60)
        if deg < 0:
            d = -d
        d, m = int(d), int(m)

        if axis:
            if axis == "latitude":
                hemi = "N" if d >= 0 else "S"
            elif axis == "longitude":
                hemi = "E" if d >= 0 else "W"
            else:
                hemi = "?"
            return "{d:d}° {m:d}′ {s:.{ndp:d}f}″ {hemi:1s}".format(
                d=np.abs(d), m=m, s=s, hemi=hemi, ndp=ndp
            )
        return d, m, s

    def undecimate_pixel_coordinates(
        self, pixel_coords: list[QPointF]
    ) -> list[list[int]] | list[int]:
        """
        Convert pixel coordinates from decimated to full-resolution image space.

        Translates coordinates from the downsampled (decimated) representation back to their
        original positions in the full-resolution image, accounting for the current scaling
        and offsets.

        Parameters
        ----------
        pixel_coords : list
            A list of QPointF objects representing coordinates in the decimated image.

        Returns
        -------
        list or list of lists
            For a single coordinate: [y, x] in the full-resolution image.
            For multiple coordinates: A list of [y, x] coordinates in the full-resolution image.
        """
        undecimated_pixel_coords = []
        for pixel_coord in pixel_coords:
            undecimated_pixel_coords.append(
                [
                    int(pixel_coord.y() * self.step_size + self.ymin_map_to_full_image),
                    int(pixel_coord.x() * self.step_size + self.xmin_map_to_full_image),
                ]
            )
        if len(undecimated_pixel_coords) < 2:
            return undecimated_pixel_coords[0]
        else:
            return undecimated_pixel_coords
