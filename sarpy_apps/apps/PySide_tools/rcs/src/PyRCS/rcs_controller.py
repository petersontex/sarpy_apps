from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.subapplication import \
    AbstractApp
from sarpy_apps.apps.PySide_tools.rcs.src.PyRCS.rcs_model import Model
from sarpy_apps.apps.PySide_tools.rcs.src.PyRCS.rcs_viewer import \
    RCSGeometryROI, RCSGeometryTableWidget, Viewer


class Controller(AbstractApp):
    """
    Controller for the Radar Cross Section (RCS) analysis tool.
    
    This class implements the controller component in the MVC (Model-View-Controller) 
    architecture for the RCS tool. It orchestrates the interaction between the RCS Model 
    (which handles data processing and RCS calculations) and the Viewer (which provides 
    the user interface).
    
    The controller coordinates:
    - Geometry creation, manipulation, and visualization
    - RCS calculations for selected geometries with different measurement units
    - Signal processing for radar data visualization (slow/fast time profiles)
    - Import/export functionality for RCS data
    - User interface interactions such as unit selection and display options
    - Integration with the PyMITM framework for SAR data access
    
    The Controller integrates with the PyMITM application framework through the AbstractApp
    inheritance, which provides access to the underlying SAR (Synthetic Aperture Radar) data
    and visualization tools.
    
    Attributes
    ----------
    model : Model
        RCS analysis model that performs data processing and calculations.
    viewer : Viewer
        RCS user interface component providing controls and displays.
    mitm_controller : Optional[Any]
        Reference to the PyMITM controller for accessing SAR data and widgets.
    
    Notes
    -----
    This class uses an event-driven architecture with Qt signal-slot connections
    between UI components and controller methods, enabling reactive updates to
    user interactions and data changes.
    """

    def __init__(self, app_id: str) -> None:
        """
        Initialize the RCS Controller.
        
        Sets up the model and viewer components and connects UI signals to
        controller methods for handling user interactions.
        
        Parameters
        ----------
        app_id : str
            Unique identifier for this controller instance used for registration 
            within the PyMITM framework.
        """
        super().__init__()
        self.model = Model()
        self.viewer = Viewer()
        self.viewer.rcs_table_view.update_headers()
        self.mitm_controller: Optional[Any] = None

        # Connect measurement unit selection signals
        self.viewer.rcs_measure_units_combo_box.currentIndexChanged.connect(
            self.measure_units_combo_box_controller
        )
        self.viewer.rcs_measure_units_combo_box.currentIndexChanged.connect(
            self.calculate_rcs_controller
        )
        
        # Connect slow time unit selection signals
        self.viewer.rcs_slow_time_units_combo_box.currentIndexChanged.connect(
            self.slow_time_units_combo_box_controller
        )

    def widget_creation_controller(self, plot_widget: Any) -> None:
        """
        Handle new plot widget creation by extending geometry functionality.
        
        This method is called when new plot widgets are created in the MITM
        framework. It sets up signal connections for geometry management.
        
        Parameters
        ----------
        plot_widget : Any
            The newly created plot widget containing canvas and viewer components.
        """
        # Connect geometry signals for RCS extension
        plot_widget.viewer.canvas.geometry_added_signal.connect(
            self.extend_geometry_roi
        )
        plot_widget.viewer.canvas.current_geometry_changed_signal.connect(
            self.calculate_rcs_controller
        )

    def set_mitm_controller(self, controller: Any) -> None:
        """
        Set the MITM controller and establish framework connections.
        
        This method integrates the RCS tool with the main MITM application,
        providing access to SAR data, plot widgets, and annotation functionality.
        
        Parameters
        ----------
        controller : Any
            The PyMITM controller instance providing access to framework services.
        """
        super().set_mitm_controller(controller)
        self.mitm_controller = controller

        # Connect annotation framework signals
        annotation_controller = self.mitm_controller.annotation_controller
        
        annotation_controller.viewer.geometry_connect_signal.connect(
            self.connect_geometry
        )
        annotation_controller.viewer.add_geometry_signal.connect(
            self.calculate_rcs_controller
        )
              
        # Connect widget creation signal
        self.mitm_controller.viewer.widget_creation_signal.connect(
            self.widget_creation_controller
        )

        # Register RCS extension for geometry table
        rcs_geometry_table_extension = RCSGeometryTableWidget()
        annotation_controller.viewer.geometry_table.register_extension(
            "rcs_geometry_table", 
            rcs_geometry_table_extension
        )

        # Connect geometry table update signal
        annotation_controller.viewer.geometry_table.populate_table_signal.connect(
            self.update_geometry_table
        )

    def extend_geometry_roi(self, geometry: Any) -> None:
        """
        Extend a geometry with RCS-specific functionality.
        
        Registers the RCS extension with a newly created geometry object,
        enabling it to store and manage RCS calculation results.
        
        Parameters
        ----------
        geometry : Any
            The geometry object to extend with RCS capabilities.
        """
        rcs_geometry_roi_extension = RCSGeometryROI()
        geometry.register_extension("rcs_geometry_roi", rcs_geometry_roi_extension)

    def get_name(self) -> str:
        """
        Get the display name of this application.
        
        Returns
        -------
        str
            The human-readable application name.
        """
        return "RCS Tool"

    def get_dock_widget(self) -> Viewer:
        """
        Get the main dock widget for this application.
        
        Returns
        -------
        Viewer
            The main viewer widget containing the RCS Tool user interface.
        """
        return self.viewer

    def slow_time_units_combo_box_controller(self) -> None:
        """
        Handle changes to the slow time units selection.
        
        If 'Target Relative' units are selected, prompts the user for a reference
        azimuth angle. Triggers RCS recalculation after unit change.
        """
        # Check if target relative units are selected
        if self.viewer.rcs_slow_time_units_combo_box.currentText() == "Target Relative":
            reference_azimuth_angle = self.viewer.azimuth_reference_angle_dialog()
            self.model.set_reference_azimuth_angle(reference_azimuth_angle)

        # Recalculate RCS with new units
        self.calculate_rcs_controller()

    def plot_rcs_controller(self, geometry: Any) -> None:
        """
        Update RCS plots for the specified geometry.
        
        Calculates and displays RCS data profiles for both slow time (azimuth)
        and fast time (range/frequency) responses using the current measurement units.
        
        Parameters
        ----------
        geometry : Any
            The geometry object defining the region of interest for RCS calculation.
        """
        if self.mitm_controller is None:
            return
            
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None:
            return
            
        meta_data = selected_widget.reader.get_sicds_as_tuple()[0].to_dict()

        # Get current unit selections
        slow_units = self.viewer.rcs_slow_time_units_combo_box.currentText()
        measure_units = self.viewer.rcs_measure_units_combo_box.currentText()
        measure_units_label = f"{measure_units} (dBsm)"
        
        # Compute RCS profile data
        (
            slow_data,
            fast_data,
            slow_x_data,
            fast_x_data,
            slow_axis_label,
            fast_axis_label,
        ) = self.model.compute_rcs_figures(
            selected_widget, meta_data, geometry, slow_units, measure_units
        )

        # Update the plot widgets with calculated data
        self.viewer.rcs_slow_plot_widget.populate_plot(
            slow_x_data,
            slow_data,
            slow_axis_label,
            measure_units_label,
            "Slow Time Response",
        )
        self.viewer.rcs_fast_plot_widget.populate_plot(
            fast_x_data,
            fast_data,
            fast_axis_label,
            measure_units_label,
            "Fast Time Response",
        )

    def measure_units_combo_box_controller(self, index: int) -> None:
        """
        Handle changes to the measurement units selection.
        
        Updates the geometry table to display RCS values in the newly selected
        units and refreshes the table content.
        
        Parameters
        ----------
        index : int
            The index of the selected measurement unit in the combo box.
        """
        if self.mitm_controller is None:
            return
            
        annotation_controller = self.mitm_controller.annotation_controller
        annotation_controller.viewer.geometry_table.set_rcs_display_units(index)
        self.update_geometry_table()

    def update_geometry_table(self) -> None:
        """
        Update the geometry table with current RCS values.
        
        Retrieves geometries from the current canvas and populates the table
        with their RCS properties using the current measurement units and
        void inclusion settings.
        """
        if self.mitm_controller is None:
            return
            
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None or not hasattr(selected_widget.viewer, "canvas"):
            return
            
        geometries = selected_widget.viewer.canvas.get_geometries()
        include_voids = self.mitm_controller.annotation_controller.model.get_include_voids()
        
        annotation_controller = self.mitm_controller.annotation_controller
        annotation_controller.viewer.geometry_table.populate_rcs_column(
            geometries, include_voids
        )

    def connect_geometry(self, geometry: Any) -> None:
        """
        Connect signals for a geometry object.
        
        Sets up signal connections to handle geometry change and removal events
        that require RCS recalculation.
        
        Parameters
        ----------
        geometry : Any
            The geometry object to connect signals for.
        """
        geometry.geometry_changed_signal.connect(self.calculate_rcs_controller)
        geometry.geometry_removed_signal.connect(self.calculate_rcs_controller)
 
    def calculate_rcs_controller(self) -> None:
        """
        Calculate RCS for all geometries and update displays.
        
        This is the primary computation method that:
        1. Processes all geometries to calculate RCS with and without voids
        2. Stores RCS features on geometry objects
        3. Updates the RCS table and plots for the current geometry
        4. Prioritizes the current geometry for display updates
        
        The method handles both void-inclusive and void-exclusive calculations
        to support different analysis scenarios.
        """
        if self.mitm_controller is None:
            return
            
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None or not hasattr(selected_widget.viewer, "canvas"):
            return
            
        canvas = selected_widget.viewer.canvas
        geometries = canvas.get_geometries()
        current_geometry = canvas.get_current_geometry()

        if not geometries:
            return

        annotation_model = self.mitm_controller.annotation_controller.model

        # Process all geometries except current_geometry first
        for geometry in geometries:
            if geometry == current_geometry:
                continue  # Skip current_geometry, process it last

            # Get interior geometries (voids) for this geometry
            interior_geometries = annotation_model.get_interior_geometries(
                selected_widget.get_undecimated_pixel_coordinates, 
                geometry, 
                geometries
            )

            # Create geometry objects with and without voids
            geometry_w_voids = annotation_model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, 
                geometry, 
                interior_geometries
            )
            geometry_wo_voids = annotation_model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, 
                geometry, 
                []
            )

            # Calculate RCS for both versions
            rcs_feature_w_voids = self.model.calculate_rcs(
                selected_widget, geometry_w_voids
            )
            rcs_feature_wo_voids = self.model.calculate_rcs(
                selected_widget, geometry_wo_voids
            )

            # Store results on the geometry using extension methods
            geometry.set_rcs_feature_w_voids(rcs_feature_w_voids)
            geometry.set_rcs_feature_wo_voids(rcs_feature_wo_voids)

        # Process current_geometry last to ensure its display is prioritized
        if current_geometry in geometries:
            interior_geometries = annotation_model.get_interior_geometries(
                selected_widget.get_undecimated_pixel_coordinates, 
                current_geometry, 
                geometries
            )

            # Create geometry objects with and without voids
            geometry_w_voids = annotation_model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, 
                current_geometry, 
                interior_geometries
            )
            geometry_wo_voids = annotation_model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, 
                current_geometry, 
                []
            )

            # Calculate RCS for both versions
            rcs_feature_w_voids = self.model.calculate_rcs(
                selected_widget, geometry_w_voids
            )
            rcs_feature_wo_voids = self.model.calculate_rcs(
                selected_widget, geometry_wo_voids
            )

            # Store results on the geometry
            current_geometry.set_rcs_feature_w_voids(rcs_feature_w_voids)
            current_geometry.set_rcs_feature_wo_voids(rcs_feature_wo_voids)

            # Update UI displays with current geometry's RCS data
            include_voids = annotation_model.get_include_voids()
            if include_voids:
                self.viewer.rcs_table_view.populate_rcs_table(rcs_feature_w_voids)
                self.plot_rcs_controller(geometry_w_voids)
            else:
                self.viewer.rcs_table_view.populate_rcs_table(rcs_feature_wo_voids)
                self.plot_rcs_controller(geometry_wo_voids)