from typing import (
    List,
    Dict,
    Tuple,
    Optional,
    Union,
    Any,
    Callable,
    TypeVar,
    Type,
    cast,
    Set,
)
import pyqtgraph as pg
from numpy.typing import NDArray
import numpy as np

from PySide6.QtWidgets import (
    QWidget,
    QDockWidget,
    QFileDialog,
    QColorDialog,
    QMenu,
    QTableWidgetItem,
    QTableWidget,
    QAbstractItemView,
)
from PySide6.QtGui import QColor, QAction
from PySide6.QtCore import Qt, QMetaObject, Signal

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.pyui.annotation import Ui_Annotation
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.application_extension import ExtensibleObject

pg.setConfigOptions(imageAxisOrder="row-major")  # needed to display image properly

# Type aliases
GeometryType = TypeVar("GeometryType", bound="GeometryROI")
AnnotationFeatureType = Any


class View(QDockWidget, Ui_Annotation):
    """
    Main view class for the annotation system.

    Provides the user interface for geometry annotation operations including
    import/export, geometry table management, and preview display.

    Signals
    -------
    add_geometry_signal : Signal(list)
        Emitted when a geometry should be added at specified coordinates.
    voids_toggle_signal : Signal(bool)
        Emitted when the void inclusion setting is toggled.
    geometry_connect_signal : Signal(object)
        Emitted when a geometry needs signal connections.

    Attributes
    ----------
    annotation_export : ExportGEOJSON
        Dialog for exporting annotation data.
    annoation_import : ImportGEOJSON
        Dialog for importing annotation data.
    right_click_add_geometry : QAction
        Action for adding geometry via right-click menu.
    """

    # signals
    add_geometry_signal = Signal(list, name="add_geometry_signal")
    voids_toggle_signal = Signal(bool, name="voids_toggle_signal")
    geometry_connect_signal = Signal(object, name="geometry_connect_signal")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the view with UI setup and signal connections.

        Parameters
        ----------
        parent : Optional[QWidget]
            Parent widget, defaults to None.
        """
        QDockWidget.__init__(self, parent)
        self.setupUi(self)

        self.annotation_export: ExportGEOJSON = ExportGEOJSON()
        self.annoation_import: ImportGEOJSON = ImportGEOJSON()

        self.import_button.clicked.connect(self.annoation_import.import_clicked)
        self.export_button.clicked.connect(self.annotation_export.export_clicked)

        self.right_click_add_geometry: QAction = QAction("Add Geometry", self)
        self.voids_toggle.stateChanged.connect(self.voids_toggle_handler)

    def voids_toggle_handler(self) -> None:
        """
        Handle toggling of the void inclusion setting.

        Emits a signal with the current state of the toggle button.
        """
        self.voids_toggle_signal.emit(self.voids_toggle.isChecked())


class ExportGEOJSON(QFileDialog):
    """
    Dialog for exporting annotation data to GeoJSON format.

    Provides a file dialog for saving annotation data and emits a signal
    with the selected file path.

    Signals
    -------
    export_signal : Signal(str)
        Emitted when an export location is selected, containing the file path.
    """

    export_signal = Signal(str, name="export_signal")

    def __init__(self) -> None:
        """Initialize the export dialog."""
        super().__init__()

    def export_clicked(self) -> None:
        """
        Handle the export button click.

        Opens a save file dialog and emits a signal with the selected file path
        if a valid path is chosen.
        """
        annotation_export_file_name: Tuple[str, str] = self.getSaveFileName(
            parent=None,
            caption="Select the export location.",
            filter="annotation collections (*.nitf.geojson.json)",
        )

        if annotation_export_file_name[0]:
            self.export_signal.emit(str(annotation_export_file_name[0]))


class ImportGEOJSON(QFileDialog):
    """
    Dialog for importing annotation data from GeoJSON or MATLAB format.

    Provides a file dialog for opening annotation data files and emits a signal
    with the selected file path.

    Signals
    -------
    import_signal : Signal(str)
        Emitted when an import file is selected, containing the file path.
    """

    import_signal = Signal(str, name="import_signal")

    def __init__(self) -> None:
        """Initialize the import dialog."""
        super().__init__()

    def import_clicked(self) -> None:
        """
        Handle the import button click.

        Opens a file dialog for selecting geojson, json, or mat files and
        emits a signal with the selected file path if a valid file is chosen.
        """
        annotation_import_file_name: List[str] = self.getOpenFileNames(
            parent=None,
            caption="Select geojson to import.",
            filter="geojson (*.geojson *.json *.mat)",
        )[0]

        if annotation_import_file_name:
            self.import_signal.emit(str(annotation_import_file_name[0]))


class GeometryTableWidget(QTableWidget, ExtensibleObject):
    """
    Table widget for displaying geometry information.

    Displays geometry names and allows for selection and editing of geometries.
    Can be extended by other applications to include additional columns.

    Signals
    -------
    name_changed_signal : Signal(object, str)
        Emitted when a geometry name is changed.
    cell_changed_signal : Signal(object)
        Emitted when a cell in the table is changed.
    populate_table_signal : Signal(list, bool)
        Emitted when the table is populated with geometries.

    Attributes
    ----------
    _headers : List[str]
        List of column headers for the table.
    _geometries : List[GeometryROI]
        List of geometry objects displayed in the table.
    """

    name_changed_signal = Signal(object, str, name="name_changed_signal")
    cell_changed_signal = Signal(object, name="cell_changed_signal")
    populate_table_signal = Signal(list, bool, name="populate_table_signal")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the geometry table widget.

        Parameters
        ----------
        *args : Any
            Positional arguments passed to QTableWidget.
        **kwargs : Any
            Keyword arguments passed to QTableWidget.
        """
        super().__init__(*args, **kwargs)

        self.setColumnCount(1)

        self._headers: List[str] = [
            "Geometry"
        ]  # default only has Geometry (name), other applications can extend this

        self.setHorizontalHeaderLabels(self.get_headers())

        self._geometries: List[GeometryType] = []
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cellChanged.connect(self.name_changed)
        self.currentItemChanged.connect(self.table_geometry_select)

    def add_header(self, header: str) -> None:
        """
        Add a header to the list of headers.

        Parameters
        ----------
        header : str
            Name of the header to add.
        """
        self._headers.append(header)

    def update_header(self, updated_header: str, header_index: int) -> None:
        """
        Replace the header text for a header that already exists.

        Parameters
        ----------
        updated_header : str
            Updated header text.
        header_index : int
            The index position of the header to replace.
        """
        self._headers[header_index] = updated_header
        self.setHorizontalHeaderLabels(self.get_headers())

    def get_headers(self) -> List[str]:
        """
        Get the list of headers.

        Returns
        -------
        List[str]
            The list containing all text for all the headers.
        """
        return self._headers

    def set_headers(self, headers: List[str]) -> None:
        """
        Set all the headers.

        Parameters
        ----------
        headers : List[str]
            A list of strings with all the column headers.
        """
        self._headers = headers

    def name_changed(self, row: int, col: int) -> None:
        """
        Handle when a geometry name is changed in the table.

        Emits a signal with the geometry and new name when the name column is edited.

        Parameters
        ----------
        row : int
            The row index of the changed cell.
        col : int
            The column index of the changed cell.
        """
        if col == 0 and row < len(self._geometries):
            item: Optional[QTableWidgetItem] = self.item(row, col)
            if item is not None:
                self.name_changed_signal.emit(self._geometries[row], item.text())

    def table_geometry_select(self) -> None:
        """
        Handle selection of a geometry in the table.

        Emits a signal with the selected geometry if geometries exist and
        a valid row is selected.
        """
        if self.get_geometries() and self.currentRow() >= 0:
            current_row: int = self.currentRow()
            if current_row < len(self._geometries):
                self.cell_changed_signal.emit(self.get_geometries()[current_row])

    def image_geometry_select(self, geometry: GeometryType) -> None:
        """
        Select a geometry in the table based on an image selection.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry selected in the image.
        """
        geometries: List[GeometryType] = self.get_geometries()
        if geometry in geometries:
            selected_index: int = geometries.index(geometry)
            self.setCurrentCell(selected_index, 0)

    def add_geometry(self, geometry: GeometryType) -> None:
        """
        Add a geometry to the table.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to add.
        """
        self.insertRow(self.rowCount())
        self._geometries.append(geometry)

    def remove_geometry(self, geometry: GeometryType) -> None:
        """
        Remove a geometry from the table.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to remove.
        """
        geometries: List[GeometryType] = self.get_geometries()
        if geometry in geometries:
            geometry_index: int = geometries.index(geometry)
            self.removeRow(geometry_index)
            del geometries[geometry_index]

    def set_geometries(self, geometries: List[GeometryType]) -> None:
        """
        Set the list of geometries.

        Parameters
        ----------
        geometries : List[GeometryROI]
            List of geometry objects.
        """
        self._geometries = geometries

    def get_geometries(self) -> List[GeometryType]:
        """
        Get the list of geometries.

        Returns
        -------
        List[GeometryROI]
            List of geometry objects.
        """
        return self._geometries

    def populate_geometry_names(
        self, geometries: List[GeometryType], include_voids: bool
    ) -> None:
        """
        Populate the table with geometries.

        Clears the existing table content and populates it with the provided
        geometries, displaying their names in the first column.

        Parameters
        ----------
        geometries : List[GeometryROI]
            List of geometry objects to display.
        include_voids : bool
            Whether voids are included in the current configuration.
        """
        self.clear()
        self.setRowCount(0)
        self.set_geometries(geometries)

        for i, geometry in enumerate(geometries):
            self.insertRow(self.rowCount())
            name_item: QTableWidgetItem = QTableWidgetItem(geometry.get_name())
            self.setItem(i, 0, name_item)

        self.populate_table_signal.emit(geometries, include_voids)
        self.setHorizontalHeaderLabels(self.get_headers())


