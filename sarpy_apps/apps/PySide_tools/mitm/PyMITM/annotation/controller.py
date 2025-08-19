from typing import List, Tuple, Any, Optional, Dict, Union, Callable
import numpy
from PySide6.QtWidgets import QMessageBox

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.view import View
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.model import Model
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.canvas import \
    GeometryROI
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.controller import \
    Controller as PlotterController


class Controller:
    """
    Main controller class for the annotation system.

    Manages interactions between the model and view components, handling
    geometry manipulation, import/export operations, and UI updates.

    Attributes
    ----------
    model : Model
        The data model for annotation operations.
    viewer : View
        The user interface view component.
    mitm_controller : Any
        Reference to the main MITM controller.
    """

    def __init__(self, mitm_controller: Any) -> None:
        """
        Initialize the controller with the given MITM controller.

        Parameters
        ----------
        mitm_controller : Any
            The main MITM controller instance.
        """
        super().__init__()
        self.model: Model = Model()
        self.viewer: View = View()
        self.mitm_controller: Any = mitm_controller

        # Connect signals for geometry manipulation
        self.viewer.add_geometry_signal.connect(self.geometry_add_controller)
        self.viewer.geometry_table.name_changed_signal.connect(
            self.geometry_name_changed_controller
        )
        self.viewer.geometry_table.cell_changed_signal.connect(
            self.geometry_clicked_controller
        )

        # Connect import/export signals
        self.viewer.annoation_import.import_signal.connect(self.import_controller)
        self.viewer.annotation_export.export_signal.connect(self.export_controller)
        self.viewer.geometry_view.update_background_color_signal.connect(
            self.background_color_controller
        )

        # Connect void toggle signals
        self.viewer.voids_toggle_signal.connect(self.model.set_include_voids)
        self.viewer.voids_toggle_signal.connect(self.update_geometry_table)

        # Connect geometry add buttons
        self.viewer.add_geometry_button.clicked.connect(self.main_geometry_add_handler)
        self.viewer.right_click_add_geometry.triggered.connect(
            self.right_click_geometry_add_handler
        )

    @property
    def right_click_add_geometry(self) -> Any:
        """
        Get the right-click add geometry action.

        Returns
        -------
        Any
            The right-click add geometry action from the viewer.
        """
        return self.viewer.right_click_add_geometry

    def plot_widget_interaction_controller(self, plot: PlotterController) -> None:
        """
        Handle plot widget interaction events.

        Detects resize events and coordinates with the model to recreate
        geometries with updated positions to maintain proper scaling and placement.

        Parameters
        ----------
        plot : Any
            The plot widget dock that was interacted with.
        """
        # Check for resize events
        processed_geometries: Union[bool, List[Dict[str, Any]]] = False
        if plot.resize_event == 1:
            # Reset the flag
            plot.clear_resize_event_flag()

            # Get all geometries (copy to avoid issues during updates)
            geometries: List[GeometryROI] = plot.get_geometries().copy()

            # Delegate to model
            processed_geometries = self.model.recreate_geometries_after_resize(
                geometries, plot.decimation_factor
            )

            # Remove the old geometries
            for geometry in geometries:
                plot.remove_geometry(geometry)

        if processed_geometries:
            # Create new geometries from the processed information
            for geom_info in processed_geometries:
                # Create a completely new geometry
                new_geometry = GeometryROI(
                    positions=geom_info["decimated_coords"],
                    closed=True,
                    removable=True,
                    movable=True,
                    snapSize=1,
                    rotateSnap=False,
                    translateSnap=False,
                    scaleSnap=False,
                    rotatable=False,
                )

                # Restore properties
                new_geometry.set_color(geom_info["original_color"])
                new_geometry.set_name(geom_info["original_name"])
                new_geometry.set_annotation_feature_w_voids(
                    geom_info["original_annotation_w_voids"]
                )
                new_geometry.set_annotation_feature_wo_voids(
                    geom_info["original_annotation_wo_voids"]
                )

                # Add to plot and connect signals
                self.connect_geometry(new_geometry)
                plot.add_geometry(new_geometry)

        # Handle selection and UI updates
        if plot.get_current_geometry():
            plot.render_geometry_selection()
            self.update_geometry_preview_controller()
            self.update_geometry_table()

    def main_geometry_add_handler(self) -> None:
        """
        Handle adding geometry from the main add button.

        Gets the center position of the current view and initiates
        geometry creation at that position.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        center_coords: Tuple[float, float] = (
            selected_widget.get_plot_center_coordinates()
        )
        self.viewer.add_geometry_signal.emit([center_coords[0], center_coords[1]])

    def right_click_geometry_add_handler(self) -> None:
        """
        Handle adding geometry from right-click menu.

        Gets the current cursor position and initiates
        geometry creation at that position.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        cursor_position: List[float] = (
            selected_widget.get_current_cursor_image_position()
        )
        self.viewer.add_geometry_signal.emit(cursor_position)

    def geometry_name_changed_controller(
        self, geometry: GeometryROI, geometry_name: str
    ) -> None:
        """
        Handle geometry name changes.

        Updates the name property of the specified geometry and emits
        the appropriate signal.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry whose name changed.
        geometry_name : str
            The new name to assign to the geometry.
        """
        geometry.set_name(geometry_name)
        geometry.geometry_name_signal.emit(geometry)

    def update_geometry_table(self) -> None:
        """
        Update the geometry table with current geometries.

        Retrieves geometries from the current canvas and updates
        the table display with their properties.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        geometries: List[GeometryROI] = selected_widget.get_geometries()
        self.viewer.geometry_table.populate_geometry_names(
            geometries, self.model.get_include_voids()
        )

    def background_color_controller(self) -> None:
        """
        Handle background color changes.

        Updates the geometry preview display when the background color changes.
        """
        self.update_geometry_preview_controller()

    def export_controller(self, filename: str) -> None:
        """
        Handle exporting annotation data.

        Creates an annotation collection and saves it to the specified file.

        Parameters
        ----------
        filename : str
            Path to save the exported file.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        geometries: List[GeometryROI] = selected_widget.get_geometries()
        file_annotation_collection: Any = self.model.create_file_annotation_collection(
            geometries, filename
        )

        self.model.export_geometry(
            selected_widget.project_image_to_ground_geo,
            filename,
            file_annotation_collection,
        )

    def import_controller(self, filename: str) -> None:
        """
        Handle importing annotation data.

        Reads geometry data from a file and creates corresponding
        visualizations in the current view.

        Parameters
        ----------
        filename : str
            Path to the file to import.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        if not selected_widget.image_loaded:
            QMessageBox.information(
                None, "Warning", "Cannot import geometries onto empty plot"
            )
            return

        geometries_list, geometry_colors, geometry_names = self.model.parse_import(
            selected_widget.project_ground_to_image_geo,
            selected_widget.decimation_factor,
            filename,
        )

        for geometries, geometry_color, geometry_name in zip(
            geometries_list, geometry_colors, geometry_names
        ):
            for image_geometry_coords in geometries:
                geometry = GeometryROI(
                    positions=image_geometry_coords,
                    closed=True,
                    removable=True,
                    movable=True,
                    snapSize=1,
                    rotateSnap=False,
                    translateSnap=False,
                    scaleSnap=False,
                    rotatable=False,
                )
                geometry.set_color(geometry_color)
                geometry.set_name(geometry_name)

                self.connect_geometry(geometry)
                selected_widget.add_geometry(geometry)
                self.annotation_feature_controller()

            selected_widget.render_geometry_selection()
            self.update_geometry_preview_controller()
            self.update_geometry_table()
            self.viewer.geometry_table.image_geometry_select(geometry)

    def connect_geometry(self, geometry: GeometryROI) -> None:
        """
        Connect signals for a geometry.

        Establishes all necessary signal connections between the geometry
        and various controller methods and UI components.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry to connect signals for.
        """
        self.viewer.geometry_connect_signal.emit(geometry)

        # Connect UI interaction signals
        geometry.geometry_clicked_signal.connect(
            self.viewer.geometry_table.image_geometry_select
        )
        geometry.geometry_changed_signal.connect(
            self.viewer.geometry_table.image_geometry_select
        )

        # Connect controller signals
        geometry.geometry_clicked_signal.connect(self.geometry_clicked_controller)
        geometry.geometry_changed_signal.connect(self.geometry_changed_controller)
        geometry.geometry_clicked_signal.connect(self.annotation_feature_controller)
        geometry.geometry_changed_signal.connect(self.annotation_feature_controller)
        geometry.geometry_color_signal.connect(self.annotation_feature_controller)
        geometry.geometry_name_signal.connect(self.annotation_feature_controller)
        geometry.geometry_removed_signal.connect(self.geometry_removed_controller)
        geometry.geometry_removed_signal.connect(self.annotation_feature_controller)
        geometry.geometry_color_signal.connect(self.geometry_color_controller)
        geometry.geometry_duplicate_signal.connect(self.geometry_duplicate_controller)

    def geometry_clicked_controller(self, geometry: GeometryROI) -> None:
        """
        Handle geometry click events.

        Updates the current selection and checks for interior geometries.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry that was clicked.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()

        # Check for interior geometries and update ordering if needed
        if self.model.check_for_interior_geometries(
            selected_widget.get_undecimated_pixel_coordinates,
            geometry,
            selected_widget.get_geometries(),
        ):
            selected_widget.update_geometry_ordering()

        # Update selection and UI
        selected_widget.update_current_geometry(geometry)
        self.update_geometry_preview_controller()
        self.annotation_feature_controller()

    def geometry_changed_controller(self, geometry: GeometryROI) -> None:
        """
        Handle geometry change events.

        Updates the UI and recalculates annotation features when a geometry is modified.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry that was changed.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        selected_widget.update_current_geometry(geometry)
        self.update_geometry_preview_controller()
        self.annotation_feature_controller()
        self.update_geometry_table()

    def geometry_removed_controller(self, geometry: GeometryROI) -> None:
        """
        Handle geometry removal events.

        Updates related geometries and UI components when a geometry is removed.

        Parameters
        ----------
        geometry : GeometryROI
            The geometry that was removed.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        geometries: List[GeometryROI] = selected_widget.get_geometries()

        # Check for associated exterior geometry before removal
        exterior_geometry, interior_geometries = self.model.get_related_geometries(
            selected_widget.get_undecimated_pixel_coordinates, geometry, geometries
        )

        selected_widget.update_current_geometry(exterior_geometry)
        selected_widget.remove_geometry(geometry)
        self.update_geometry_preview_controller()
        self.update_geometry_table()

    def geometry_add_controller(self, spawn_image_coords: List[float]) -> None:
        """
        Handle geometry addition events.

        Creates a new geometry at the specified coordinates with default triangle shape.

        Parameters
        ----------
        spawn_image_coords : List[float]
            [x, y] coordinates where the geometry should be added.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        size_ratio: float = self.model.get_size_ratio(selected_widget.get_view_range())

        if not selected_widget.image_loaded:
            QMessageBox.information(
                None, "Warning", "Cannot add geometry to empty plot."
            )
            return

        # Create geometry with triangle shape initially
        triangle_positions: List[List[float]] = [
            [0 * size_ratio, -1 * size_ratio],
            [1 * size_ratio, 1 * size_ratio],
            [-1 * size_ratio, 1 * size_ratio],
        ]

        geometry = GeometryROI(
            triangle_positions,
            pos=spawn_image_coords,
            closed=True,
            removable=True,
            movable=True,
            snapSize=1,
            rotateSnap=False,
            translateSnap=False,
            scaleSnap=False,
            rotatable=False,
        )

        # Add to plot and connect signals
        self.connect_geometry(geometry)
        selected_widget.add_geometry(geometry)
        selected_widget.render_geometry_selection()

        # Update UI and calculate annotation features
        self.annotation_feature_controller()
        self.update_geometry_table()
        self.update_geometry_preview_controller()
        self.viewer.geometry_table.image_geometry_select(geometry)
        self.geometry_changed_controller(geometry)
        geometry.geometry_changed_signal.emit(geometry)

    def update_geometry_preview_controller(self) -> None:
        """
        Update the geometry preview display.

        Creates a preview image based on the current geometry and background color,
        with optional void inclusion based on the current toggle state.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        background_color: Tuple[int, int, int, int] = (
            self.viewer.geometry_view.get_background_color()
        )
        geometries: List[GeometryROI] = selected_widget.get_geometries()
        exterior_geometry: Optional[GeometryROI] = (
            selected_widget.get_current_geometry()
        )

        if exterior_geometry:
            if self.model.get_include_voids():
                # Get interior geometries for the current geometry
                interior_geometries: List[GeometryROI] = (
                    self.model.get_interior_geometries(
                        selected_widget.get_undecimated_pixel_coordinates,
                        exterior_geometry,
                        geometries,
                    )
                )

                # Create a combined geometry with interior voids if present
                geometry: Optional[Any] = self.model.create_geometry(
                    selected_widget.get_undecimated_pixel_coordinates,
                    exterior_geometry,
                    interior_geometries,
                )
            else:
                # Won't include interior geometries in the preview image
                geometry = self.model.create_geometry(
                    selected_widget.get_undecimated_pixel_coordinates,
                    exterior_geometry,
                    [],
                )

            # Create and display preview image
            preview_image: numpy.ndarray = self.model.create_preview_image(
                selected_widget.reader,
                selected_widget.remap_function,
                background_color,
                geometry,
            )
        else:
            # No geometry selected, clear the preview
            preview_image = numpy.zeros((1, 1))

        self.viewer.geometry_view.update_geometry_view(
            selected_widget.get_aspect_ratio(), preview_image
        )

    def geometry_color_controller(self) -> None:
        """
        Handle geometry color change events.

        Updates the visual appearance of geometries when their colors change.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        selected_widget.render_geometry_selection()

    def geometry_duplicate_controller(self, duplicated_geometry: GeometryROI) -> None:
        """
        Handle geometry duplication events.

        Sets up a duplicated geometry and updates the UI.

        Parameters
        ----------
        duplicated_geometry : GeometryROI
            The duplicated geometry to set up.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        self.connect_geometry(duplicated_geometry)
        selected_widget.add_geometry(duplicated_geometry)
        selected_widget.render_geometry_selection()

        # Update UI and calculate annotation features
        self.annotation_feature_controller()
        self.update_geometry_table()
        self.viewer.geometry_table.image_geometry_select(duplicated_geometry)
        self.update_geometry_preview_controller()

    def annotation_feature_controller(self) -> None:
        """
        Update annotation features for all geometries.

        Processes all geometries to create annotation features both with and without
        voids, ensuring the current geometry is processed last for proper display priority.
        """
        selected_widget: Any = self.mitm_controller.get_current_widget()
        geometries: List[GeometryROI] = selected_widget.get_geometries()
        current_geometry: Optional[GeometryROI] = selected_widget.get_current_geometry()

        # Process all geometries except current_geometry first
        for geometry in geometries:
            if geometry == current_geometry:
                continue  # Skip current_geometry for now

            interior_geometries: List[GeometryROI] = self.model.get_interior_geometries(
                selected_widget.get_undecimated_pixel_coordinates,
                geometry,
                geometries,
            )

            exterior_geometry: GeometryROI = geometry

            # Create geometries with and without voids
            geometry_w_voids: Optional[Any] = self.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates,
                exterior_geometry,
                interior_geometries,
            )
            geometry_wo_voids: Optional[Any] = self.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, exterior_geometry, []
            )

            annotation_feature_w_voids: Any = self.model.create_feature(
                geometry_w_voids
            )
            annotation_feature_wo_voids: Any = self.model.create_feature(
                geometry_wo_voids
            )

            # Store results on the geometry
            exterior_geometry.set_annotation_feature_w_voids(annotation_feature_w_voids)
            exterior_geometry.set_annotation_feature_wo_voids(
                annotation_feature_wo_voids
            )

        # Now process current_geometry last to ensure its display is prioritized
        if current_geometry in geometries:
            geometry = current_geometry
            interior_geometries = self.model.get_interior_geometries(
                selected_widget.get_undecimated_pixel_coordinates,
                geometry,
                geometries,
            )
            exterior_geometry = geometry

            # Create geometries with and without voids
            geometry_w_voids = self.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates,
                exterior_geometry,
                interior_geometries,
            )
            geometry_wo_voids = self.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, exterior_geometry, []
            )

            # Calculate annotation features for both versions
            annotation_feature_w_voids = self.model.create_feature(geometry_w_voids)
            annotation_feature_wo_voids = self.model.create_feature(geometry_wo_voids)

            # Store results on the geometry
            exterior_geometry.set_annotation_feature_w_voids(annotation_feature_w_voids)
            exterior_geometry.set_annotation_feature_wo_voids(
                annotation_feature_wo_voids
            )
