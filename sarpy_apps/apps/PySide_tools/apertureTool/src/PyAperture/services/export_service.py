import os
import cv2
import numpy as np
from typing import Optional, Dict, List, Any
from PySide6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox, QApplication
from PySide6.QtCore import Qt
from sarpy.io.complex.sicd import SICDWriter
from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader


class ExportService:
    """
    Service class for handling export operations.
    
    This class manages the export of processed chips and animations, including
    SICD metadata updates, file writing, and user interface interactions.
    
    Attributes:
        model: The data model containing export parameters and filtering logic
        viewer: The UI viewer containing export controls and display components
        controller: Reference to the main controller for method calls
    """
    
    def __init__(self, model: Any, viewer: Any) -> None:
        """
        Initialize the ExportService.
        
        Args:
            model: The data model containing export parameters and filtering logic
            viewer: The UI viewer containing export controls and display components
        """
        self.model = model
        self.viewer = viewer
        self.controller: Optional[Any] = None  # Reference to controller for calling methods
    
    def set_controller(self, controller: Any) -> None:
        """
        Set reference to controller for calling controller methods.
        
        Args:
            controller: The main controller instance
        """
        self.controller = controller
    
    def export_chip(self, selected_widget: Any, mitm_controller: Any) -> None:
        """
        Export the processed chip with updated SICD metadata.
        
        This method validates the required ROI data, calculates spatial and k-space bounds,
        creates updated SICD metadata with processing history, and writes the chip to file.
        
        Args:
            selected_widget: The currently selected widget containing image data
            mitm_controller: Controller for managing meta-icon updates
        """
        # Validate required data
        aperture_roi = self.model.get_aperture_roi()
        if aperture_roi is None:
            QMessageBox.warning(self.viewer, "Export Error", "No aperture ROI selected")
            return
        
        k_space_roi = self.model.get_k_space_roi()
        if k_space_roi is None:
            QMessageBox.warning(self.viewer, "Export Error", "No k-space ROI selected")
            return
        
        # Calculate spatial bounds
        spatial_bounds = self._calculate_spatial_bounds(aperture_roi, selected_widget)
        k_space_bounds = self._calculate_k_space_bounds(k_space_roi)
        
        # Get the aperture filter
        aperture_filter = self.model.get_aperture_filter()
        if aperture_filter is None:
            QMessageBox.warning(self.viewer, "Export Error", "No aperture filter available")
            return
        
        # Get the original image data from the aperture filter (spatial domain)
        # This is the complex image data before any FFT processing
        original_image_data = aperture_filter._original_image_data
        if original_image_data is None:
            QMessageBox.warning(self.viewer, "Export Error", "No original image data available")
            return
        
        # Create updated chip SICD first
        chip_sicd = self.model.update_chip_sub_aperture_sicd(selected_widget)
        
        # Apply the inverse of what the viewer does
        
        # Get the filtered spatial domain data
        filtered_image = aperture_filter[
            k_space_bounds['ky']:k_space_bounds['ky']+k_space_bounds['kheight'], 
            k_space_bounds['kx']:k_space_bounds['kx']+k_space_bounds['kwidth']
        ]
        
        # TODO: check with Roy this follows matlab
        
        
        desired_kspace = np.zeros(filtered_image.shape, dtype=np.complex64)
        
        # Calculate where to place the k-space data for centered display
        ky_start = k_space_bounds['ky']
        kx_start = k_space_bounds['kx'] 
        ky_size = k_space_bounds['kheight']
        kx_size = k_space_bounds['kwidth']
        
        # Get the original k-space data for this region
        full_kspace = aperture_filter.normalized_phase_history
        kspace_region = full_kspace[ky_start:ky_start+ky_size, kx_start:kx_start+kx_size]
        
        # Place it in the center of our desired k-space
        center_y = desired_kspace.shape[0] // 2
        center_x = desired_kspace.shape[1] // 2
        
        start_y = center_y - ky_size // 2
        start_x = center_x - kx_size // 2
        end_y = start_y + ky_size
        end_x = start_x + kx_size

        # set the bounds
        start_y = max(0, start_y)
        start_x = max(0, start_x)
        end_y = min(desired_kspace.shape[0], end_y)
        end_x = min(desired_kspace.shape[1], end_x)
        
        # Adjust the k-space region size if needed
        actual_ky_size = end_y - start_y
        actual_kx_size = end_x - start_x
        
        desired_kspace[start_y:end_y, start_x:end_x] = kspace_region[:actual_ky_size, :actual_kx_size]
        
        # Now convert this centered k-space to spatial domain
        # Apply the inverse of what the viewer does: ifft2(ifftshift(kspace))
        shifted_kspace = np.fft.ifftshift(desired_kspace)
        filtered_image = np.fft.ifft2(shifted_kspace)
        
        
        # Add processing history to document what was done
        full_kspace = aperture_filter.normalized_phase_history
        chip_sicd = self._add_processing_history(chip_sicd, spatial_bounds, k_space_bounds, full_kspace)
        
        # Ensure the data is complex64
        if filtered_image.dtype != np.complex64:
            filtered_image = filtered_image.astype(np.complex64)
        
        # Get output file path
        file_path = self._get_export_file_path()
        if not file_path:
            return
        
        # Write the chip
        success = self._write_chip_file(file_path, filtered_image, chip_sicd)
        if success:
            self._update_meta_icon_display(chip_sicd, mitm_controller)
            self._show_export_success_message(file_path)
    
    def export_animation(self, selected_widget: Any, mitm_controller: Any) -> None:
        """
        Export animation as MP4 video.
        
        This method generates all animation frames, creates a video file, and manages
        the progress dialog during the export process.
        
        Args:
            selected_widget: The currently selected widget containing image data
            mitm_controller: Controller for managing meta-icon updates
        """
        file_path = self._get_animation_file_path()
        if not file_path:
            return
        
        # Get animation parameters
        fft_bounds = self.model.get_fft_image_bounds(
            SICDTypeCanvasImageReader(selected_widget.reader), 
            self.viewer.phase_history_view.getImageItem()
        )
        
        frame_count = self.model.get_frame_count()
        frame_rate = self.model.get_frame_rate()
        mode = self.viewer.direction_combo_box.currentText()
        aperture_fraction = self.model.get_aperture_fraction()
        
        # Store original frame position
        try:
            original_frame = int(self.viewer.current_frame.text())
        except ValueError:
            original_frame = 0
        
        colormap = self.viewer.phase_history_view.get_color_map()
        
        # Create progress dialog
        progress = QProgressDialog("Preparing to export...", "Cancel", 0, frame_count+1, self.viewer)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        progress.setValue(0)
        QApplication.processEvents()
        
        # Generate all frames
        all_frames = self._generate_animation_frames(
            frame_count, fft_bounds, mode, aperture_fraction, 
            colormap, progress
        )
        
        if not all_frames:
            QMessageBox.warning(self.viewer, "Export Error", "No frames were generated.")
            return
        
        # Write video file
        success = self._write_video_file(file_path, all_frames, frame_rate, progress)
        
        # Restore original frame position
        self._restore_original_frame_position(
            original_frame, fft_bounds, frame_count, mode, aperture_fraction
        )
        
        if success and not progress.wasCanceled():
            QMessageBox.information(
                self.viewer, 
                "Export Complete", 
                f"Animation exported to {file_path}"
            )
    
    def _calculate_spatial_bounds(self, aperture_roi: Any, selected_widget: Any) -> Dict[str, int]:
        """
        Calculate spatial bounds from aperture ROI.
        
        Args:
            aperture_roi: The aperture region of interest
            selected_widget: The currently selected widget containing image data
            
        Returns:
            Dictionary containing spatial bounds (x, y, width, height)
        """
        decimated_pixel_rect = selected_widget.viewer.img.mapFromScene(
            aperture_roi.sceneBoundingRect()).boundingRect()
        
        return {
            'x': int(decimated_pixel_rect.x() * selected_widget.model.step_size + 
                    selected_widget.model.xmin_map_to_full_image),
            'y': int(decimated_pixel_rect.y() * selected_widget.model.step_size + 
                    selected_widget.model.ymin_map_to_full_image),
            'width': int(decimated_pixel_rect.width() * selected_widget.model.step_size),
            'height': int(decimated_pixel_rect.height() * selected_widget.model.step_size)
        }
    
    def _calculate_k_space_bounds(self, k_space_roi: Any) -> Dict[str, int]:
        """
        Calculate k-space bounds from ROI.
        
        Args:
            k_space_roi: The k-space region of interest
            
        Returns:
            Dictionary containing k-space bounds (kx, ky, kwidth, kheight)
        """
        k_space_pos = k_space_roi.pos()
        k_space_size = k_space_roi.size()
        
        return {
            'kx': int(k_space_pos[0]),
            'ky': int(k_space_pos[1]),
            'kwidth': int(k_space_size[0]),
            'kheight': int(k_space_size[1])
        }
    
    def _add_processing_history(self, chip_sicd: Any, spatial_bounds: Dict[str, int], 
                              k_space_bounds: Dict[str, int], full_kspace: np.ndarray) -> Any:
        """
        Add processing history to SICD metadata.
        
        Args:
            chip_sicd: The SICD metadata object to update
            spatial_bounds: Dictionary containing spatial bounds information
            k_space_bounds: Dictionary containing k-space bounds information
            full_kspace: The full k-space data array
            
        Returns:
            Updated SICD metadata object with processing history
        """
        if chip_sicd.ImageFormation is None:
            from sarpy.io.complex.sicd_elements.ImageFormation import ImageFormationType
            chip_sicd.ImageFormation = ImageFormationType()
        
        if chip_sicd.ImageFormation.Processings is None:
            chip_sicd.ImageFormation.Processings = []
        
        # Calculate processing parameters
        k_rows, k_cols = full_kspace.shape
        row_fraction = k_space_bounds['kheight'] / k_rows
        col_fraction = k_space_bounds['kwidth'] / k_cols
        window_type = self.viewer.window_filter_combo_box.currentText()
        
        from sarpy.io.complex.sicd_elements.ImageFormation import ProcessingType
        processing_step = ProcessingType()
        processing_step.Type = 'Aperture Tool Processing'
        processing_step.Applied = True
        processing_step.Parameters = {
            'PolygonMasked': 'True',
            'WindowType': window_type if window_type and window_type != "None" else 'None',
            'KSpaceRowFraction': f'{row_fraction:.3f}',
            'KSpaceColFraction': f'{col_fraction:.3f}',
            'SpatialChipBounds': f'Row: {spatial_bounds["y"]}-{spatial_bounds["y"]+spatial_bounds["height"]}, Col: {spatial_bounds["x"]}-{spatial_bounds["x"]+spatial_bounds["width"]}',
            'KSpaceBounds': f'Row: {k_space_bounds["ky"]}-{k_space_bounds["ky"]+k_space_bounds["kheight"]}, Col: {k_space_bounds["kx"]}-{k_space_bounds["kx"]+k_space_bounds["kwidth"]}'
        }
        chip_sicd.ImageFormation.Processings.append(processing_step)
        
        return chip_sicd
    
    def _get_export_file_path(self) -> Optional[str]:
        """
        Get file path for chip export.
        
        Returns:
            Selected file path or None if cancelled
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self.viewer, 
            "Save Processed Chip", 
            "", 
            "NITF Files (*.ntf);;All Files (*.*)"
        )
        return file_path
    
    def _get_animation_file_path(self) -> Optional[str]:
        """
        Get file path for animation export.
        
        Returns:
            Selected file path with .mp4 extension or None if cancelled
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self.viewer, 
            "Save Animation", 
            "", 
            "MP4 Files (*.mp4)"
        )
        
        if file_path and not file_path.lower().endswith('.mp4'):
            file_path += '.mp4'
        
        return file_path
    
    def _write_chip_file(self, file_path: str, filtered_image: np.ndarray, chip_sicd: Any) -> bool:
        """
        Write chip data to file.
        
        Args:
            file_path: Path where the chip file should be written
            filtered_image: The filtered image data to write
            chip_sicd: The SICD metadata for the chip
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure the data is complex64
            if filtered_image.dtype != np.complex64:
                filtered_image = filtered_image.astype(np.complex64)
            
            writer = SICDWriter(file_path, chip_sicd)
            writer.write_chip(filtered_image)
            writer.close()
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.viewer, 
                "Export Error", 
                f"An error occurred while writing the chip: {str(e)}"
            )
            return False
    
    def _update_meta_icon_display(self, chip_sicd: Any, mitm_controller: Any) -> None:
        """
        Update meta icon display.
        
        Args:
            chip_sicd: The SICD metadata for the chip
            mitm_controller: Controller for managing meta-icon updates
        """
        updated_meta_data = mitm_controller.model.get_metadata_from_sicd(chip_sicd)
        self.viewer.aperture_meta_icon.display_metaicon(updated_meta_data)
    
    def _show_export_success_message(self, file_path: str) -> None:
        """
        Show export success message.
        
        Args:
            file_path: Path where the file was exported
        """
        QMessageBox.information(
            self.viewer, 
            "Export Complete", 
            f"Processed sub-aperture chip exported to {file_path}\n\n"
            f"Metadata includes:\n"
            f"- Updated geometry for sub-aperture timing\n"
            f"- Corrected IPR for reduced aperture size\n"
            f"- Processing history documentation"
        )
    
    def _generate_animation_frames(self, frame_count: int, fft_bounds: Any, mode: str, 
                             aperture_fraction: float, colormap: Any, 
                             progress: QProgressDialog) -> Optional[List[np.ndarray]]:
        """
        Generate all animation frames for video export.
        """
        all_frames = []
        
        for frame_num in range(frame_count + 1):  
            if progress.wasCanceled():
                break
            
            progress.setLabelText(f"Generating frame {frame_num}/{frame_count}...")
            QApplication.processEvents()
            
            # Calculate new ROI position/size
            geometry_translation = self.model.step_animation(
                fft_bounds, min(frame_num, frame_count-1), frame_count, mode,
                aperture_fraction, self.model.get_aperture_min(), 
                self.model.get_aperture_max(), self.model.get_animation_direction()
            )
            
            # Apply to ROI
            k_space_roi = self.model.get_k_space_roi()
            k_space_roi.setPos(geometry_translation[0])
            k_space_roi.setSize(geometry_translation[1])
            
            # Update filtered view
            if self.controller:
                self.controller.k_space_roi_changed_controller(k_space_roi)
            
            # Update UI
            self.viewer.current_frame.setText(str(min(frame_num, frame_count-1)))
            QApplication.processEvents()
            
            # Capture images
            k_space_img = self.viewer.phase_history_view.getImageItem().image
            filtered_img = self.viewer.filtered_view.getImageItem().image
            
            if k_space_img is None or filtered_img is None:
                continue
                
            # Process and combine frames
            frame = self._create_composite_frame(k_space_img, filtered_img, colormap, 
                                            k_space_roi, frame_num, frame_count)
            all_frames.append(frame)
            
            progress.setValue(frame_num + 1)
        
        return all_frames

    def _write_video_file(self, file_path: str, all_frames: List[np.ndarray], 
                        frame_rate: float, progress: QProgressDialog) -> bool:
        """
        Write frames to MP4 video file.
        """
        if not all_frames:
            return False
        
        height, width = all_frames[0].shape[:2]
        
        progress.setLabelText("Writing video file...")
        progress.setValue(0)
        progress.setMaximum(len(all_frames))
        QApplication.processEvents()
        
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(file_path, fourcc, frame_rate, (width, height))
            
            for i, frame in enumerate(all_frames):
                if progress.wasCanceled():
                    video_writer.release()
                    return False
                    
                video_writer.write(frame)
                progress.setValue(i + 1)
                QApplication.processEvents()
                
            video_writer.release()
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.viewer, "Export Error", 
                f"Error writing video: {str(e)}"
            )
            return False

    def _create_composite_frame(self, k_space_img: np.ndarray, filtered_img: np.ndarray,
                            colormap: Any, k_space_roi: Any, frame_num: int, 
                            frame_count: int) -> np.ndarray:
        """
        Create composite frame combining k-space and filtered views.
        """
        # Apply colormap to k-space
        k_min, k_max = k_space_img.min(), k_space_img.max()
        if k_max > k_min:
            k_norm = (k_space_img - k_min) / (k_max - k_min)
            k_colored_rgba = colormap.map(k_norm, mode='byte')
            k_frame = cv2.cvtColor(k_colored_rgba[:, :, :3], cv2.COLOR_RGB2BGR)
        else:
            k_frame = np.zeros((*k_space_img.shape, 3), dtype=np.uint8)
        
        # Convert filtered image to 8-bit BGR
        if filtered_img.dtype != np.uint8:
            f_min, f_max = filtered_img.min(), filtered_img.max()
            if f_max > f_min:
                f_frame = ((filtered_img - f_min) / (f_max - f_min) * 255).astype(np.uint8)
            else:
                f_frame = np.zeros_like(filtered_img, dtype=np.uint8)
        else:
            f_frame = filtered_img.copy()
        
        if len(f_frame.shape) == 2:
            f_frame = cv2.cvtColor(f_frame, cv2.COLOR_GRAY2BGR)
        
        # Create composite based on include_kspace setting
        if self.model.get_include_kspace():
            composite_frame = self._combine_frames_side_by_side(k_frame, f_frame)
            self._draw_roi_overlay(composite_frame, k_space_roi, k_frame.shape)
        else:
            composite_frame = f_frame
        
        # Add annotations if enabled
        if self.model.get_include_annotations():
            self._add_frame_annotations(composite_frame, frame_num, frame_count)
        
        return composite_frame