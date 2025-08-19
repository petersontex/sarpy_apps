import time
import numpy as np
from typing import Tuple, Optional, Any
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader

class AnimationService:
    """
    Service class for handling animation-related operations.
    
    This class manages the animation of aperture filtering, including frame processing,
    animation controls, and the main animation loop for visualizing sub-aperture data.
    
    Attributes:
        model: The data model containing animation parameters and filtering logic
        viewer: The UI viewer containing animation controls and display components
    """
    
    def __init__(self, model: Any, viewer: Any) -> None:
        """
        Initialize the AnimationService.
        
        Args:
            model: The data model containing animation parameters and filtering logic
            viewer: The UI viewer containing animation controls and display components
        """
        self.model = model
        self.viewer = viewer
    
    def process_frame(self, frame: int, selected_widget: Any, mitm_controller: Any) -> None:
        """
        Process a single animation frame.
        
        This method calculates the new ROI position and size for the current frame,
        updates the k-space ROI, forms the filtered image, and updates the UI display.
        
        Args:
            frame: The current frame number to process
            selected_widget: The currently selected widget containing image data
            mitm_controller: Controller for managing meta-icon updates
        """
        # Calculate new ROI position/size using the exact same pattern as original
        fft_bounds = self.model.get_fft_image_bounds(
            SICDTypeCanvasImageReader(selected_widget.reader), 
            self.viewer.phase_history_view.getImageItem()
        )
        
        frame_count = self.model.get_frame_count()
        geometry_translation = self.model.step_animation(
            fft_bounds,
            frame,
            frame_count,
            self.viewer.direction_combo_box.currentText(),
            self.model.get_aperture_fraction(),
            self.model.get_aperture_min(),
            self.model.get_aperture_max(),
            self.model.get_animation_direction()
        )
        
        # Apply to ROI
        k_space_roi = self.model.get_k_space_roi()
        k_space_roi.setPos(geometry_translation[0])
        k_space_roi.setSize(geometry_translation[1])
        
        # Update the model's k-space ROI reference
        self.model.set_k_space_roi(k_space_roi)
        
        # Update the filtered image display
        filtered_image = self.model.form_filtered_image(
            selected_widget, 
            self.viewer.phase_history_view, 
            k_space_roi
        )
        self.viewer.filtered_view.setImage(filtered_image)
        
        # Update UI
        self.viewer.current_frame.setText(str(frame))
        QApplication.processEvents()
        
        # Update the sub aperture chip sicd for meta-icon
        updated_chip_sicd = self.model.update_chip_sub_aperture_sicd(selected_widget)
        self._update_meta_icon_display(updated_chip_sicd, mitm_controller)
    
    def _update_meta_icon_display(self, updated_chip_sicd: Any, mitm_controller: Any) -> None:
        """
        Update meta icon display with chip SICD data.
        
        Args:
            updated_chip_sicd: The updated SICD metadata for the current chip
            mitm_controller: Controller for managing meta-icon updates
        """
        updated_meta_data = mitm_controller.model.get_metadata_from_sicd(updated_chip_sicd)
        self.viewer.aperture_meta_icon.display_metaicon(updated_meta_data)
    
    def toggle_animation_controls(self, enabled: bool) -> None:
        """
        Enable or disable animation controls during playback.
        
        This method controls the availability of animation UI elements to prevent
        user interaction during animation playback.
        
        Args:
            enabled: True to enable controls, False to disable them
        """
        controls = [
            self.viewer.step_start_frame_button,
            self.viewer.step_back_frame_button,
            self.viewer.step_forward_frame_button,
            self.viewer.step_end_frame_button,
            self.viewer.frame_count,
            self.viewer.frame_rate,
            self.viewer.aperture_min,
            self.viewer.aperture_max,
            self.viewer.aperture_fraction,
            self.viewer.reverse_toggle,
            self.viewer.play_button
        ]
        
        for control in controls:
            control.setEnabled(enabled)
        
        k_space_roi = self.model.get_k_space_roi()
        if k_space_roi:
            k_space_roi.setEnabled(enabled)
    
    def run_animation(self, selected_widget: Any, mitm_controller: Any) -> None:
        """
        Execute the main animation loop.
        
        This method handles the complete animation sequence, including initialization,
        frame processing, cycling behavior, and cleanup. It manages the animation
        state and responds to pause/stop conditions.
        
        Args:
            selected_widget: The currently selected widget containing image data
            mitm_controller: Controller for managing meta-icon updates
        """
        self.toggle_animation_controls(False)
        frame_count = self.model.get_frame_count()
        
        # Get the current frame from the UI
        try:
            current_frame = int(self.viewer.current_frame.text())
            current_frame = max(0, min(current_frame, frame_count-1))
        except (ValueError, AttributeError):
            current_frame = 0
        
        # Check if we're at the last frame and handle cycling
        if current_frame >= frame_count - 1:
            current_frame = 0
        
        # Set initial frame display
        self.viewer.current_frame.setText(str(current_frame))
        
        # Animation loop
        while True:
            if not self.model.get_pause_flag():
                self.process_frame(current_frame, selected_widget, mitm_controller)
                current_frame += 1
                
                # Check if we've reached the end
                if current_frame >= frame_count:
                    if self.viewer.cycle_continuously_toggle.isChecked():
                        current_frame = 0
                    else:
                        break
                
                # Wait for next frame
                time.sleep(1/self.model.get_frame_rate())
            else:
                # User paused - exit
                self.model.set_pause_flag(False)
                self.toggle_animation_controls(True)
                return
            
            # Check for pause after each frame
            if self.model.get_pause_flag():
                self.model.set_pause_flag(False)
                self.toggle_animation_controls(True)
                return
        
        self.toggle_animation_controls(True)