from typing import List, Optional, Any, Dict, Tuple
import pyqtgraph as pg
from PySide6.QtWidgets import QMenu, QColorDialog
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QCoreApplication, Signal, QObject

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.application_extension import ExtensibleObject


class GeometryROI(pg.PolyLineROI, ExtensibleObject):
    """
    Region of Interest class for polygonal geometries.

    Extends pyqtgraph's PolyLineROI with additional functionality for
    annotation features, color management, naming, and signal handling.

    Signals
    -------
    geometry_clicked_signal : Signal(object)
        Emitted when geometry is clicked.
    geometry_changed_signal : Signal(object)
        Emitted when geometry is modified.
    geometry_removed_signal : Signal(object)
        Emitted when geometry is removed.
    geometry_duplicate_signal : Signal(object)
        Emitted when geometry is duplicated.
    geometry_color_signal : Signal(object)
        Emitted when geometry color is changed.
    geometry_name_signal : Signal(object)
        Emitted when geometry name is changed.

    Attributes
    ----------
    duplicatable : bool
        Whether the geometry can be duplicated.
    colorable : bool
        Whether the geometry color can be changed.
    view_box : Optional[pg.ViewBox]
        Associated view box for this ROI.
    _color : str
        Hex color string for the geometry.
    _name : str
        Name of the geometry.
    _annotation_feature_w_voids : Optional[Any]
        Annotation feature including voids.
    _annotation_feature_wo_voids : Optional[Any]
        Annotation feature excluding voids.
    """

    # Signals
    geometry_clicked_signal = Signal(object, name="geometry_clicked_signal")
    geometry_changed_signal = Signal(object, name="geometry_changed_signal")
    geometry_removed_signal = Signal(object, name="geometry_removed_signal")
    geometry_duplicate_signal = Signal(object, name="geometry_duplicate_signal")
    geometry_color_signal = Signal(object, name="geometry_color_signal")
    geometry_name_signal = Signal(object, name="geometry_name_signal")

    def __init__(
        self, positions: List[List[float]], closed: bool = False, **kwargs: Any
    ) -> None:
        """
        Initialize the geometry ROI.

        Parameters
        ----------
        positions : List[List[float]]
            List of [x, y] coordinates for ROI vertices.
        closed : bool, optional
            Whether the ROI is closed (polygon), defaults to False.
        **kwargs : Any
            Additional arguments passed to pg.PolyLineROI.
        """
        # Initialize both parent classes
        pg.PolyLineROI.__init__(self, positions, closed=closed, **kwargs)
        ExtensibleObject.__init__(self)

        # Original attributes
        self.duplicatable: bool = True
        self.colorable: bool = True
        self._color: str = "#FFFFFF"  # white is default
        self._name: str = "None"  # default name

        self._annotation_feature_w_voids: Optional[Any] = None
        self._annotation_feature_wo_voids: Optional[Any] = None

        # Connect signals
        self.sigClicked.connect(self.geometry_clicked)
        self.sigRegionChangeFinished.connect(self.geometry_changed)
        self.sigRemoveRequested.connect(self.geometry_removed)

        self.geometry_color_signal.connect(self._update_geometry_properties)
        self.geometry_name_signal.connect(self._update_geometry_properties)

        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.improve_handle_selectability()
        self.view_box: Optional[pg.ViewBox] = None

    def set_view_box(self, view_box: pg.ViewBox) -> None:
        """
        Set the view box for this ROI.

        Disconnects from previous view box if one exists, and connects to the new one.

        Parameters
        ----------
        view_box : pg.ViewBox
            The view box to connect to.
        """
        if self.view_box is not None:
            self.view_box.sigRangeChanged.disconnect(self.update_handle_positions)

        self.view_box = view_box
        if view_box is not None:
            view_box.sigRangeChanged.connect(self.update_handle_positions)

    def update_handle_positions(self) -> None:
        """Update handle positions when view range changes."""
        self.stateChanged()

    def improve_handle_selectability(self) -> None:
        """
        Make ROI handles easier to select by increasing size and visibility.

        Sets handle properties to make them more visible and easier to interact with.
        """
        handles: List[Any] = self.getHandles()
        for handle in handles:
            # Increase the size of the handle
            if hasattr(handle, "setSize"):
                handle.setSize(12)  # Larger size

            if hasattr(handle, "setPen"):
                handle.setPen(pg.mkPen("y", width=3))
            if hasattr(handle, "setBrush"):
                handle.setBrush(pg.mkBrush(255, 255, 0, 180))

            if hasattr(handle, "setClickRadius"):
                handle.setClickRadius(10)

            if hasattr(handle, "setZValue"):
                handle.setZValue(self.zValue() + 1000)

    def addHandle(self, *args: Any, **kwargs: Any) -> Any:
        """
        Add a handle to the ROI with improved selectability.

        Parameters
        ----------
        *args : Any
            Positional arguments passed to pg.PolyLineROI.addHandle.
        **kwargs : Any
            Keyword arguments passed to pg.PolyLineROI.addHandle.

        Returns
        -------
        Any
            The created handle.
        """
        handle = super().addHandle(*args, **kwargs)

        if hasattr(handle, "setSize"):
            handle.setSize(12)
        if hasattr(handle, "setPen"):
            handle.setPen(pg.mkPen("y", width=3))
        if hasattr(handle, "setBrush"):
            handle.setBrush(pg.mkBrush(255, 255, 0, 180))
        if hasattr(handle, "setClickRadius"):
            handle.setClickRadius(10)
        if hasattr(handle, "setZValue"):
            handle.setZValue(self.zValue() + 1000)

        return handle

    def setZValue(self, z: float) -> None:
        """
        Set Z-value for ROI and handles.

        Parameters
        ----------
        z : float
            Z-value to set.
        """
        super().setZValue(z)

        # Update handle z-values to stay above the ROI
        handles: List[Any] = self.getHandles()
        for handle in handles:
            if hasattr(handle, "setZValue"):
                handle.setZValue(z + 1000)

    def set_annotation_feature_wo_voids(self, feature_wo_voids: Any) -> None:
        """
        Set the annotation feature without voids.

        Parameters
        ----------
        feature_wo_voids : Any
            Annotation feature without voids.
        """
        self._annotation_feature_wo_voids = feature_wo_voids
        self._update_geometry_properties(feature_wo_voids)

    def get_annotation_feature_wo_voids(self) -> Any:
        """
        Get the annotation feature without voids.

        Returns
        -------
        Any
            Annotation feature without voids.
        """
        return self._annotation_feature_wo_voids

    def set_annotation_feature_w_voids(self, feature_w_voids: Any) -> None:
        """
        Set the annotation feature with voids.

        Parameters
        ----------
        feature_w_voids : Any
            Annotation feature with voids.
        """
        self._annotation_feature_w_voids = feature_w_voids
        self._update_geometry_properties(feature_w_voids)

    def get_annotation_feature_w_voids(self) -> Any:
        """
        Get the annotation feature with voids.

        Returns
        -------
        Any
            Annotation feature with voids.
        """
        return self._annotation_feature_w_voids

    def get_name(self) -> str:
        """
        Get the geometry name.

        Returns
        -------
        str
            The geometry name.
        """
        return self._name

    def set_name(self, name: str) -> None:
        """
        Set the geometry name.

        Parameters
        ----------
        name : str
            The new name.
        """
        self._name = name

    def get_color(self) -> str:
        """
        Get the geometry color.

        Returns
        -------
        str
            Hex color string.
        """
        return self._color

    def set_color(self, color: str) -> None:
        """
        Set the geometry color.

        Parameters
        ----------
        color : str
            Hex color string.
        """
        self._color = color

    def _update_geometry_properties(self, feature: Any) -> None:
        """
        Update geometry properties in the annotation feature.

        Parameters
        ----------
        feature : Any
            Feature to update with current geometry properties.
        """
        if feature and hasattr(feature, "properties"):
            geometry_properties: Dict[str, str] = {
                "type": "GeometryProperties",
                "color": str(self.get_color()),
                "name": str(self.get_name()),
            }
            feature.properties.add_geometry_property(geometry_properties)

    def register_menu_action(self, action: QAction) -> None:
        """
        Register a menu action to be added to the context menu.

        Parameters
        ----------
        action : QAction
            Action to add to the context menu.
        """
        if not hasattr(self, "_additional_menu_actions"):
            self._additional_menu_actions: List[QAction] = []
        self._additional_menu_actions.append(action)

    def duplicate_geometry_clicked(self) -> None:
        """
        Handle duplicate geometry request.

        Creates a duplicate of this geometry with the same properties and
        emits a signal with the new geometry.
        """
        state: Dict[str, Any] = self.getState()
        positions: List[List[float]] = [point.copy() for point in state["points"]]
        loc: List[float] = state["pos"]

        duplicated_geometry = GeometryROI(
            positions=positions,
            pos=loc,
            closed=True,
            removable=True,
            movable=True,
            snapSize=1,
            rotateSnap=False,
            translateSnap=False,
            scaleSnap=False,
            rotatable=False,
        )

        # Copy properties
        duplicated_geometry.set_color(self.get_color())
        duplicated_geometry.set_name(self.get_name())

        # Copy all extensions to the new geometry
        for name, extension in self._extensions.items():
            if hasattr(extension, "duplicate"):
                new_extension = extension.duplicate()
                duplicated_geometry.register_extension(name, new_extension)

        self.geometry_duplicate_signal.emit(duplicated_geometry)

    def color_geometry_clicked(self) -> None:
        """
        Handle color geometry request.

        Opens a color dialog and updates the geometry color, then emits
        a signal when a color is selected.
        """
        color_dialog = GeometryColorSelect()
        selected_color: QColor = color_dialog.getColor()
        if selected_color.isValid():
            self.set_color(selected_color.name())
            self.geometry_color_signal.emit(self)

    def getMenu(self) -> QMenu:
        """
        Get the context menu for this geometry.

        Creates and returns a context menu with options for removing,
        duplicating, and changing the color of the geometry.

        Returns
        -------
        QMenu
            The context menu.
        """
        if self.menu is None:
            self.menu = QMenu()
            self.menu.setTitle(QCoreApplication.translate("Geometry", "Geometry"))

            if self.removable:
                remove_action: QAction = QAction(
                    QCoreApplication.translate("Geometry", "Remove Geometry"), self.menu
                )
                remove_action.triggered.connect(self.geometry_removed)
                self.menu.addAction(remove_action)
                self.menu.remove_action = remove_action

            if self.duplicatable:
                duplicate_action: QAction = QAction(
                    QCoreApplication.translate("Geometry", "Duplicate Geometry"),
                    self.menu,
                )
                duplicate_action.triggered.connect(self.duplicate_geometry_clicked)
                self.menu.addAction(duplicate_action)
                self.menu.duplicate_action = duplicate_action

            if self.colorable:
                color_action: QAction = QAction(
                    QCoreApplication.translate("Geometry", "Color Geometry"), self.menu
                )
                color_action.triggered.connect(self.color_geometry_clicked)
                self.menu.addAction(color_action)
                self.menu.color_action = color_action

            # Add extension actions if any
            if (
                hasattr(self, "_additional_menu_actions")
                and self._additional_menu_actions
            ):
                self.menu.addSeparator()
                for action in self._additional_menu_actions:
                    self.menu.addAction(action)

        return self.menu

    def geometry_clicked(self) -> None:
        """
        Handle geometry clicked event.

        Emits a signal and notifies all registered extensions.
        """
        self.geometry_clicked_signal.emit(self)

        # Notify all extensions
        for extension in self._extensions.values():
            if hasattr(extension, "on_geometry_clicked"):
                extension.on_geometry_clicked(self)

    def geometry_changed(self) -> None:
        """
        Handle geometry changed event.

        Emits a signal and notifies all registered extensions.
        """
        self.geometry_changed_signal.emit(self)

        # Notify all extensions
        for extension in self._extensions.values():
            if hasattr(extension, "on_geometry_changed"):
                extension.on_geometry_changed(self)

    def geometry_removed(self) -> None:
        """
        Handle geometry removed event.

        Notifies all registered extensions and emits a signal.
        """
        # Notify all extensions
        for extension in self._extensions.values():
            if hasattr(extension, "on_geometry_removed"):
                extension.on_geometry_removed(self)

        self.geometry_removed_signal.emit(self)