class GeometryViewWidget(pg.ImageView):
    """
    Widget for displaying geometry previews.

    Provides a view of geometries with customizable background color and
    image overlay capabilities.

    Signals
    -------
    update_background_color_signal : Signal()
        Emitted when the background color is changed.

    Attributes
    ----------
    _background_color : Tuple[int, int, int]
        RGB background color tuple.
    """

    update_background_color_signal = Signal(name="update_background_color_signal")

    def __init__(self) -> None:
        """Initialize the geometry view widget with default settings."""
        super().__init__()

        self.ui.histogram.hide()
        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()
        self._background_color: Tuple[int, int, int] = (0, 0, 0)  # default black
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos: Any) -> None:
        """
        Show a context menu for the view.

        Creates and displays a context menu with background color selection
        and default view actions.

        Parameters
        ----------
        pos : QPoint
            Position where the context menu was requested.
        """
        context_menu: QMenu = QMenu(self)

        background_color_select_action: QAction = context_menu.addAction(
            "Background Color"
        )
        background_color_select_action.triggered.connect(self.background_color_select)

        context_menu.addSeparator()
        default_actions: List[QAction] = self.view.menu.actions()
        context_menu.addActions(default_actions)
        context_menu.exec_(self.mapToGlobal(pos))

    def update_background_color(self) -> None:
        """Emit signal indicating background color has changed."""
        self.update_background_color_signal.emit()

    def background_color_select(self) -> None:
        """
        Open a color dialog to select background color.

        Opens a QColorDialog and sets the selected color as the background color,
        then emits an update signal.
        """
        color: QColor = QColorDialog.getColor()
        if color.isValid():
            color_tuple: Tuple[int, int, int, int] = color.getRgb()
            self.set_background_color(color_tuple)
            self.update_background_color()

    def set_background_color(self, background_color: Tuple[int, int, int, int]) -> None:
        """
        Set the background color.

        Parameters
        ----------
        background_color : Tuple[int, int, int, int]
            RGBA color tuple.
        """
        self._background_color = background_color[:3]  # Only store RGB

    def get_background_color(self) -> Tuple[int, int, int, int]:
        """
        Get the current background color.

        Returns
        -------
        Tuple[int, int, int, int]
            RGBA color tuple (alpha is always 255).
        """
        return (*self._background_color, 255)

    def update_geometry_view(
        self, aspect_ratio: float, preview_image: NDArray[np.uint8]
    ) -> None:
        """
        Update the geometry view with a new preview image.

        Sets the aspect ratio and displays the provided image with the
        current background color.

        Parameters
        ----------
        aspect_ratio : float
            Aspect ratio to maintain for the display.
        preview_image : NDArray[np.uint8]
            Image data to display as numpy array.
        """
        background_color: List[int] = list(self.get_background_color())[:3]

        self.view.setAspectLocked(lock=True, ratio=aspect_ratio)
        self.setImage(preview_image)
        self.getView().setBackgroundColor(
            QColor(background_color[0], background_color[1], background_color[2])
        )
