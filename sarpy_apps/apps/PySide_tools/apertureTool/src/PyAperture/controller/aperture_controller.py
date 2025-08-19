from typing import Any, Optional, Union, TYPE_CHECKING
from PySide6.QtWidgets import QApplication, QLineEdit
from PySide6.QtCore import QRectF, Qt

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.subapplication import AbstractApp
from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.model.aperture_model \
    import ApertureModel
from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.view.aperture_viewer \
    import ApertureViewer, KSpaceROI
from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.services.animation_service \
    import AnimationService
from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.services.roi_service \
    import ROIService
from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.services.export_service \
    import ExportService

if TYPE_CHECKING:
    from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader
    from sarpy.io.complex.sicd_elements.SICD import SICDType
    from sarpy.geometry.geometry_elements import Polygon


class ApertureController(AbstractApp):
    """
    Controller class for the Aperture Tool following MVC pattern.
    
    This class serves as the central coordinator between the user interface (View),
    business logic (Model), and various services. It handles all user interactions,
    processes UI events, and coordinates data flow between components.
    
    The controller maintains references to:
    - Model: For business logic and data management
    - View: For user interface components
    - Services: For specialized operations (animation, ROI, export)
    - MITM Controller: For integration with the larger application framework
    
    Attributes
    ----------
    model : ApertureModel
        The data model containing business logic and state
    viewer : ApertureViewer
        The main view widget for user interaction
    animation_service : AnimationService
        Service for handling animation operations
    roi_service : ROIService
        Service for managing region of interest operations
    export_service : ExportService
        Service for handling data export operations
    mitm_controller : Optional[Any]
        Reference to the main MITM controller (set after initialization)
        
    Methods
    -------
    connect_geometry(geometry: Any) -> None
        Connect geometry signals for ROI change handling
    aperture_roi_changed_controller(aperture_roi: Any) -> None
        Handle aperture ROI change events
    k_space_roi_changed_controller(k_space_roi: Any) -> None
        Handle k-space ROI change events
    export_animation() -> None
        Export animation to video file
    """

    def __init__(self, id: str) -> None:
        """
        Initialize the Aperture Controller.
        
        Sets up the MVC components and services, connects UI signals,
        and prepares the controller for operation.
        
        Parameters
        ----------
        id : str
            Unique identifier for this controller instance
        """
        super().__init__()
        
        # Initialize MVC components
        self.model: ApertureModel = ApertureModel()
        self.viewer: ApertureViewer = ApertureViewer()
        
        # Initialize services
        self.animation_service: AnimationService = AnimationService(self.model, self.viewer)
        self.roi_service: ROIService = ROIService(self.model, self.viewer)
        self.export_service: ExportService = ExportService(self.model, self.viewer)
        
        # Set controller reference in services that need it
        self.export_service.set_controller(self)
        
        # Connect UI signals to controller methods
        self._connect_ui_signals()
        
        # Reference to MITM controller (set later)
        self.mitm_controller: Optional[Any] = None

    def _connect_ui_signals(self) -> None:
        """
        Connect all UI signals to their respective controller methods.
        
        Establishes the signal-slot connections between UI widgets and
        controller methods to handle user interactions. This includes
        animation controls, parameter inputs, toggles, and export functions.
        """
        # Animation controls - connect directly to main methods
        self.viewer.play_button.clicked.connect(self.play_button_controller)
        self.viewer.pause_button.clicked.connect(self.pause_button_controller)
        self.viewer.step_forward_frame_button.clicked.connect(self.step_forward_frame_button_controller)
        self.viewer.step_back_frame_button.clicked.connect(self.step_back_frame_button_controller)
        self.viewer.step_start_frame_button.clicked.connect(self.step_start_frame_button_controller)
        self.viewer.step_end_frame_button.clicked.connect(self.step_end_frame_button_controller)
        
        # Parameter controls - connect directly to main methods
        self.viewer.frame_count.textChanged.connect(self._handle_frame_count_change)
        self.viewer.frame_count.editingFinished.connect(self.frame_count_controller)
        self.viewer.frame_rate.editingFinished.connect(self.frame_rate_controller)
        self.viewer.aperture_fraction.editingFinished.connect(self.aperture_fraction_controller)
        self.viewer.aperture_min.editingFinished.connect(self.aperture_min_controller)
        self.viewer.aperture_max.editingFinished.connect(self.aperture_max_controller)
        
        # Toggle controls - connect directly to main methods
        self.viewer.reverse_toggle.checkStateChanged.connect(self.reverse_toggle_controller)
        self.viewer.include_annotations_toggle.checkStateChanged.connect(self.include_annotations_controller)
        self.viewer.include_kspace_toggle.checkStateChanged.connect(self.include_kspace_controller)
        
        # Processing toggles - connect directly to main methods
        if hasattr(self.viewer, 'deskew_toggle'):
            self.viewer.deskew_toggle.checkStateChanged.connect(self.deskew_controller)
        if hasattr(self.viewer, 'weighting_toggle'):
            self.viewer.weighting_toggle.checkStateChanged.connect(self.uniform_weighting_controller)
        
        # Window filter - connect directly to main method
        self.viewer.window_filter_combo_box.currentIndexChanged.connect(self.window_filter_combo_box_controller)
        
        # Export controls - connect directly to main methods
        self.viewer.animation_export_button.clicked.connect(self.export_animation)
        self.viewer.export_chip_button.clicked.connect(self.export_chip)

    # Animation control handlers - simplified to main implementations
    def play_button_controller(self) -> None:
        """
        Handle play button click event.
        
        Initiates animation playback using the animation service if a valid
        widget is currently selected in the MITM controller.
        """
        if self.mitm_controller is None:
            return
        
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None:
            return
        
        self.animation_service.run_animation(selected_widget, self.mitm_controller)

    def pause_button_controller(self) -> None:
        """
        Handle pause button click event.
        
        Sets the pause flag in the model to stop any currently running animation.
        """
        self.model.set_pause_flag(True)

    def step_forward_frame_button_controller(self) -> None:
        """
        Handle step forward button click event.
        
        Advances the animation by one frame, wrapping to the beginning
        if at the last frame.
        """
        current_frame = self._get_current_frame_safely()
        frame_count = self.model.get_frame_count()
        
        next_frame = 0 if current_frame >= frame_count - 1 else current_frame + 1
        self._process_single_frame(next_frame)

    def step_back_frame_button_controller(self) -> None:
        """
        Handle step back button click event.
        
        Steps the animation back by one frame, wrapping to the end
        if at the first frame.
        """
        current_frame = self._get_current_frame_safely()
        frame_count = self.model.get_frame_count()
        
        prev_frame = frame_count - 1 if current_frame <= 0 else current_frame - 1
        self._process_single_frame(prev_frame)

    def step_start_frame_button_controller(self) -> None:
        """
        Handle step to start button click event.
        
        Jumps the animation to the first frame (frame 0).
        """
        self._process_single_frame(0)

    def step_end_frame_button_controller(self) -> None:
        """
        Handle step to end button click event.
        
        Jumps the animation to the last frame.
        """
        self._process_single_frame(self.model.get_frame_count() - 1)

    # Parameter control handlers - simplified to main implementations
    def _handle_frame_count_change(self) -> None:
        """
        Handle frame count text change event (real-time validation).
        
        Validates the frame count input in real-time and updates the
        total frames display. This provides immediate feedback to the user.
        """
        frame_count = self.model.ensure_valid_integer(self.viewer.frame_count.text())
        self.viewer.total_frames.setText(str(frame_count - 1))

    def frame_count_controller(self) -> None:
        """
        Handle frame count editing finished event (final validation and update).
        
        Performs final validation when the user finishes editing the frame count,
        updates the UI display, and commits the value to the model.
        """
        frame_count = self.model.ensure_valid_integer(self.viewer.frame_count.text())
        self.viewer.frame_count.setText(str(frame_count))
        self.viewer.total_frames.setText(str(frame_count - 1))
        self.model.set_frame_count(frame_count)

    def frame_rate_controller(self) -> None:
        """
        Handle frame rate change event.
        
        Validates and updates the animation frame rate when the user
        finishes editing the frame rate field.
        """
        frame_rate = self.model.ensure_valid_integer(self.viewer.frame_rate.text())
        self.viewer.frame_rate.setText(str(frame_rate))
        self.model.set_frame_rate(frame_rate)

    def aperture_fraction_controller(self) -> None:
        """
        Handle aperture fraction change event.
        
        Validates and updates the aperture fraction used in animations
        when the user finishes editing the field.
        """
        aperture_fraction = self.model.ensure_valid_percentage(self.viewer.aperture_fraction.text())
        self.viewer.aperture_fraction.setText(str(aperture_fraction))
        self.model.set_aperture_fraction(aperture_fraction)

    def aperture_min_controller(self) -> None:
        """
        Handle aperture minimum change event.
        
        Validates and updates the minimum aperture percentage when
        the user finishes editing the field.
        """
        aperture_min = self.model.ensure_valid_percentage(self.viewer.aperture_min.text())
        self.viewer.aperture_min.setText(str(aperture_min))
        self.model.set_aperture_min(aperture_min)

    def aperture_max_controller(self) -> None:
        """
        Handle aperture maximum change event.
        
        Validates and updates the maximum aperture percentage when
        the user finishes editing the field.
        """
        aperture_max = self.model.ensure_valid_percentage(self.viewer.aperture_max.text())
        self.viewer.aperture_max.setText(str(aperture_max))
        self.model.set_aperture_max(aperture_max)

    # Toggle control handlers - simplified to main implementations
    def reverse_toggle_controller(self) -> None:
        """
        Handle reverse animation toggle event.
        
        Updates the animation direction based on the toggle state.
        When checked, animations play backward; when unchecked, forward.
        """
        direction = "backward" if self.viewer.reverse_toggle.isChecked() else "forward"
        self.model.set_animation_direction(direction)

    def include_annotations_controller(self) -> None:
        """
        Handle include annotations toggle event.
        
        Updates whether annotations (frame numbers, etc.) are included
        in exported animations and displays.
        """
        include = self.viewer.include_annotations_toggle.isChecked()
        self.model.set_include_annotations(include)

    def include_kspace_controller(self) -> None:
        """
        Handle include k-space toggle event.
        
        Updates whether k-space visualization is included alongside
        the filtered image in exports and displays.
        """
        include = self.viewer.include_kspace_toggle.isChecked()
        self.model.set_include_kspace(include)

    def deskew_controller(self) -> None:
        """
        Handle deskew toggle event.
        
        Updates the deskewing option and reprocesses the current
        aperture ROI if one exists to apply the change immediately.
        """
        if hasattr(self.viewer, 'deskew_toggle'):
            self.model.set_deskew(self.viewer.deskew_toggle.isChecked())
            # Reprocess if we have an aperture ROI
            if self.model.get_aperture_roi() is not None:
                self.aperture_roi_changed_controller(self.model.get_aperture_roi())

    def uniform_weighting_controller(self) -> None:
        """
        Handle uniform weighting toggle event.
        
        Updates the deweighting option and reprocesses the current
        aperture ROI if one exists to apply the change immediately.
        """
        if hasattr(self.viewer, 'weighting_toggle'):
            self.model.set_deweighting(self.viewer.weighting_toggle.isChecked())
            # Reprocess if we have an aperture ROI
            if self.model.get_aperture_roi() is not None:
                self.aperture_roi_changed_controller(self.model.get_aperture_roi())

    # Processing control handlers
    def window_filter_combo_box_controller(self) -> None:
        """
        Handle window filter combo box change event.
        
        Applies the selected windowing function to the current aperture
        filter to reduce sidelobes in the processed imagery.
        """
        window_type = self.viewer.window_filter_combo_box.currentText()
        
        if self.model.get_aperture_filter() is None:
            print("No aperture filter available")
            return
        
        k_space_roi = self.model.get_k_space_roi()
        self.k_space_roi_changed_controller(k_space_roi)
        
        self.model.apply_window_function(window_type)

    # ROI event handlers
    def aperture_roi_changed_controller(self, aperture_roi: Any) -> None:
        """
        This method is called when the spatial domain region of interest
        changes. It triggers reprocessing of the k-space image and updates
        the display.
        
        Parameters
        ----------
        aperture_roi : Any
            The changed aperture ROI object
        """
        self.model.set_aperture_roi(aperture_roi)
        selected_widget = self.mitm_controller.get_current_widget()
        
        from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader
        reader = SICDTypeCanvasImageReader(selected_widget.reader)
        
        center = self.viewer.phase_history_view.get_center_coords()
        view_ratio = self.viewer.phase_history_view.get_view_size_ratio()

        self.k_space_roi_controller(center, view_ratio)

        if self.mitm_controller.annotation_controller.model.get_include_voids():
            geometries = selected_widget.get_geometries()
            interior_geometries = self.mitm_controller.annotation_controller.model.get_interior_geometries(
                selected_widget.get_undecimated_pixel_coordinates, aperture_roi, geometries)
            aperture_roi_polygon = self.mitm_controller.annotation_controller.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, aperture_roi, interior_geometries)
        else:
            aperture_roi_polygon = self.mitm_controller.annotation_controller.model.create_geometry(
                selected_widget.get_undecimated_pixel_coordinates, aperture_roi, [])

        k_space_image = self.model.form_k_space_image(selected_widget, reader, aperture_roi, aperture_roi_polygon)

        self.viewer.phase_history_view.setImage(k_space_image)
        fft_bounds = self.model.get_fft_image_bounds(
            SICDTypeCanvasImageReader(selected_widget.reader), 
            self.viewer.phase_history_view.getImageItem()
        )
        k_space_roi = self.model.get_k_space_roi()
        k_space_roi.set_boundary(fft_bounds)
        
        # Update weighting toggle based on SICD metadata
        self.weighting_enabled_controller(self.model.check_weighting(reader.get_sicd()))

    def k_space_roi_changed_controller(self, k_space_roi: Any) -> None:
        """
        This method is called when the k-space region of interest changes.
        It triggers regeneration of the filtered image based on the new
        k-space selection.
        
        Parameters
        ----------
        k_space_roi : Any
            The changed k-space ROI object
        """
        selected_widget = self.mitm_controller.get_current_widget()

        filtered_image = self.model.form_filtered_image(
            selected_widget, self.viewer.phase_history_view, k_space_roi)
        self.viewer.filtered_view.setImage(filtered_image)

    def k_space_roi_controller(self, center: list[float], view_ratio: float) -> None:
        """
        Creates or manages the k-space ROI widget based on the current
        view center and size ratio.

        Parameters
        ----------
        center : list[float]
            Center coordinates [x, y] for ROI positioning
        view_ratio : float
            Size ratio for ROI dimensions
        """
        flag = 0
        for item in self.viewer.phase_history_view.scene.items():
            if isinstance(item, KSpaceROI):
                flag = 1
            else:
                pass
        
        if not flag:
            # Does not currently have a KSpaceROI so add one
            k_space_roi = KSpaceROI(
                pos=center,
                size=[view_ratio, view_ratio]
            )
            self.viewer.phase_history_view.addItem(k_space_roi)
            k_space_roi.roi_changed_finished_signal.connect(self.k_space_roi_changed_controller)
            self.model.set_k_space_roi(k_space_roi)
        else:
            # already has a KSpaceROI
            pass

    # Geometry connection method
    def connect_geometry(self, geometry: Any) -> None:
        """
        Connect geometry signals for ROI changes.
        
        Establishes signal connections between geometry objects and
        the aperture ROI change controller for proper event handling.
        
        Parameters
        ----------
        geometry : Any
            Geometry object with change and click signals
        """
        geometry.geometry_changed_signal.connect(self.aperture_roi_changed_controller)
        geometry.geometry_clicked_signal.connect(self.aperture_roi_changed_controller)

    def weighting_enabled_controller(self, weighting_available: bool) -> None:
        """
        Enable/disable weighting toggle based on SICD metadata.
        
        Controls the availability of the weighting toggle based on whether
        the current SICD data contains the necessary weighting functions.
        
        Parameters
        ----------
        weighting_available : bool
            Whether weighting functions are available in the SICD metadata
        """
        if hasattr(self.viewer, 'weighting_toggle'):
            if weighting_available:
                self.viewer.weighting_toggle.setEnabled(True)
                self.viewer.weighting_toggle.setChecked(self.model.get_deweighting())
            else:
                self.viewer.weighting_toggle.setChecked(False)
                self.viewer.weighting_toggle.setEnabled(False)
                self.model.set_deweighting(False)

    def export_animation(self) -> None:
        """
        Export animation to video file.
        
        Creates an MP4 video file showing the aperture animation sequence.
        This method handles the complete export process including frame
        generation, video encoding, and user interaction.
        """
        if self.mitm_controller is None:
            return
        
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None:
            return
        
        # User will select a output path/file
        from PySide6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox
        file_path, _ = QFileDialog.getSaveFileName(
            self.viewer, 
            "Save Animation", 
            "", 
            "MP4 Files (*.mp4)"
        )
        
        if not file_path:
            return  # User canceled
        
        if not file_path.lower().endswith('.mp4'):
            file_path += '.mp4'
        
        # Get animation parameters
        from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader
        fft_bounds = self.model.get_fft_image_bounds(
            SICDTypeCanvasImageReader(selected_widget.reader), 
            self.viewer.phase_history_view.getImageItem()
        )
        
        frame_count = self.model.get_frame_count()
        frame_rate = self.model.get_frame_rate()
        mode = self.viewer.direction_combo_box.currentText()
        aperture_fraction = self.model.get_aperture_fraction()
        
        # Store original frame position to restore later
        try:
            original_frame = int(self.viewer.current_frame.text())
        except ValueError:
            original_frame = 0
        
        colormap = self.viewer.phase_history_view.get_color_map()
        
        # Create progress dialog
        progress = QProgressDialog("Preparing to export...", "Cancel", 0, frame_count+1, self.viewer)
        progress.show()
        progress.setValue(0)
        QApplication.processEvents()
        
        # First, prepare all frames and store them in memory
        all_frames = []
        
        for frame_num in range(frame_count + 1):  
            if progress.wasCanceled():
                break
            
            progress.setLabelText(f"Generating frame {frame_num}/{frame_count}...")
            QApplication.processEvents()
            
            # Calculate new ROI position/size
            geometry_translation = self.model.step_animation(
                fft_bounds,
                min(frame_num, frame_count-1),
                frame_count,
                mode,
                aperture_fraction,
                self.model.get_aperture_min(),
                self.model.get_aperture_max(),
                self.model.get_animation_direction()
            )
            
            # Apply to ROI
            k_space_roi = self.model.get_k_space_roi()
            k_space_roi.setPos(geometry_translation[0])
            k_space_roi.setSize(geometry_translation[1])
            
            # Update the filtered view using the same method as the working original
            self.k_space_roi_changed_controller(k_space_roi)
            
            # Update UI
            self.viewer.current_frame.setText(str(min(frame_num, frame_count-1)))
            QApplication.processEvents()
            
            # Capture both views
            k_space_img = self.viewer.phase_history_view.getImageItem().image
            filtered_img = self.viewer.filtered_view.getImageItem().image
            
            if k_space_img is None or filtered_img is None:
                continue
            
            # Process frames 
            import cv2
            import numpy as np
            
            # Determine sizes for the composite frame
            k_height, k_width = k_space_img.shape[:2]
            f_height, f_width = filtered_img.shape[:2]
            
            # Make both images the same height
            max_height = max(k_height, f_height)
            k_scale = max_height / k_height
            f_scale = max_height / f_height
            
            k_new_width = int(k_width * k_scale)
            f_new_width = int(f_width * f_scale)
            
            # Combined frame dimensions
            combined_width = k_new_width + f_new_width
            combined_height = max_height
            
            # Apply colormap to k-space image
            k_min, k_max = k_space_img.min(), k_space_img.max()
            if k_max > k_min:
                k_norm = (k_space_img - k_min) / (k_max - k_min)
                k_colored_rgba = colormap.map(k_norm, mode='byte')
                k_frame = cv2.cvtColor(k_colored_rgba[:, :, :3], cv2.COLOR_RGB2BGR)
            else:
                k_frame = np.zeros((k_height, k_width, 3), dtype=np.uint8)
            
            # Convert filtered image to 8-bit for video
            if filtered_img.dtype != np.uint8:
                f_min, f_max = filtered_img.min(), filtered_img.max()
                if f_max > f_min:
                    f_frame = ((filtered_img - f_min) / (f_max - f_min) * 255).astype(np.uint8)
                else:
                    f_frame = np.zeros_like(filtered_img, dtype=np.uint8)
            else:
                f_frame = filtered_img.copy()
            
            # Convert filtered image to BGR if it's grayscale
            if len(f_frame.shape) == 2:
                f_frame = cv2.cvtColor(f_frame, cv2.COLOR_GRAY2BGR)
            elif f_frame.shape[2] == 4:  # RGBA
                f_frame = cv2.cvtColor(f_frame, cv2.COLOR_RGBA2BGR)
            
            # Resize images to have the same height
            k_frame_resized = cv2.resize(k_frame, (k_new_width, max_height))
            f_frame_resized = cv2.resize(f_frame, (f_new_width, max_height))
            
            # Create a composite frame
            composite_frame = np.zeros((combined_height, combined_width, 3), dtype=np.uint8)
            composite_frame[:, :k_new_width] = k_frame_resized
            composite_frame[:, k_new_width:] = f_frame_resized
            
            # Add the ROI visualization to the k-space part
            roi_pos = k_space_roi.pos()
            roi_size = k_space_roi.size()

            # Scale the ROI coordinates to match the resized frame
            roi_x = int(roi_pos[0] * k_scale)
            roi_y = int(roi_pos[1] * k_scale)
            roi_w = int(roi_size[0] * k_scale)
            roi_h = int(roi_size[1] * k_scale)
            
            # Draw the ROI rectangle on the composite frame
            cv2.rectangle(
                composite_frame,
                (roi_x, roi_y),
                (roi_x + roi_w, roi_y + roi_h),
                (255, 255, 255),  # White color
                2  # Line thickness
            )
            
            # Add the annotation text
            if self.model.get_include_annotations():
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6  
                text = f"Frame: {frame_num}/{frame_count-1}"
                text_size = cv2.getTextSize(text, font, font_scale, 1)[0] 

                text_x = 10  
                text_y = combined_height - 10  

                cv2.rectangle(
                    composite_frame,
                    (text_x - 5, text_y - text_size[1] - 5),
                    (text_x + text_size[0] + 5, text_y + 5),
                    (0, 0, 0), 
                    -1 
                )

                cv2.putText(
                    composite_frame, 
                    text,
                    (text_x, text_y), 
                    font, 
                    font_scale,  
                    (255, 255, 255),
                    1, 
                    cv2.LINE_AA
                )

            # Store the frame
            if self.model.get_include_kspace():
                all_frames.append(composite_frame)
            else:
                all_frames.append(f_frame_resized)
            
            # Update progress
            progress.setValue(frame_num + 1)
        
        # Check if we have frames to write
        if not all_frames:
            QMessageBox.warning(self.viewer, "Export Error", "No frames were generated.")
            return
        
        # Get dimensions from the first frame
        height, width = all_frames[0].shape[:2]
        
        # Create video writer
        progress.setLabelText("Writing video file...")
        progress.setValue(0)
        progress.setMaximum(len(all_frames))
        QApplication.processEvents()
        
        try:
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(file_path, fourcc, frame_rate, (width, height))
            
            # Write all frames to video
            for i, frame in enumerate(all_frames):
                if progress.wasCanceled():
                    break
                video_writer.write(frame)
                progress.setValue(i + 1)
                QApplication.processEvents()
                
            # Close video writer
            video_writer.release()
            
        except Exception as e:
            QMessageBox.critical(self.viewer, "Export Error", f"An error occurred while writing the video: {str(e)}")
            return
        finally:
            # Restore original frame position
            self.viewer.current_frame.setText(str(original_frame))
            geometry_translation = self.model.step_animation(
                fft_bounds,
                original_frame,
                frame_count,
                mode,
                aperture_fraction,
                self.model.get_aperture_min(),
                self.model.get_aperture_max(),
                self.model.get_animation_direction()
            )
            k_space_roi = self.model.get_k_space_roi()
            k_space_roi.setPos(geometry_translation[0])
            k_space_roi.setSize(geometry_translation[1])
            self.k_space_roi_changed_controller(k_space_roi)
        
        # Show success message
        if not progress.wasCanceled():
            QMessageBox.information(
                self.viewer, 
                "Export Complete", 
                f"Animation exported to {file_path}"
            )
    
    def export_chip(self, chip_sicd: Optional['SICDType'] = None) -> None:
        """
        Export chip with updated SICD metadata.
        
        Initiates the export process for the current aperture-processed
        chip with updated SICD metadata.
        
        Parameters
        ----------
        chip_sicd : Optional[SICDType], optional
            SICD metadata for the chip (unused in current implementation)
        """
        if self.mitm_controller is None:
            return
        
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None:
            return
        
        self.export_service.export_chip(selected_widget, self.mitm_controller)

    # Helper methods
    def _get_current_frame_safely(self) -> int:
        """
        Safely get current frame number from UI.
        
        Attempts to parse the current frame number from the UI display,
        returning 0 if parsing fails or the field is not available.
        
        Returns
        -------
        int
            Current frame number, or 0 if unavailable/invalid
        """
        try:
            return int(self.viewer.current_frame.text())
        except (ValueError, AttributeError):
            return 0

    def _process_single_frame(self, frame: int) -> None:
        """
        Process a single animation frame.
        
        Updates the display to show the specified animation frame by
        calculating the appropriate ROI position and size, then updating
        the views.
        
        Parameters
        ----------
        frame : int
            Frame number to process (0-based)
        """
        if self.mitm_controller is None:
            return
        
        selected_widget = self.mitm_controller.get_current_widget()
        if selected_widget is None:
            return
        
        self.animation_service.process_frame(frame, selected_widget, self.mitm_controller)

    def process_frame(self, frame: int) -> None:
        """
        Process a frame - delegates to the single frame processor.
        
        Parameters
        ----------
        frame : int
            Frame number to process
        """
        return self._process_single_frame(frame)

    def animation_options_controller(self, enabled: bool) -> None:
        """
        Controls the availability of animation-related UI controls based
        on the current application state.
        
        Parameters
        ----------
        enabled : bool
            Whether animation controls should be enabled
        """
        self.animation_service.toggle_animation_controls(enabled)

    def update_meta_icon_display(self, updated_chip_sicd: 'SICDType') -> None:
        """
        Updates the metadata icon display with information from the
        provided SICD metadata object.
        
        Parameters
        ----------
        updated_chip_sicd : SICDType
            SICD metadata containing updated chip information
        """
        updated_meta_data = self.mitm_controller.model.get_metadata_from_sicd(updated_chip_sicd)
        self.viewer.aperture_meta_icon.display_metaicon(updated_meta_data)

    # AbstractApp interface implementation
    def set_mitm_controller(self, controller: Any) -> None:
        """
        Set the MITM controller reference.
        
        Establishes the connection to the main MITM controller and sets up
        signal connections for geometry handling.
        
        Parameters
        ----------
        controller : Any
            The main MITM controller instance
        """
        super().set_mitm_controller(controller)
        self.mitm_controller = controller
        
        # Connect to annotation controller geometry signals
        self.mitm_controller.annotation_controller.viewer.geometry_connect_signal.connect(
            self.connect_geometry
        )

    def get_name(self) -> str:
        """
        Get the application name.
        
        Returns the display name for this application component.
        
        Returns
        -------
        str
            The application name "Aperture Tool"
        """
        return "Aperture Tool"

    def get_dock_widget(self) -> ApertureViewer:
        """
        Get the main dock widget.
        
        Returns the primary UI widget for docking in the main application.
        
        Returns
        -------
        ApertureViewer
            The main viewer widget
        """
        return self.viewer

    def get_preferred_area(self) -> Qt.DockWidgetArea:
        """
        Get the preferred dock area.
        
        Returns the preferred location for docking this widget in the
        main application interface.
        
        Returns
        -------
        Qt.DockWidgetArea
            The preferred dock area from the viewer
        """
        return self.viewer.preferred_area()