class Canvas(QObject):
    """
    Canvas for managing geometries.

    Provides methods for tracking and manipulating geometries on the plot canvas,
    including current selection management and geometry relationships.

    Signals
    -------
    current_geometry_changed_signal : Signal(object)
        Emitted when the current geometry changes.
    geometry_added_signal : Signal(object)
        Emitted when a geometry is added to the canvas.

    Attributes
    ----------
    _current_geometry : Optional[GeometryROI]
        The currently selected geometry.
    _previous_geometry : Optional[GeometryROI]
        The previously selected geometry.
    _current_related_geometries : Optional[List[GeometryROI]]
        List of geometries related to the current geometry.
    _previous_related_geometries : Optional[List[GeometryROI]]
        List of geometries related to the previous geometry.
    _geometries : List[GeometryROI]
        List of all geometries on the canvas.
    _plotWidget : Optional[pg.PlotWidget]
        The plot widget containing the canvas.
    """

    current_geometry_changed_signal = Signal(
        object, name="current_geometry_changed_signal"
    )
    geometry_added_signal = Signal(object, name="geometry_added_signal")

    def __init__(self) -> None:
        """Initialize the canvas with empty geometry collections."""
        super().__init__()
        self._current_geometry: Optional[GeometryROI] = None
        self._previous_geometry: Optional[GeometryROI] = None
        self._current_related_geometries: Optional[List[GeometryROI]] = None
        self._previous_related_geometries: Optional[List[GeometryROI]] = None
        self._geometries: List[GeometryROI] = []
        self._plotWidget: Optional[pg.PlotWidget] = None

    def set_current_geometry(self, geometry: Optional[GeometryROI]) -> None:
        """
        Set the current geometry.

        Updates the previous geometry before setting the new current geometry
        and emits a signal with the new current geometry.

        Parameters
        ----------
        geometry : Optional[GeometryROI]
            The geometry to set as current, or None to clear selection.
        """
        if self.get_current_geometry() is not None:
            self._set_previous_geometry(self.get_current_geometry())
        self._current_geometry = geometry
        self.current_geometry_changed_signal.emit(geometry)

    def _set_previous_geometry(self, geometry: GeometryROI) -> None:
        """
        Set the previous geometry.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to set as previous.
        """
        self._previous_geometry = geometry

    def get_previous_geometry(self) -> Optional[GeometryROI]:
        """
        Get the previous geometry.

        Returns
        -------
        Optional[GeometryROI]
            The previous geometry, or None if no previous geometry exists.
        """
        return self._previous_geometry

    def get_current_geometry(self) -> Optional[GeometryROI]:
        """
        Get the current geometry.

        Returns
        -------
        Optional[GeometryROI]
            The current geometry, or None if no geometry is selected.
        """
        return self._current_geometry

    def set_current_related_geometries(
        self, related_geometries: Optional[List[GeometryROI]]
    ) -> None:
        """
        Set the current related geometries.

        Updates the previous related geometries before setting the new ones.

        Parameters
        ----------
        related_geometries : Optional[List[GeometryROI]]
            List of related geometries, or None to clear.
        """
        if self.get_current_related_geometries() is not None:
            self._set_previous_related_geometries(self.get_current_related_geometries())
        self._current_related_geometries = related_geometries

    def get_current_related_geometries(self) -> Optional[List[GeometryROI]]:
        """
        Get the current related geometries.

        Returns
        -------
        Optional[List[GeometryROI]]
            List of related geometries, or None if no related geometries exist.
        """
        return self._current_related_geometries

    def _set_previous_related_geometries(
        self, related_geometries: List[GeometryROI]
    ) -> None:
        """
        Set the previous related geometries.

        Parameters
        ----------
        related_geometries : List[GeometryROI]
            List of related geometries.
        """
        self._previous_related_geometries = related_geometries

    def get_previous_related_geometries(self) -> Optional[List[GeometryROI]]:
        """
        Get the previous related geometries.

        Returns
        -------
        Optional[List[GeometryROI]]
            List of previous related geometries, or None if none exist.
        """
        return self._previous_related_geometries

    def get_geometries(self) -> List[GeometryROI]:
        """
        Get all geometries on the canvas.

        Returns
        -------
        List[GeometryROI]
            List of all geometries.
        """
        return self._geometries.copy()

    def set_geometries(self, geometries: List[GeometryROI]) -> None:
        """
        Set the list of geometries.

        Parameters
        ----------
        geometries : List[GeometryROI]
            List of geometries to set.
        """
        self._geometries = geometries

    def add_geometry(self, geometry: GeometryROI) -> None:
        """
        Add a geometry to the canvas.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to add.
        """
        self._geometries.append(geometry)
        self.geometry_added_signal.emit(geometry)

    def remove_geometry(self, geometry: GeometryROI) -> None:
        """
        Remove a geometry from the canvas.

        Also clears the current geometry selection if the removed geometry
        was currently selected.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to remove.
        """
        if geometry in self._geometries:
            geometry_index: int = self._geometries.index(geometry)
            del self._geometries[geometry_index]
        self.set_current_geometry(None)

    def update_geometry_ordering(self) -> None:
        """
        Update the Z-ordering of geometries.

        Sets the current geometry to the lowest Z-value and orders other
        geometries above it to ensure proper layering.
        """
        # Get the current selected geometry (exterior ROI)
        current_geometry: Optional[GeometryROI] = self.get_current_geometry()

        if current_geometry is None:
            return

        # Get all geometries on screen
        all_geometries: List[GeometryROI] = self.get_geometries()

        # Filter out the current geometry
        other_geometries: List[GeometryROI] = [
            geometry for geometry in all_geometries if geometry != current_geometry
        ]

        # First, increment all other geometries' z-values to avoid conflicts
        for geometry in other_geometries:
            geometry.setZValue(geometry.zValue() + len(all_geometries))

        # Set the current (exterior) geometry to lowest z-value
        current_geometry.setZValue(0)

        # Now set incrementing z-values for other geometries
        for i, geometry in enumerate(other_geometries):
            geometry.setZValue(i + 1)

    def render_geometry_selection(self) -> None:
        """
        Update the visual appearance of geometries based on selection state.

        The selected geometry gets a solid line, while others get dashed lines.
        Requires a current geometry to be selected.
        """
        geometries: List[GeometryROI] = self.get_geometries()
        selected_geometry: Optional[GeometryROI] = self.get_current_geometry()

        if selected_geometry is None:
            return

        for geometry in geometries:
            geometry.setPen(
                pg.mkPen(color=geometry.get_color(), width=1, style=Qt.DashLine)
            )
        selected_geometry.setPen(
            pg.mkPen(color=selected_geometry.get_color(), width=2, style=Qt.SolidLine)
        )


class GeometryColorSelect(QColorDialog):
    """
    Dialog for selecting colors for geometries.

    Inherits from QColorDialog to provide color selection functionality
    specifically for geometry objects.
    """

    def __init__(self) -> None:
        """Initialize the color selection dialog."""
        super().__init__()
