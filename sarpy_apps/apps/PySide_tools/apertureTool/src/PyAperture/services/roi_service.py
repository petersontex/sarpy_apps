from typing import Any, Optional, List

from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader


class ROIService:
    """
    Service class for handling ROI (Region of Interest) operations.
    
    This class manages aperture and k-space ROI changes, including polygon creation,
    k-space image formation, and filtered image updates.
    
    Attributes:
        model: The data model containing ROI parameters and filtering logic
        viewer: The UI viewer containing ROI controls and display components
    """
    
    def __init__(self, model: Any, viewer: Any) -> None:
        """
        Initialize the ROIService.
        
        Args:
            model: The data model containing ROI parameters and filtering logic
            viewer: The UI viewer containing ROI controls and display components
        """
        self.model = model
        self.viewer = viewer
    
    def handle_aperture_roi_change(self, aperture_roi: Any, selected_widget: Any, 
                                 mitm_controller: Any) -> Any:
        """
        Handle changes to the aperture ROI.
        
        This method processes aperture ROI changes by setting up the k-space ROI,
        creating aperture polygons based on void inclusion settings, forming k-space
        images, and updating the display.
        
        Args:
            aperture_roi: The aperture region of interest that changed
            selected_widget: The currently selected widget containing image data
            mitm_controller: Controller for managing annotations and geometries
            
        Returns:
            The k-space ROI object for signal connection in the controller
        """
        self.model.set_aperture_roi(aperture_roi)
        reader = SICDTypeCanvasImageReader(selected_widget.reader)
        
        center = self.viewer.phase_history_view.get_center_coords()
        view_ratio = self.viewer.phase_history_view.get_view_size_ratio()

        # Setup k-space ROI and get reference to it
        k_space_roi = self._setup_k_space_roi(center, view_ratio)

        # Create aperture polygon based on void inclusion setting
        if mitm_controller.annotation_controller.model.get_include_voids():
            geometries = selected_widget.get_geometries()
            interior_geometries = mitm_controller.annotation_controller.model.get_interior_geometries(
                selected_widget.get_undecimated_pixel_coordinates, 
                aperture_roi, 
                geometries
            )
            aperture_roi_polygon = mitm_controller.annotation_controller.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, 
                aperture_roi, 
                interior_geometries
            )
        else:
            aperture_roi_polygon = mitm_controller.annotation_controller.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, 
                aperture_roi, 
                []
            )

        # Form and display k-space image
        k_space_image = self.model.form_k_space_image(
            selected_widget, 
            reader, 
            aperture_roi, 
            aperture_roi_polygon
        )

        self.viewer.phase_history_view.setImage(k_space_image)
        
        # Set k-space ROI boundaries
        fft_bounds = self.model.get_fft_image_bounds(
            SICDTypeCanvasImageReader(selected_widget.reader), 
            self.viewer.phase_history_view.getImageItem()
        )
        if k_space_roi:
            k_space_roi.set_boundary(fft_bounds)
        
        # Return the k_space_roi so controller can connect signals
        return k_space_roi
    
    def handle_k_space_roi_change(self, k_space_roi: Any, selected_widget: Any) -> None:
        """
        Handle changes to the k-space ROI.
        
        This method processes k-space ROI changes by forming a filtered image
        and updating the filtered view display.
        
        Args:
            k_space_roi: The k-space region of interest that changed
            selected_widget: The currently selected widget containing image data
        """
        filtered_image = self.model.form_filtered_image(
            selected_widget, 
            self.viewer.phase_history_view, 
            k_space_roi
        )
        self.viewer.filtered_view.setImage(filtered_image)
    
    def _setup_k_space_roi(self, center: List[float], view_ratio: float) -> Optional[Any]:
        """
        Setup k-space ROI if it doesn't exist.
        
        This method checks if a k-space ROI already exists in the scene and creates
        one if it doesn't exist.
        
        Args:
            center: Center coordinates for the ROI
            view_ratio: Size ratio for the ROI
            
        Returns:
            The k-space ROI object or None if one already exists
        """
        from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.view.aperture_viewer \
            import KSpaceROI
        
        # Check if k-space ROI already exists
        has_roi = any(
            isinstance(item, KSpaceROI) 
            for item in self.viewer.phase_history_view.scene.items()
        )
        
        if not has_roi:
            # Create new k-space ROI
            k_space_roi = KSpaceROI(
                pos=center,
                size=[view_ratio, view_ratio]
            )
            self.viewer.phase_history_view.addItem(k_space_roi)
            # Note: Signal connection should be handled in controller
            self.model.set_k_space_roi(k_space_roi)
            return k_space_roi
        
        return None