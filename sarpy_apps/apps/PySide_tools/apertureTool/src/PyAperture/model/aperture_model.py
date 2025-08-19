import numpy as np
import copy
from typing import List, Tuple, Dict, Union, Optional, Any, Set, Callable, Literal, TYPE_CHECKING
from numpy.typing import NDArray

from sarpy.processing.sicd.subaperture import ApertureFilter, SICDTypeReader,fftshift, fft2_sicd, fft, FFTCalculator
from sarpy.io.complex.sicd import SICDWriter
from sarpy.utils.chip_sicd import create_chip
from sarpy.geometry.geometry_elements import Polygon
from sarpy.geometry.geocoords import wgs_84_norm, geodetic_to_ecf, ecf_to_geodetic
from sarpy.annotation.rcs import _get_polygon_bounds
from sarpy.geometry.point_projection import image_to_ground

import scipy.io
import warnings

from PySide6.QtGui import QColor

if TYPE_CHECKING:
    from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.services.validation_service \
        import ValidationService
    from sarpy.io.complex.sicd_elements.SICD import SICDType
    from PySide6.QtCore import QRectF

# Type aliases for clarity
AnimationDirection = Literal["forward", "backward"]
AnimationMode = Literal["Slow-Time", "Fast-Time", "Aperture-Percent", 
                       "Full-Range-Bandwidth", "Full-Azimuth-Bandwidth"]
WindowType = Literal["None", "Gaussian", "1/x^4", "Hamming", "Cosine on Pedestal"]


class ApertureModel:
    """
    Model class for aperture processing operations.
    
    This class handles all business logic and data management for the SAR
    Aperture Tool. It maintains processing state, coordinates with processing
    services, and provides validation for user inputs.
    
    The model follows the MVC pattern by separating business logic from
    the user interface, allowing for better testability and maintainability.
    
    Attributes
    ----------
    _aperture_filter : Optional[PolygonApertureFilter]
        The current aperture filter instance for processing
    _k_space_roi : Optional[Any]
        The k-space region of interest selection
    _aperture_roi : Optional[Any]
        The spatial domain region of interest selection
    _pause_flag : bool
        Flag indicating if animation is paused
    _animation_direction : AnimationDirection
        Direction of animation playback
    _include_kspace : bool
        Whether to include k-space in exports
    _include_annotations : bool
        Whether to include annotations in exports
    _deskew : bool
        Whether to apply deskewing during processing
    _deweighting : bool
        Whether to apply uniform weighting
    _frame_count : int
        Number of frames for animations
    _frame_rate : int
        Frame rate for animation playback
    _aperture_fraction : float
        Fraction of aperture to use in animations
    _aperture_min : float
        Minimum aperture percentage
    _aperture_max : float
        Maximum aperture percentage
    """

    def __init__(self) -> None:
        """
        Initialize the aperture model with default values.
        
        Sets up all internal state variables with sensible defaults for
        SAR aperture processing operations.
        """
        # Core data
        self._aperture_filter: Optional['PolygonApertureFilter'] = None
        self._k_space_roi: Optional[Any] = None
        self._aperture_roi: Optional[Any] = None
        
        # Animation state
        self._pause_flag: bool = False
        self._animation_direction: AnimationDirection = "forward"
        
        # Processing options
        self._include_kspace: bool = False
        self._include_annotations: bool = False
        self._deskew: bool = True
        self._deweighting: bool = False
        
        # Animation parameters
        self._frame_count: int = 7
        self._frame_rate: int = 5
        self._aperture_fraction: float = 0.25
        self._aperture_min: float = 0.1
        self._aperture_max: float = 1.0

    # Validation methods using service
    def ensure_valid_integer(self, value: str) -> int:
        """
        Validate and convert string input to valid integer.
        
        Parameters
        ----------
        value : str
            String representation of integer value
            
        Returns
        -------
        int
            Validated integer value
            
        Notes
        -----
        This method delegates to ValidationService for consistency
        across the application.
        """
        from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.services.validation_service \
            import ValidationService
        return ValidationService.ensure_valid_integer(value)

    def ensure_valid_percentage(self, value: str) -> float:
        """
        Validate and convert string input to valid percentage.
        
        Parameters
        ----------
        value : str
            String representation of percentage value
            
        Returns
        -------
        float
            Validated percentage value (0.0 to 1.0)
            
        Notes
        -----
        This method delegates to ValidationService for consistency
        across the application.
        """
        from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.services.validation_service \
            import ValidationService
        return ValidationService.ensure_valid_percentage(value)

    # Property setters and getters
    def set_frame_count(self, frame_count: int) -> None:
        """
        Set the number of frames for animation.
        
        Parameters
        ----------
        frame_count : int
            Number of animation frames (must be positive)
        """
        self._frame_count = max(1, frame_count)

    def get_frame_count(self) -> int:
        """
        Get the current frame count.
        
        Returns
        -------
        int
            Number of animation frames
        """
        return self._frame_count

    def set_frame_rate(self, frame_rate: int) -> None:
        """
        Set the animation frame rate.
        
        Parameters
        ----------
        frame_rate : int
            Frame rate in frames per second (must be positive)
        """
        self._frame_rate = max(1, frame_rate)

    def get_frame_rate(self) -> int:
        """
        Get the current frame rate.
        
        Returns
        -------
        int
            Frame rate in frames per second
        """
        return self._frame_rate

    def set_aperture_fraction(self, aperture_fraction: float) -> None:
        """
        Set the aperture fraction for animations.
        
        Parameters
        ----------
        aperture_fraction : float
            Fraction of total aperture to use (0.0 to 1.0)
        """
        self._aperture_fraction = max(0.0, min(1.0, aperture_fraction))

    def get_aperture_fraction(self) -> float:
        """
        Get the current aperture fraction.
        
        Returns
        -------
        float
            Aperture fraction (0.0 to 1.0)
        """
        return self._aperture_fraction

    def set_aperture_min(self, aperture_min: float) -> None:
        """
        Set the minimum aperture percentage.
        
        Parameters
        ----------
        aperture_min : float
            Minimum aperture percentage (0.0 to 1.0)
        """
        self._aperture_min = max(0.0, min(1.0, aperture_min))

    def get_aperture_min(self) -> float:
        """
        Get the minimum aperture percentage.
        
        Returns
        -------
        float
            Minimum aperture percentage
        """
        return self._aperture_min

    def set_aperture_max(self, aperture_max: float) -> None:
        """
        Set the maximum aperture percentage.
        
        Parameters
        ----------
        aperture_max : float
            Maximum aperture percentage (0.0 to 1.0)
        """
        self._aperture_max = max(0.0, min(1.0, aperture_max))

    def get_aperture_max(self) -> float:
        """
        Get the maximum aperture percentage.
        
        Returns
        -------
        float
            Maximum aperture percentage
        """
        return self._aperture_max

    def set_deskew(self, deskew: bool) -> None:
        """
        Set the deskewing option.
        
        Parameters
        ----------
        deskew : bool
            Whether to apply deskewing during processing
        """
        self._deskew = deskew
    
    def get_deskew(self) -> bool:
        """
        Get the current deskewing setting.
        
        Returns
        -------
        bool
            Whether deskewing is enabled
        """
        return self._deskew
    
    def set_deweighting(self, deweight: bool) -> None:
        """
        Set the uniform weighting (deweighting) option.
        
        Parameters
        ----------
        deweight : bool
            Whether to apply uniform weighting
        """
        self._deweighting = deweight
    
    def get_deweighting(self) -> bool:
        """
        Get the current deweighting setting.
        
        Returns
        -------
        bool
            Whether uniform weighting is enabled
        """
        return self._deweighting

    def set_aperture_roi(self, aperture_roi: Any) -> None:
        """
        Set the spatial domain region of interest.
        
        Parameters
        ----------
        aperture_roi : Any
            The aperture ROI object (typically a Qt graphics item)
        """
        self._aperture_roi = aperture_roi

    def check_weighting(self, sicd: 'SICDType') -> bool:
        """
        Check if deweighting can be applied based on SICD metadata.
        
        Examines the SICD metadata to determine if weighting functions
        are available for both row and column directions.
        
        Parameters
        ----------
        sicd : SICDType
            SICD metadata object to examine
            
        Returns
        -------
        bool
            True if deweighting can be applied, False otherwise
        """
        if sicd.Grid.Row.WgtFunct is None or sicd.Grid.Col.WgtFunct is None:
            return False
        else:
            return True

    def get_aperture_roi(self) -> Optional[Any]:
        """
        Get the current aperture ROI.
        
        Returns
        -------
        Optional[Any]
            The aperture ROI object or None if not set
        """
        return self._aperture_roi

    def set_include_kspace(self, include: bool) -> None:
        """
        Set whether to include k-space in exports.
        
        Parameters
        ----------
        include : bool
            Whether to include k-space visualization in exports
        """
        self._include_kspace = include

    def get_include_kspace(self) -> bool:
        """
        Get the k-space inclusion setting.
        
        Returns
        -------
        bool
            Whether k-space is included in exports
        """
        return self._include_kspace

    def set_include_annotations(self, include: bool) -> None:
        """
        Set whether to include annotations in exports.
        
        Parameters
        ----------
        include : bool
            Whether to include annotations in exports
        """
        self._include_annotations = include

    def get_include_annotations(self) -> bool:
        """
        Get the annotations inclusion setting.
        
        Returns
        -------
        bool
            Whether annotations are included in exports
        """
        return self._include_annotations

    def set_animation_direction(self, animation_direction: AnimationDirection) -> None:
        """
        Set the animation playback direction.
        
        Parameters
        ----------
        animation_direction : AnimationDirection
            Direction of animation playback ("forward" or "backward")
        """
        self._animation_direction = animation_direction

    def get_animation_direction(self) -> AnimationDirection:
        """
        Get the current animation direction.
        
        Returns
        -------
        AnimationDirection
            Current animation direction
        """
        return self._animation_direction

    def set_pause_flag(self, pause_flag: bool) -> None:
        """
        Set the animation pause state.
        
        Parameters
        ----------
        pause_flag : bool
            Whether animation is paused
        """
        self._pause_flag = pause_flag

    def get_pause_flag(self) -> bool:
        """
        Get the current pause state.
        
        Returns
        -------
        bool
            Whether animation is currently paused
        """
        return self._pause_flag

    def set_k_space_roi(self, k_space_roi: Any) -> None:
        """
        Set the k-space region of interest.
        
        Parameters
        ----------
        k_space_roi : Any
            The k-space ROI object
        """
        self._k_space_roi = k_space_roi

    def get_k_space_roi(self) -> Optional[Any]:
        """
        Get the current k-space ROI.
        
        Returns
        -------
        Optional[Any]
            The k-space ROI object or None if not set
        """
        return self._k_space_roi

    def get_aperture_filter(self) -> Optional['PolygonApertureFilter']:
        """
        Get the current aperture filter.
        
        Returns
        -------
        Optional[PolygonApertureFilter]
            The aperture filter instance or None if not created
        """
        return self._aperture_filter

    def set_aperture_filter(self, aperture_filter: 'PolygonApertureFilter') -> None:
        """
        Set the aperture filter instance.
        
        Parameters
        ----------
        aperture_filter : PolygonApertureFilter
            The aperture filter to use for processing
        """
        self._aperture_filter = aperture_filter

    # Core business logic methods
    def create_aperture_filter(
        self, 
        reader: Any, 
        dimension: int, 
        apply_deskew: bool, 
        apply_deweighting: bool
    ) -> 'PolygonApertureFilter':
        """
        Create and configure the aperture filter.
        
        Initializes a new PolygonApertureFilter with the specified processing
        parameters for SAR data processing.
        
        Parameters
        ----------
        reader : Any
            The SICD reader object containing SAR data
        dimension : int
            Processing dimension (0 or 1)
        apply_deskew : bool
            Whether to apply deskewing during processing
        apply_deweighting : bool
            Whether to apply uniform weighting
            
        Returns
        -------
        PolygonApertureFilter
            Configured aperture filter ready for processing
        """
        self._aperture_filter = PolygonApertureFilter(
            reader=reader.base_reader,
            dimension=dimension,
            apply_deskew=apply_deskew,
            apply_deweighting=apply_deweighting
        )
        return self._aperture_filter

    def configure_aperture_filter(self, selected_widget: Any, aperture_roi_polygon: Polygon) -> None:
            """
            Configure the aperture filter with spatial bounds and mask.
            
            Sets up the aperture filter with the correct spatial bounds and
            mask based on the selected region of interest.
            
            Parameters
            ----------
            selected_widget : Any
                The selected widget containing image data
            aperture_roi_polygon : Polygon
                Polygon defining the aperture region of interest
                
            Raises
            ------
            ValueError
                If aperture filter has not been created before configuration
            """
            if self._aperture_filter is None:
                raise ValueError("Aperture filter must be created before configuration")
            
            # Calculate spatial bounds
            spatial_bounds = self._calculate_spatial_bounds_from_roi(
                self.get_aperture_roi(), selected_widget
            )
            
            # Get polygon bounds and mask
            row_bounds, col_bounds, mask = _get_polygon_bounds(
                aperture_roi_polygon, 
                selected_widget.reader.get_data_size_as_tuple()[0]
            )

            # Configure the filter
            self._aperture_filter.set_sub_image_bounds(
                (spatial_bounds['y'], spatial_bounds['y'] + spatial_bounds['height']),
                (spatial_bounds['x'], spatial_bounds['x'] + spatial_bounds['width'])
            )
            
            self._aperture_filter.set_raw_mask(
                mask[0:spatial_bounds['height'], 0:spatial_bounds['width']]
            )

    def form_k_space_image(
        self, 
        selected_widget: Any, 
        reader: Any, 
        aperture_roi: Any, 
        aperture_roi_polygon: Polygon
    ) -> NDArray[np.floating]:
        """
        Form k-space image from aperture data.
        
        Processes the selected aperture region to generate the k-space
        (phase history) representation for visualization and analysis.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the image data
        reader : Any
            SICD reader for accessing metadata
        aperture_roi : Any
            Spatial domain region of interest
        aperture_roi_polygon : Polygon
            Polygon defining the processing region
            
        Returns
        -------
        NDArray[np.floating]
            Processed k-space image ready for display
        """
        # Validate SICD metadata
        the_sicd = reader.get_sicd()
        self._validate_and_fix_sicd_metadata(the_sicd)
        
        # Determine processing parameters
        dimension, deweighting = self._determine_processing_parameters(the_sicd)
        
        # Create and configure aperture filter using user settings
        self.create_aperture_filter(reader, dimension, self.get_deskew(), self.get_deweighting())
        # 
        self.configure_aperture_filter(selected_widget, aperture_roi_polygon)
        
        # Return processed k-space image
        return selected_widget.remap_function(self._aperture_filter.normalized_phase_history)

    def form_filtered_image(
        self, 
        selected_widget: Any, 
        k_space_view_widget: Any, 
        k_space_roi: Any
    ) -> Optional[NDArray[np.floating]]:
        """
        Form filtered image from k-space selection.
        
        Applies inverse FFT to the selected k-space region to generate
        the filtered spatial domain image.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the original image data
        k_space_view_widget : Any
            Widget displaying the k-space data
        k_space_roi : Any
            Region of interest in k-space
            
        Returns
        -------
        Optional[NDArray[np.floating]]
            Filtered image data or None if no aperture filter exists
        """
        if self._aperture_filter is None:
            return None
        
        # Calculate k-space bounds
        phase_aperture_rect = k_space_view_widget.imageItem.mapFromScene(
            k_space_roi.sceneBoundingRect()
        ).boundingRect()

        x = int(phase_aperture_rect.x())
        y = int(phase_aperture_rect.y())
        width = int(phase_aperture_rect.width())
        height = int(phase_aperture_rect.height())

        # Apply k-space selection and return filtered image
        filtered_data = self._aperture_filter[y:y+height, x:x+width]
        return selected_widget.remap_function(filtered_data)

    def get_fft_image_bounds(self, image_reader: Any, image_item: Any) -> List[int]:
        """
        Calculate FFT image bounds based on SICD metadata.
        
        Determines the valid region within the FFT image that excludes
        spectral leakage areas based on impulse response bandwidth.
        
        Parameters
        ----------
        image_reader : Any
            Reader containing SICD metadata
        image_item : Any
            Image item with shape information
            
        Returns
        -------
        List[int]
            Bounds as [y_start, x_start, y_end, x_end]
        """
        meta_data = image_reader.get_sicd()
        
        row_ratio = meta_data.Grid.Row.ImpRespBW * meta_data.Grid.Row.SS
        col_ratio = meta_data.Grid.Col.ImpRespBW * meta_data.Grid.Col.SS

        full_n_rows = image_item.image.shape[0]
        full_n_cols = image_item.image.shape[1]

        full_im_y_start = int(full_n_rows * (1 - row_ratio) / 2)
        full_im_y_end = full_n_rows - full_im_y_start

        full_im_x_start = int(full_n_cols * (1 - col_ratio) / 2)
        full_im_x_end = full_n_cols - full_im_x_start

        return [full_im_y_start, full_im_x_start, full_im_y_end, full_im_x_end]

    def step_animation(
        self, 
        fft_bounds: List[int], 
        current_frame: int, 
        total_frames: int, 
        mode: AnimationMode, 
        aperture_fraction: float = 0.25, 
        min_aperture_percent: float = 0.01, 
        max_aperture_percent: float = 1.0, 
        direction: AnimationDirection = "forward"
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate animation step parameters for ROI positioning.
        
        Computes the position and size for the k-space ROI at a specific
        animation frame based on the selected animation mode.
        
        Parameters
        ----------
        fft_bounds : List[int]
            FFT image bounds [y_start, x_start, y_end, x_end]
        current_frame : int
            Current frame number (0-based)
        total_frames : int
            Total number of frames in animation
        mode : AnimationMode
            Type of animation to perform
        aperture_fraction : float, optional
            Fraction of aperture to use, by default 0.25
        min_aperture_percent : float, optional
            Minimum aperture percentage, by default 0.01
        max_aperture_percent : float, optional
            Maximum aperture percentage, by default 1.0
        direction : AnimationDirection, optional
            Animation direction, by default "forward"
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position [x, y] and size [width, height] for the ROI
        """
        # Ensure current_frame is within bounds
        current_frame = max(0, min(current_frame, total_frames - 1))
        
        # Calculate animation parameters based on mode
        animation_calculator = AnimationCalculator(fft_bounds)
        return animation_calculator.calculate_step(
            current_frame, total_frames, mode, aperture_fraction,
            min_aperture_percent, max_aperture_percent, direction
        )

    def apply_window_function(self, window_type: WindowType) -> None:
        """
        Apply window function to aperture filter data.
        
        Applies the specified windowing function to the aperture data
        to reduce sidelobe artifacts in the processed image.
        
        Parameters
        ----------
        window_type : WindowType
            Type of window function to apply
        """
        if self._aperture_filter is None:
            print("No aperture filter available")
            return
        
        self._aperture_filter.apply_window_function(window_type)

    def update_chip_sub_aperture_sicd(self, selected_widget: Any) -> 'SICDType':
        """
        Update chip SICD metadata for sub-aperture processing.
        
        Creates updated SICD metadata that reflects the spatial and
        spectral subsetting performed during aperture processing.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the original image data
            
        Returns
        -------
        SICDType
            Updated SICD metadata for the processed chip
        """
        if not self._validate_export_requirements():
            return selected_widget.reader.get_sicds_as_tuple()[0]
        
        sicd_processor = SICDProcessor()
        return sicd_processor.update_chip_sub_aperture_sicd(
            selected_widget, self.get_aperture_roi(), self.get_k_space_roi(),
            self.get_aperture_filter(), self.get_aperture_fraction()
        )

    # Private helper methods
    def _validate_and_fix_sicd_metadata(self, the_sicd: 'SICDType') -> None:
        """
        Validate and fix SICD metadata for processing.
        
        Ensures that required metadata fields are populated with
        default values if they are missing.
        
        Parameters
        ----------
        the_sicd : SICDType
            SICD metadata object to validate and fix
        """
        if the_sicd.Grid.Row.DeltaKCOAPoly is None or the_sicd.Grid.Col.DeltaKCOAPoly is None:
            print('DeltaKCOAPolys not populated, will be populated as [[0]] for processing')
            if the_sicd.Grid.Row.DeltaKCOAPoly is None:
                the_sicd.Grid.Row.DeltaKCOAPoly = [[0, ], ]
            if the_sicd.Grid.Col.DeltaKCOAPoly is None:
                the_sicd.Grid.Col.DeltaKCOAPoly = [[0, ], ]

    def _determine_processing_parameters(self, the_sicd: 'SICDType') -> Tuple[int, bool]:
        """
        Determine processing parameters from SICD metadata.
        
        Analyzes SICD metadata to determine the appropriate processing
        dimension and availability of deweighting functions.
        
        Parameters
        ----------
        the_sicd : SICDType
            SICD metadata object to analyze
            
        Returns
        -------
        Tuple[int, bool]
            Processing dimension and deweighting availability
        """
        row_delta_kcoa = the_sicd.Grid.Row.DeltaKCOAPoly.get_array()
        dimension = 0 if not (row_delta_kcoa.size == 1 and row_delta_kcoa[0, 0] == 0) else 1
        
        # Check if deweighting is available (but don't auto-enable it)
        deweighting_available = (the_sicd.Grid.Row.WgtFunct is not None and 
                            the_sicd.Grid.Col.WgtFunct is not None)
        
        return dimension, deweighting_available

    def _calculate_spatial_bounds_from_roi(
        self, 
        aperture_roi: Any, 
        selected_widget: Any
    ) -> Dict[str, int]:
        """
        Calculate spatial bounds from aperture ROI.
        
        Converts the ROI selection from screen coordinates to full-resolution
        image coordinates for processing.
        
        Parameters
        ----------
        aperture_roi : Any
            Region of interest in the aperture domain
        selected_widget : Any
            Widget containing coordinate transformation information
            
        Returns
        -------
        Dict[str, int]
            Spatial bounds with keys 'x', 'y', 'width', 'height'
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

    def _validate_export_requirements(self) -> bool:
        """
        Validate that all required data is available for export.
        
        Checks that aperture ROI, k-space ROI, and aperture filter
        are all properly configured before export operations.
        
        Returns
        -------
        bool
            True if all requirements are met, False otherwise
        """
        return (self.get_aperture_roi() is not None and 
                self.get_k_space_roi() is not None and
                self.get_aperture_filter() is not None)


class AnimationCalculator:
    """
    Helper class for animation calculations.
    
    This class handles the mathematical calculations required for different
    types of aperture animations, including position and size calculations
    for ROI movement through k-space.
    
    Attributes
    ----------
    x_min : int
        Minimum x coordinate of the valid k-space region
    x_max : int
        Maximum x coordinate of the valid k-space region
    y_min : int
        Minimum y coordinate of the valid k-space region
    y_max : int
        Maximum y coordinate of the valid k-space region
    full_x_aperture : int
        Full width of the k-space aperture
    full_y_aperture : int
        Full height of the k-space aperture
    x_center : float
        Center x coordinate of the k-space region
    y_center : float
        Center y coordinate of the k-space region
    """
    
    def __init__(self, fft_bounds: List[int]) -> None:
        """
        Initialize the animation calculator.
        
        Parameters
        ----------
        fft_bounds : List[int]
            FFT image bounds as [y_start, x_start, y_end, x_end]
        """
        self.x_min: int = fft_bounds[1]
        self.x_max: int = fft_bounds[3]
        self.y_min: int = fft_bounds[0]
        self.y_max: int = fft_bounds[2]
        self.full_x_aperture: int = self.x_max - self.x_min
        self.full_y_aperture: int = self.y_max - self.y_min
        self.x_center: float = (self.x_min + self.x_max) / 2
        self.y_center: float = (self.y_min + self.y_max) / 2

    def calculate_step(
        self, 
        current_frame: int, 
        total_frames: int, 
        mode: AnimationMode, 
        aperture_fraction: float,
        min_aperture_percent: float, 
        max_aperture_percent: float, 
        direction: AnimationDirection
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate animation step based on mode and parameters.
        
        Determines the ROI position and size for a specific frame
        based on the animation mode and direction.
        
        Parameters
        ----------
        current_frame : int
            Current frame number
        total_frames : int
            Total number of frames
        mode : AnimationMode
            Type of animation to perform
        aperture_fraction : float
            Fraction of aperture to use
        min_aperture_percent : float
            Minimum aperture percentage
        max_aperture_percent : float
            Maximum aperture percentage
        direction : AnimationDirection
            Animation direction
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position [x, y] and size [width, height]
        """
        # Reverse frame index if going backward
        frame_index = self._get_frame_index(current_frame, total_frames, direction)
        
        if mode == "Slow-Time":
            return self._calculate_slow_time_step(frame_index, total_frames, aperture_fraction)
        elif mode == "Fast-Time":
            return self._calculate_fast_time_step(frame_index, total_frames, aperture_fraction)
        elif mode == "Aperture-Percent":
            return self._calculate_aperture_percent_step(
                frame_index, total_frames, min_aperture_percent, max_aperture_percent
            )
        elif mode == "Full-Range-Bandwidth":
            return self._calculate_range_bandwidth_step(
                frame_index, total_frames, min_aperture_percent, max_aperture_percent
            )
        elif mode == "Full-Azimuth-Bandwidth":
            return self._calculate_azimuth_bandwidth_step(
                frame_index, total_frames, min_aperture_percent, max_aperture_percent
            )
        else:
            # Default fallback
            return [self.x_min, self.y_min], [self.full_x_aperture, self.full_y_aperture]

    def configure_aperture_filter(self, selected_widget: Any, aperture_roi_polygon: Polygon) -> None:
        """
        Configure the aperture filter with spatial bounds and mask.
        
        Sets up the aperture filter with the correct spatial bounds and
        mask based on the selected region of interest.
        
        Parameters
        ----------
        selected_widget : Any
            The selected widget containing image data
        aperture_roi_polygon : Polygon
            Polygon defining the aperture region of interest
            
        Raises
        ------
        ValueError
            If aperture filter has not been created before configuration
        """
        if self._aperture_filter is None:
            raise ValueError("Aperture filter must be created before configuration")
        
        # Calculate spatial bounds
        spatial_bounds = self._calculate_spatial_bounds_from_roi(
            self.get_aperture_roi(), selected_widget
        )
        
        # Get polygon bounds and mask
        row_bounds, col_bounds, mask = _get_polygon_bounds(
            aperture_roi_polygon, 
            selected_widget.reader.get_data_size_as_tuple()[0]
        )

        # Configure the filter
        self._aperture_filter.set_sub_image_bounds(
            (spatial_bounds['y'], spatial_bounds['y'] + spatial_bounds['height']),
            (spatial_bounds['x'], spatial_bounds['x'] + spatial_bounds['width'])
        )
        
        self._aperture_filter.set_raw_mask(
            mask[0:spatial_bounds['height'], 0:spatial_bounds['width']]
        )

    def form_k_space_image(
        self, 
        selected_widget: Any, 
        reader: Any, 
        aperture_roi: Any, 
        aperture_roi_polygon: Polygon
    ) -> NDArray[np.floating]:
        """
        Form k-space image from aperture data.
        
        Processes the selected aperture region to generate the k-space
        (phase history) representation for visualization and analysis.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the image data
        reader : Any
            SICD reader for accessing metadata
        aperture_roi : Any
            Spatial domain region of interest
        aperture_roi_polygon : Polygon
            Polygon defining the processing region
            
        Returns
        -------
        NDArray[np.floating]
            Processed k-space image ready for display
        """
        # Validate SICD metadata
        the_sicd = reader.get_sicd()
        self._validate_and_fix_sicd_metadata(the_sicd)
        
        # Determine processing parameters
        dimension, deweighting = self._determine_processing_parameters(the_sicd)
        
        # Create and configure aperture filter using user settings
        self.create_aperture_filter(reader, dimension, self.get_deskew(), self.get_deweighting())
        self.configure_aperture_filter(selected_widget, aperture_roi_polygon)
        
        # Return processed k-space image
        return selected_widget.remap_function(self._aperture_filter.normalized_phase_history)

    def form_filtered_image(
        self, 
        selected_widget: Any, 
        k_space_view_widget: Any, 
        k_space_roi: Any
    ) -> Optional[NDArray[np.floating]]:
        """
        Form filtered image from k-space selection.
        
        Applies inverse FFT to the selected k-space region to generate
        the filtered spatial domain image.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the original image data
        k_space_view_widget : Any
            Widget displaying the k-space data
        k_space_roi : Any
            Region of interest in k-space
            
        Returns
        -------
        Optional[NDArray[np.floating]]
            Filtered image data or None if no aperture filter exists
        """
        if self._aperture_filter is None:
            return None
        
        # Calculate k-space bounds
        phase_aperture_rect = k_space_view_widget.imageItem.mapFromScene(
            k_space_roi.sceneBoundingRect()
        ).boundingRect()

        x = int(phase_aperture_rect.x())
        y = int(phase_aperture_rect.y())
        width = int(phase_aperture_rect.width())
        height = int(phase_aperture_rect.height())

        # Apply k-space selection and return filtered image
        filtered_data = self._aperture_filter[y:y+height, x:x+width]
        return selected_widget.remap_function(filtered_data)

    def get_fft_image_bounds(self, image_reader: Any, image_item: Any) -> List[int]:
        """
        Calculate FFT image bounds based on SICD metadata.
        
        Determines the valid region within the FFT image that excludes
        spectral leakage areas based on impulse response bandwidth.
        
        Parameters
        ----------
        image_reader : Any
            Reader containing SICD metadata
        image_item : Any
            Image item with shape information
            
        Returns
        -------
        List[int]
            Bounds as [y_start, x_start, y_end, x_end]
        """
        meta_data = image_reader.get_sicd()
        
        row_ratio = meta_data.Grid.Row.ImpRespBW * meta_data.Grid.Row.SS
        col_ratio = meta_data.Grid.Col.ImpRespBW * meta_data.Grid.Col.SS

        full_n_rows = image_item.image.shape[0]
        full_n_cols = image_item.image.shape[1]

        full_im_y_start = int(full_n_rows * (1 - row_ratio) / 2)
        full_im_y_end = full_n_rows - full_im_y_start

        full_im_x_start = int(full_n_cols * (1 - col_ratio) / 2)
        full_im_x_end = full_n_cols - full_im_x_start

        return [full_im_y_start, full_im_x_start, full_im_y_end, full_im_x_end]

    def step_animation(
        self, 
        fft_bounds: List[int], 
        current_frame: int, 
        total_frames: int, 
        mode: AnimationMode, 
        aperture_fraction: float = 0.25, 
        min_aperture_percent: float = 0.01, 
        max_aperture_percent: float = 1.0, 
        direction: AnimationDirection = "forward"
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate animation step parameters for ROI positioning.
        
        Computes the position and size for the k-space ROI at a specific
        animation frame based on the selected animation mode.
        
        Parameters
        ----------
        fft_bounds : List[int]
            FFT image bounds [y_start, x_start, y_end, x_end]
        current_frame : int
            Current frame number (0-based)
        total_frames : int
            Total number of frames in animation
        mode : AnimationMode
            Type of animation to perform
        aperture_fraction : float, optional
            Fraction of aperture to use, by default 0.25
        min_aperture_percent : float, optional
            Minimum aperture percentage, by default 0.01
        max_aperture_percent : float, optional
            Maximum aperture percentage, by default 1.0
        direction : AnimationDirection, optional
            Animation direction, by default "forward"
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position [x, y] and size [width, height] for the ROI
        """
        # Ensure current_frame is within bounds
        current_frame = max(0, min(current_frame, total_frames - 1))
        
        # Calculate animation parameters based on mode
        animation_calculator = AnimationCalculator(fft_bounds)
        return animation_calculator.calculate_step(
            current_frame, total_frames, mode, aperture_fraction,
            min_aperture_percent, max_aperture_percent, direction
        )

    def apply_window_function(self, window_type: WindowType) -> None:
        """
        Apply window function to aperture filter data.
        
        Applies the specified windowing function to the aperture data
        to reduce sidelobe artifacts in the processed image.
        
        Parameters
        ----------
        window_type : WindowType
            Type of window function to apply
        """
        if self._aperture_filter is None:
            print("No aperture filter available")
            return
        
        self._aperture_filter.apply_window_function(window_type)

    def update_chip_sub_aperture_sicd(self, selected_widget: Any) -> 'SICDType':
        """
        Update chip SICD metadata for sub-aperture processing.
        
        Creates updated SICD metadata that reflects the spatial and
        spectral subsetting performed during aperture processing.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the original image data
            
        Returns
        -------
        SICDType
            Updated SICD metadata for the processed chip
        """
        if not self._validate_export_requirements():
            return selected_widget.reader.get_sicds_as_tuple()[0]
        
        sicd_processor = SICDProcessor()
        return sicd_processor.update_chip_sub_aperture_sicd(
            selected_widget, self.get_aperture_roi(), self.get_k_space_roi(),
            self.get_aperture_filter(), self.get_aperture_fraction()
        )

    # Private helper methods
    def _validate_and_fix_sicd_metadata(self, the_sicd: 'SICDType') -> None:
        """
        Validate and fix SICD metadata for processing.
        
        Ensures that required metadata fields are populated with
        default values if they are missing.
        
        Parameters
        ----------
        the_sicd : SICDType
            SICD metadata object to validate and fix
        """
        if the_sicd.Grid.Row.DeltaKCOAPoly is None or the_sicd.Grid.Col.DeltaKCOAPoly is None:
            print('DeltaKCOAPolys not populated, will be populated as [[0]] for processing')
            if the_sicd.Grid.Row.DeltaKCOAPoly is None:
                the_sicd.Grid.Row.DeltaKCOAPoly = [[0, ], ]
            if the_sicd.Grid.Col.DeltaKCOAPoly is None:
                the_sicd.Grid.Col.DeltaKCOAPoly = [[0, ], ]

    def _determine_processing_parameters(self, the_sicd: 'SICDType') -> Tuple[int, bool]:
        """
        Determine processing parameters from SICD metadata.
        
        Analyzes SICD metadata to determine the appropriate processing
        dimension and availability of deweighting functions.
        
        Parameters
        ----------
        the_sicd : SICDType
            SICD metadata object to analyze
            
        Returns
        -------
        Tuple[int, bool]
            Processing dimension and deweighting availability
        """
        row_delta_kcoa = the_sicd.Grid.Row.DeltaKCOAPoly.get_array()
        dimension = 0 if not (row_delta_kcoa.size == 1 and row_delta_kcoa[0, 0] == 0) else 1
        
        # Check if deweighting is available (but don't auto-enable it)
        deweighting_available = (the_sicd.Grid.Row.WgtFunct is not None and 
                               the_sicd.Grid.Col.WgtFunct is not None)
        
        return dimension, deweighting_available

    def _calculate_spatial_bounds_from_roi(
        self, 
        aperture_roi: Any, 
        selected_widget: Any
    ) -> Dict[str, int]:
        """
        Calculate spatial bounds from aperture ROI.
        
        Converts the ROI selection from screen coordinates to full-resolution
        image coordinates for processing.
        
        Parameters
        ----------
        aperture_roi : Any
            Region of interest in the aperture domain
        selected_widget : Any
            Widget containing coordinate transformation information
            
        Returns
        -------
        Dict[str, int]
            Spatial bounds with keys 'x', 'y', 'width', 'height'
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

    def _validate_export_requirements(self) -> bool:
        """
        Validate that all required data is available for export.
        
        Checks that aperture ROI, k-space ROI, and aperture filter
        are all properly configured before export operations.
        
        Returns
        -------
        bool
            True if all requirements are met, False otherwise
        """
        return (self.get_aperture_roi() is not None and 
                self.get_k_space_roi() is not None and
                self.get_aperture_filter() is not None)


class AnimationCalculator:
    """
    Helper class for animation calculations.
    
    This class handles the mathematical calculations required for different
    types of aperture animations, including position and size calculations
    for ROI movement through k-space.
    
    Attributes
    ----------
    x_min : int
        Minimum x coordinate of the valid k-space region
    x_max : int
        Maximum x coordinate of the valid k-space region
    y_min : int
        Minimum y coordinate of the valid k-space region
    y_max : int
        Maximum y coordinate of the valid k-space region
    full_x_aperture : int
        Full width of the k-space aperture
    full_y_aperture : int
        Full height of the k-space aperture
    x_center : float
        Center x coordinate of the k-space region
    y_center : float
        Center y coordinate of the k-space region
    """
    
    def __init__(self, fft_bounds: List[int]) -> None:
        """
        Initialize the animation calculator.
        
        Parameters
        ----------
        fft_bounds : List[int]
            FFT image bounds as [y_start, x_start, y_end, x_end]
        """
        self.x_min: int = fft_bounds[1]
        self.x_max: int = fft_bounds[3]
        self.y_min: int = fft_bounds[0]
        self.y_max: int = fft_bounds[2]
        self.full_x_aperture: int = self.x_max - self.x_min
        self.full_y_aperture: int = self.y_max - self.y_min
        self.x_center: float = (self.x_min + self.x_max) / 2
        self.y_center: float = (self.y_min + self.y_max) / 2

    def calculate_step(
        self, 
        current_frame: int, 
        total_frames: int, 
        mode: AnimationMode, 
        aperture_fraction: float,
        min_aperture_percent: float, 
        max_aperture_percent: float, 
        direction: AnimationDirection
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate animation step based on mode and parameters.
        
        Determines the ROI position and size for a specific frame
        based on the animation mode and direction.
        
        Parameters
        ----------
        current_frame : int
            Current frame number
        total_frames : int
            Total number of frames
        mode : AnimationMode
            Type of animation to perform
        aperture_fraction : float
            Fraction of aperture to use
        min_aperture_percent : float
            Minimum aperture percentage
        max_aperture_percent : float
            Maximum aperture percentage
        direction : AnimationDirection
            Animation direction
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position [x, y] and size [width, height]
        """
        # Reverse frame index if going backward
        frame_index = self._get_frame_index(current_frame, total_frames, direction)
        
        if mode == "Slow-Time":
            return self._calculate_slow_time_step(frame_index, total_frames, aperture_fraction)
        elif mode == "Fast-Time":
            return self._calculate_fast_time_step(frame_index, total_frames, aperture_fraction)
        elif mode == "Aperture-Percent":
            return self._calculate_aperture_percent_step(
                frame_index, total_frames, min_aperture_percent, max_aperture_percent
            )
        elif mode == "Full-Range-Bandwidth":
            return self._calculate_range_bandwidth_step(
                frame_index, total_frames, min_aperture_percent, max_aperture_percent
            )
        elif mode == "Full-Azimuth-Bandwidth":
            return self._calculate_azimuth_bandwidth_step(
                frame_index, total_frames, min_aperture_percent, max_aperture_percent
            )
        else:
            # Default fallback
            return [self.x_min, self.y_min], [self.full_x_aperture, self.full_y_aperture]

    def _get_frame_index(
        self, 
        current_frame: int, 
        total_frames: int, 
        direction: AnimationDirection
    ) -> int:
        """
        Get the correct frame index based on direction.
        
        Parameters
        ----------
        current_frame : int
            Current frame number
        total_frames : int
            Total number of frames
        direction : AnimationDirection
            Animation direction
            
        Returns
        -------
        int
            Adjusted frame index
        """
        if direction == "backward":
            frame_index = total_frames - 1 - current_frame
        else:
            frame_index = current_frame
        return max(0, min(frame_index, total_frames - 1))

    def _calculate_slow_time_step(
        self, 
        frame_index: int, 
        total_frames: int, 
        aperture_fraction: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate step for slow-time (cross-range) movement.
        
        Parameters
        ----------
        frame_index : int
            Current frame index
        total_frames : int
            Total number of frames
        aperture_fraction : float
            Fraction of aperture to use
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position and size
        """
        aperture_width = self.full_x_aperture * aperture_fraction
        
        if total_frames > 1:
            start_positions = np.linspace(self.x_min, self.x_max - aperture_width, total_frames)
        else:
            start_positions = np.array([self.x_min])
            
        x_start = start_positions[frame_index]
        new_pos = [x_start, self.y_min]
        new_size = [aperture_width, self.full_y_aperture]
        
        return new_pos, new_size

    def _calculate_fast_time_step(
        self, 
        frame_index: int, 
        total_frames: int, 
        aperture_fraction: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate step for fast-time (range) movement.
        
        Parameters
        ----------
        frame_index : int
            Current frame index
        total_frames : int
            Total number of frames
        aperture_fraction : float
            Fraction of aperture to use
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position and size
        """
        aperture_height = self.full_y_aperture * aperture_fraction
        
        if total_frames > 1:
            start_positions = np.linspace(self.y_min, self.y_max - aperture_height, total_frames)
            start_positions = np.flip(start_positions)  # Invert for top-to-bottom
        else:
            start_positions = np.array([self.y_min])
            
        y_start = start_positions[frame_index]
        new_pos = [self.x_min, y_start]
        new_size = [self.full_x_aperture, aperture_height]
        
        return new_pos, new_size

    def _calculate_aperture_percent_step(
        self, 
        frame_index: int, 
        total_frames: int, 
        min_aperture_percent: float, 
        max_aperture_percent: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate step for aperture percentage change.
        
        Parameters
        ----------
        frame_index : int
            Current frame index
        total_frames : int
            Total number of frames
        min_aperture_percent : float
            Minimum aperture percentage
        max_aperture_percent : float
            Maximum aperture percentage
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position and size
        """
        max_aperture_percent = min(1.0, max_aperture_percent)
        min_aperture_percent = max(0.0, min_aperture_percent)
        
        max_x_width = 0.5 * self.full_x_aperture * max_aperture_percent
        max_y_width = 0.5 * self.full_y_aperture * max_aperture_percent
        min_x_width = 0.5 * self.full_x_aperture * min_aperture_percent
        min_y_width = 0.5 * self.full_y_aperture * min_aperture_percent
        
        if total_frames > 1:
            x_widths = np.linspace(max_x_width, min_x_width, total_frames)
            y_widths = np.linspace(max_y_width, min_y_width, total_frames)
        else:
            x_widths = np.array([max_x_width])
            y_widths = np.array([max_y_width])
        
        current_x_width = x_widths[frame_index]
        current_y_width = y_widths[frame_index]
        
        new_pos = [
            max(self.x_min, min(self.x_center - current_x_width, self.x_max - 2*current_x_width)), 
            max(self.y_min, min(self.y_center - current_y_width, self.y_max - 2*current_y_width))
        ]
        new_size = [
            min(2 * current_x_width, self.x_max - new_pos[0]),
            min(2 * current_y_width, self.y_max - new_pos[1])
        ]
        
        return new_pos, new_size

    def _calculate_range_bandwidth_step(
        self, 
        frame_index: int, 
        total_frames: int,
        min_aperture_percent: float, 
        max_aperture_percent: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate step for range bandwidth variation.
        
        Parameters
        ----------
        frame_index : int
            Current frame index
        total_frames : int
            Total number of frames
        min_aperture_percent : float
            Minimum aperture percentage
        max_aperture_percent : float
            Maximum aperture percentage
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position and size
        """
        max_aperture_percent = min(1.0, max_aperture_percent)
        min_aperture_percent = max(0.0, min_aperture_percent)
        
        max_y_width = 0.5 * self.full_y_aperture * max_aperture_percent
        min_y_width = 0.5 * self.full_y_aperture * min_aperture_percent
        
        if total_frames > 1:
            y_widths = np.linspace(max_y_width, min_y_width, total_frames)
        else:
            y_widths = np.array([max_y_width])
            
        current_y_width = y_widths[frame_index]
        
        new_pos = [
            self.x_min, 
            max(self.y_min, min(self.y_center - current_y_width, self.y_max - 2*current_y_width))
        ]
        new_size = [
            self.full_x_aperture,
            min(2 * current_y_width, self.y_max - new_pos[1])
        ]
        
        return new_pos, new_size

    def _calculate_azimuth_bandwidth_step(
        self, 
        frame_index: int, 
        total_frames: int,
        min_aperture_percent: float, 
        max_aperture_percent: float
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate step for azimuth bandwidth variation.
        
        Parameters
        ----------
        frame_index : int
            Current frame index
        total_frames : int
            Total number of frames
        min_aperture_percent : float
            Minimum aperture percentage
        max_aperture_percent : float
            Maximum aperture percentage
            
        Returns
        -------
        Tuple[List[float], List[float]]
            New position and size
        """
        max_aperture_percent = min(1.0, max_aperture_percent)
        min_aperture_percent = max(0.0, min_aperture_percent)
        
        max_x_width = 0.5 * self.full_x_aperture * max_aperture_percent
        min_x_width = 0.5 * self.full_x_aperture * min_aperture_percent
        
        if total_frames > 1:
            x_widths = np.linspace(max_x_width, min_x_width, total_frames)
        else:
            x_widths = np.array([max_x_width])
            
        current_x_width = x_widths[frame_index]
        
        new_pos = [
            max(self.x_min, min(self.x_center - current_x_width, self.x_max - 2*current_x_width)), 
            self.y_min
        ]
        new_size = [
            min(2 * current_x_width, self.x_max - new_pos[0]),
            self.full_y_aperture
        ]
        
        return new_pos, new_size


class PolygonApertureFilter(ApertureFilter):
    """
    Extension of ApertureFilter with built-in masking and windowing capabilities.
    
    This class extends the basic ApertureFilter to provide masking capabilities
    for both raw complex image data (before FFT) and normalized phase history
    (after FFT). It also supports various windowing functions to reduce sidelobes
    and improve image quality.
    
    The filter supports two types of masks:
    1. Raw mask: Applied to complex image data before FFT transformation
    2. K-space mask: Applied to normalized phase history after FFT
    
    Additionally, it provides several windowing functions:
    - Gaussian: Smooth tapering with good sidelobe suppression
    - 1/x^4: Polynomial window with strong sidelobe reduction
    - Hamming: Classic raised cosine window
    - Cosine on Pedestal: Adjustable pedestal height for controlled tapering
    
    Attributes
    ----------
    _raw_mask : Optional[NDArray[np.floating]]
        Mask applied to raw complex data before FFT
    _k_space_mask : Optional[NDArray[np.floating]]
        Mask applied to k-space data after FFT
    _original_image_data : Optional[NDArray[np.complexfloating]]
        Original complex image data before masking and windowing
    _window_type : Optional[WindowType]
        Type of windowing function currently applied
    """

    __slots__ = ('_raw_mask', '_k_space_mask', '_original_image_data', '_window_type')

    def __init__(
        self,
        reader: SICDTypeReader,
        dimension: int = 1,
        index: int = 0,
        apply_deskew: bool = True,
        apply_deweighting: bool = False,
        window_type: Optional[WindowType] = None
    ) -> None:
        """
        Initialize the polygon aperture filter.
        
        Creates a new aperture filter with enhanced masking and windowing
        capabilities for advanced SAR processing operations.
        
        Parameters
        ----------
        reader : SICDTypeReader
            Reader for accessing SICD data and metadata
        dimension : int, optional
            Processing dimension (0 for row-wise, 1 for column-wise), by default 1
        index : int, optional
            SICD index for multi-image files, by default 0
        apply_deskew : bool, optional
            Whether to apply deskewing correction, by default True
        apply_deweighting : bool, optional
            Whether to apply uniform weighting (remove apodization), by default False
        window_type : Optional[WindowType], optional
            Type of window function to apply initially, by default None
            
        Notes
        -----
        The dimension parameter controls the processing direction:
        - 0: Process along rows (range direction)
        - 1: Process along columns (azimuth direction)
        
        Deskewing corrects for linear phase ramps in the data, while
        deweighting removes the amplitude tapering applied during collection.
        """
        super().__init__(
            reader=reader, 
            dimension=dimension, 
            index=index, 
            apply_deskew=apply_deskew, 
            apply_deweighting=apply_deweighting
        )
        self._raw_mask: Optional[NDArray[np.floating]] = None
        self._k_space_mask: Optional[NDArray[np.floating]] = None
        self._original_image_data: Optional[NDArray[np.complexfloating]] = None
        self._window_type: Optional[WindowType] = window_type

    @property
    def raw_mask(self) -> Optional[NDArray[np.floating]]:
        """
        Get the current raw data mask.
        
        Returns the mask that is applied to complex image data before
        FFT transformation. This mask affects the spatial domain data.
        
        Returns
        -------
        Optional[NDArray[np.floating]]
            Raw mask array with values between 0 and 1, or None if not set
        """
        return self._raw_mask

    @property
    def k_space_mask(self) -> Optional[NDArray[np.floating]]:
        """
        Get the current k-space mask.
        
        Returns the mask that is applied to the normalized phase history
        after FFT transformation. This mask affects the frequency domain data.
        
        Returns
        -------
        Optional[NDArray[np.floating]]
            K-space mask array with values between 0 and 1, or None if not set
        """
        return self._k_space_mask

    @property
    def normalized_phase_history(self) -> Optional[NDArray[np.complexfloating]]:
        """
        Get the normalized phase history (k-space data).
        
        Returns the complex-valued k-space representation of the data after
        applying any masks and windowing functions. This is the frequency
        domain representation used for sub-aperture processing.
        
        Returns
        -------
        Optional[NDArray[np.complexfloating]]
            Complex k-space data array, or None if not available
        """
        return self._normalized_phase_history

    def set_raw_mask(self, mask: NDArray[np.floating]) -> None:
        """
        Set the raw data mask.
        
        Sets a mask to be applied to the complex image data before FFT
        transformation. The mask must match the sub-image bounds and should
        contain values between 0 (completely masked) and 1 (unmasked).
        
        Parameters
        ----------
        mask : NDArray[np.floating]
            Mask array with same shape as sub-image bounds, values in [0, 1]
            
        Raises
        ------
        ValueError
            If sub_image_bounds is not set or mask shape doesn't match expected shape
            
        Notes
        -----
        The raw mask is applied in the spatial domain before FFT transformation.
        This affects both the amplitude and phase of the resulting k-space data.
        After setting the mask, the normalized phase history is automatically
        recalculated.
        """
        if self._sub_image_bounds is None:
            raise ValueError("Cannot set raw mask before sub_image_bounds is set")
            
        row_bounds, col_bounds = self._sub_image_bounds
        expected_shape = (row_bounds[1] - row_bounds[0], col_bounds[1] - col_bounds[0])
        
        if mask.shape != expected_shape:
            raise ValueError(
                f"Raw mask shape {mask.shape} must match sub-image shape {expected_shape}"
            )
            
        self._raw_mask = mask
        self._set_normalized_phase_history()
        
    def set_k_space_mask(self, mask: NDArray[np.floating]) -> None:
        """
        Set the k-space mask.
        
        Sets a mask to be applied to the normalized phase history after FFT.
        The mask must match the phase history dimensions and should contain
        values between 0 (completely masked) and 1 (unmasked).
        
        Parameters
        ----------
        mask : NDArray[np.floating]
            Mask array with same shape as normalized_phase_history, values in [0, 1]
            
        Raises
        ------
        ValueError
            If normalized_phase_history is not initialized or mask shape doesn't match
            
        Notes
        -----
        The k-space mask is applied in the frequency domain after FFT transformation.
        This allows for precise control over which frequencies are retained in
        the sub-aperture processing.
        """
        if self._normalized_phase_history is None:
            raise ValueError("Cannot set k-space mask before normalized_phase_history is initialized")
            
        if mask.shape != self._normalized_phase_history.shape:
            raise ValueError(
                f"K-space mask shape {mask.shape} must match "
                f"normalized_phase_history shape {self._normalized_phase_history.shape}"
            )
            
        self._k_space_mask = mask
        self._apply_k_space_mask()
        
    def clear_raw_mask(self) -> None:
        """
        Clear the raw data mask.
        
        Removes the raw mask and recalculates the normalized phase history
        without spatial domain masking. This restores the full spatial
        extent of the data.
        """
        self._raw_mask = None
        self._set_normalized_phase_history()
        
    def clear_k_space_mask(self) -> None:
        """
        Clear the k-space mask.
        
        Removes the k-space mask and recalculates the normalized phase history
        without frequency domain masking. This restores the full spectral
        content of the data.
        """
        self._k_space_mask = None
        self._set_normalized_phase_history()
        
    def clear_all_masks(self) -> None:
        """
        Clear both raw and k-space masks.
        
        Removes all masks and recalculates the normalized phase history
        using the full, unmasked data. This completely restores the
        original data extent.
        """
        self._raw_mask = None
        self._k_space_mask = None
        self._set_normalized_phase_history()

    def apply_window_function(self, window_type: WindowType) -> None:
        """
        Apply a windowing function to the data.
        
        Applies the specified windowing function to reduce sidelobes and
        improve image quality. The window is applied in the spatial domain
        before FFT transformation.
        
        Parameters
        ----------
        window_type : WindowType
            Type of window function to apply:
            - "None": No windowing (rectangular window)
            - "Gaussian": Gaussian taper with good sidelobe suppression
            - "1/x^4": Polynomial window with strong sidelobe reduction
            - "Hamming": Classic raised cosine window
            - "Cosine on Pedestal": Cosine window with adjustable pedestal
            
        Notes
        -----
        Windowing functions trade off between mainlobe width and sidelobe levels.
        Gaussian and 1/x^4 windows provide excellent sidelobe suppression but
        increase the mainlobe width. Hamming provides a good compromise.
        
        The window is applied as a 2D separable function, with the same
        window applied in both row and column directions.
        """
        self._window_type = window_type
        self._set_normalized_phase_history_with_window()

    def __getitem__(self, item: Any) -> Optional[NDArray[np.complexfloating]]:
        """
        Get filtered data for a specific k-space region.
        
        Applies inverse FFT to a selected region of the normalized phase
        history to generate filtered spatial domain data. This is the core
        operation for sub-aperture processing.
        
        Parameters
        ----------
        item : Any
            Slice or index specification for k-space selection
            
        Returns
        -------
        Optional[NDArray[np.complexfloating]]
            Filtered complex spatial domain data, or None if phase history unavailable
            
        Notes
        -----
        This method creates a zero-filled k-space array with only the selected
        region containing data, then applies inverse FFT to generate the
        filtered spatial domain result. This effectively applies a brick-wall
        filter in the frequency domain.
        """
        if self.normalized_phase_history is None:
            return None
            
        filtered_cdata = np.zeros(self.normalized_phase_history.shape, dtype='complex64')
        filtered_cdata[item] = self.normalized_phase_history[item]
        
        return self._get_fft_phase_data(filtered_cdata)

    def _apply_k_space_mask(self) -> None:
        """
        Apply the k-space mask to normalized phase history.
        
        Multiplies the normalized phase history by the k-space mask
        if both are available. This is called automatically when
        masks or phase history are updated.
        """
        if self._k_space_mask is not None and self._normalized_phase_history is not None:
            self._normalized_phase_history = self._normalized_phase_history * self._k_space_mask
    
    def _set_normalized_phase_history(self) -> None:
        """
        Set the normalized phase history with current masks.
        
        Computes the FFT of the (possibly masked) complex data to generate
        the normalized phase history for display and processing. This method
        applies raw masking but not windowing.
        
        Raises
        ------
        ValueError
            If row or column bounds exceed the underlying data size
        """
        if self._sub_image_bounds is None:
            self._normalized_phase_history = None
            return

        row_bounds, col_bounds = self._sub_image_bounds
        underlying_size = self._deskew_calculator.data_size
        
        if row_bounds[0] < 0 or row_bounds[1] > underlying_size[0]:
            raise ValueError(
                f'Desired row_bounds {row_bounds} exceed underlying data size {underlying_size}'
            )
        if col_bounds[0] < 0 or col_bounds[1] > underlying_size[1]:
            raise ValueError(
                f'Desired col_bounds {col_bounds} exceed underlying data size {underlying_size}'
            )

        self._original_image_data = self._deskew_calculator[
            row_bounds[0]:row_bounds[1], 
            col_bounds[0]:col_bounds[1]
        ]
        
        if self._raw_mask is not None:
            masked_data = self._original_image_data * self._raw_mask
        else:
            masked_data = self._original_image_data
            
        self._normalized_phase_history = self._get_fft_complex_data(masked_data)
        self._apply_k_space_mask()

    def _set_normalized_phase_history_with_window(self) -> None:
        """
        Set normalized phase history with windowing applied.
        
        Computes the windowed FFT of the complex data using the currently
        selected window function. This method applies both raw masking
        and windowing before FFT transformation.
        
        Raises
        ------
        ValueError
            If row or column bounds exceed the underlying data size
        """
        if self._sub_image_bounds is None:
            self._normalized_phase_history = None
            return

        row_bounds, col_bounds = self._sub_image_bounds
        underlying_size = self._deskew_calculator.data_size
        
        if row_bounds[0] < 0 or row_bounds[1] > underlying_size[0]:
            raise ValueError(
                f'Desired row_bounds {row_bounds} exceed underlying data size {underlying_size}'
            )
        if col_bounds[0] < 0 or col_bounds[1] > underlying_size[1]:
            raise ValueError(
                f'Desired col_bounds {col_bounds} exceed underlying data size {underlying_size}'
            )

        self._original_image_data = self._deskew_calculator[
            row_bounds[0]:row_bounds[1], 
            col_bounds[0]:col_bounds[1]
        ]
        
        if self._raw_mask is not None:
            masked_data = self._original_image_data * self._raw_mask
        else:
            masked_data = self._original_image_data
        
        windowed_data = self._apply_window_to_data(masked_data, self._window_type)
        self._normalized_phase_history = self._get_fft_complex_data(windowed_data)
        self._apply_k_space_mask()
    
    def _apply_window_to_data(
        self, 
        data: NDArray[np.complexfloating], 
        window_type: Optional[WindowType]
    ) -> NDArray[np.complexfloating]:
        """
        Apply windowing function to complex data.
        
        Applies the specified 2D windowing function to the complex data
        to reduce spectral leakage and sidelobes. The window is applied
        as a separable 2D function.
        
        Parameters
        ----------
        data : NDArray[np.complexfloating]
            Complex data to window
        window_type : Optional[WindowType]
            Type of window function to apply
            
        Returns
        -------
        NDArray[np.complexfloating]
            Windowed complex data with same shape as input
            
        Notes
        -----
        The windowing is applied as the outer product of 1D windows in
        each direction, creating a separable 2D window function. This
        approach is computationally efficient and provides good results
        for most SAR processing applications.
        """
        if window_type is None or window_type == "None":
            return data
                
        rows, cols = data.shape[:2]
        
        if window_type == "Gaussian":
            row_window = self._gaussian_window(rows)
            col_window = self._gaussian_window(cols)
        elif window_type == "1/x^4":
            row_window = self._x4_window(rows)
            col_window = self._x4_window(cols)
        elif window_type == "Hamming":
            row_window = np.hamming(rows)
            col_window = np.hamming(cols)
        elif window_type == "Cosine on Pedestal":
            pedestal = 0.5  # Default pedestal height
            row_window = self._cosine_pedestal_window(rows, pedestal)
            col_window = self._cosine_pedestal_window(cols, pedestal)
        else:
            return data
        
        window_2d = np.outer(row_window, col_window)
        return data * window_2d

    def _gaussian_window(self, N: int) -> NDArray[np.floating]:
        """
        Generate a Gaussian window function.
        
        Creates a Gaussian-shaped window with good sidelobe suppression
        characteristics. The window has a smooth taper that minimizes
        spectral leakage.
        
        Parameters
        ----------
        N : int
            Length of the window
            
        Returns
        -------
        NDArray[np.floating]
            Gaussian window coefficients normalized to peak value of 1
            
        Notes
        -----
        The Gaussian window is defined by:
        w[n] = exp(-0.5 * ((n - (N-1)/2) / (α*(N-1)/2))^2)
        
        where α = (N-1)/(2*σ*N) and σ = 0.4 is chosen to provide
        good sidelobe suppression while maintaining reasonable
        mainlobe width.
        """
        sigma = 0.4
        n = np.arange(0, N)
        alpha = (N-1)/(2*sigma*N)
        w = np.exp(-0.5 * ((n - (N-1)/2)/(alpha*(N-1)/2))**2)
        return w

    def _x4_window(self, N: int) -> NDArray[np.floating]:
        """
        Generate a 1/x^4 window function.
        
        Creates a polynomial window that provides excellent sidelobe
        suppression at the cost of increased mainlobe width. This window
        is particularly effective for high dynamic range applications.
        
        Parameters
        ----------
        N : int
            Length of the window
            
        Returns
        -------
        NDArray[np.floating]
            1/x^4 window coefficients normalized to peak value of 1
            
        Notes
        -----
        The 1/x^4 window is defined by:
        w[x] = 1 / (1 + 15 * x^4)
        
        where x is linearly spaced from -1 to 1. The coefficient 15
        is chosen to provide the desired sidelobe characteristics.
        A small epsilon is added to prevent division by zero.
        """
        x = np.linspace(-1, 1, N)
        eps = 1e-6
        x_squared = x**2 + eps
        w = 1 / (1 + 15 * x_squared**2)
        w = w / np.max(w)  # Normalize to unit peak
        return w

    def _cosine_pedestal_window(
        self, 
        N: int, 
        pedestal_height: float = 0.5
    ) -> NDArray[np.floating]:
        """
        Generate a cosine-on-pedestal window function.
        
        Creates a window function that combines a flat pedestal with
        cosine-squared tapering at the edges. This provides adjustable
        trade-offs between sidelobe suppression and mainlobe width.
        
        Parameters
        ----------
        N : int
            Length of the window
        pedestal_height : float, optional
            Height of the flat pedestal (0.0 to 1.0), by default 0.5
            
        Returns
        -------
        NDArray[np.floating]
            Cosine-on-pedestal window coefficients
            
        Notes
        -----
        The cosine-on-pedestal window is defined by:
        w[x] = pedestal_height + (1 - pedestal_height) * cos^2(π*(x - 0.5))
        
        where x is linearly spaced from 0 to 1. The pedestal_height parameter
        controls the minimum value of the window, with higher values providing
        less tapering and lower sidelobe suppression.
        """
        pedestal_height = max(0, min(1, pedestal_height))
        x = np.linspace(0, 1, N)
        w = pedestal_height + (1 - pedestal_height) * np.cos(np.pi * (x - 0.5)) ** 2
        return w


class SICDProcessor:
    """
    Helper class for SICD metadata processing.
    
    This class handles the complex operations required to update SICD
    metadata when performing sub-aperture processing, including coordinate
    transformations, time offset calculations, and metadata consistency.
    
    Methods
    -------
    update_chip_sub_aperture_sicd(selected_widget, aperture_roi, k_space_roi, aperture_filter)
        Update SICD metadata for sub-aperture processed chips
    """
    
    def update_chip_sub_aperture_sicd(
        self, 
        selected_widget: Any, 
        aperture_roi: Any, 
        k_space_roi: Any, 
        aperture_filter: 'PolygonApertureFilter',
        aperture_fraction: float
    ) -> 'SICDType':
        """
        Update chip SICD metadata for sub-aperture processing.
        
        Creates updated SICD metadata that correctly reflects the spatial
        and spectral subsetting performed during aperture processing. This
        includes updating geometry, timing, and grid parameters.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the original image data and reader
        aperture_roi : Any
            Spatial domain region of interest
        k_space_roi : Any
            K-space domain region of interest
        aperture_filter : PolygonApertureFilter
            The aperture filter used for processing
            
        Returns
        -------
        SICDType
            Updated SICD metadata for the processed chip
        """
        full_sicd = selected_widget.reader.get_sicds_as_tuple()[0]
        
        # Calculate bounds
        spatial_bounds = self._calculate_spatial_bounds(aperture_roi, selected_widget)
        k_space_bounds = self._calculate_k_space_bounds(k_space_roi)

        
        # Get full k-space dimensions
        full_kspace = aperture_filter.normalized_phase_history
        if full_kspace is None:
            return full_sicd
        
        k_rows, k_cols = full_kspace.shape
        
        # Create initial chip SICD
        chip_sicd, _, _ = full_sicd.create_subset_structure(
            row_bounds=(spatial_bounds['y'], spatial_bounds['y'] + spatial_bounds['height']),
            column_bounds=(spatial_bounds['x'], spatial_bounds['x'] + spatial_bounds['width'])
        )

        # Calculate and apply time offset
        chip_sicd = self._apply_time_offset(chip_sicd, k_space_bounds, k_cols, full_sicd)
        
        # Update scene center position
        chip_sicd = self._update_scene_center(chip_sicd)
        
        # Update Grid parameters for k-space subset
        chip_sicd = self._update_grid_parameters(chip_sicd, k_space_bounds, k_rows, k_cols)

        # TODO: add logic for aperture percent for other modes outside of slow and fast
        chip_sicd = self._update_cdp(chip_sicd, aperture_fraction)
        
        # Final derive to recalculate all dependent parameters
        chip_sicd.derive()
        
        return chip_sicd

    def _calculate_spatial_bounds(
        self, 
        aperture_roi: Any, 
        selected_widget: Any
    ) -> Dict[str, int]:
        """
        Calculate spatial bounds from aperture ROI.
        
        Converts ROI coordinates from screen space to full-resolution
        image coordinates for SICD metadata calculations.
        
        Parameters
        ----------
        aperture_roi : Any
            Region of interest in spatial domain
        selected_widget : Any
            Widget with coordinate transformation information
            
        Returns
        -------
        Dict[str, int]
            Spatial bounds with keys 'x', 'y', 'width', 'height'
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
        
        Extracts position and size information from the k-space ROI
        for metadata calculations.
        
        Parameters
        ----------
        k_space_roi : Any
            K-space region of interest
            
        Returns
        -------
        Dict[str, int]
            K-space bounds with keys 'kx', 'ky', 'kwidth', 'kheight'
        """
        k_space_pos = k_space_roi.pos()
        k_space_size = k_space_roi.size()
        
        return {
            'kx': int(k_space_pos[0]),
            'ky': int(k_space_pos[1]),
            'kwidth': int(k_space_size[0]),
            'kheight': int(k_space_size[1])
        }

    def _apply_time_offset(
        self, 
        chip_sicd: 'SICDType', 
        k_space_bounds: Dict[str, int], 
        k_cols: int, 
        full_sicd: 'SICDType'
    ) -> 'SICDType':
        """
        Apply time offset based on k-space position.
        
        Calculates and applies a time offset to the ARP (Antenna Reference Point)
        position and velocity based on the center of the k-space selection.
        
        Parameters
        ----------
        chip_sicd : SICDType
            Chip SICD metadata to update
        k_space_bounds : Dict[str, int]
            K-space bounds information
        k_cols : int
            Total number of k-space columns
        full_sicd : SICDType
            Original full SICD metadata
            
        Returns
        -------
        SICDType
            Updated SICD with time offset applied
        """
        col_center_fraction = (k_space_bounds['kx'] + k_space_bounds['kwidth']/2) / k_cols
        
        if hasattr(full_sicd.ImageFormation, 'TStartProc') and hasattr(full_sicd.ImageFormation, 'TEndProc'):
            original_duration = full_sicd.ImageFormation.TEndProc - full_sicd.ImageFormation.TStartProc
            original_t_center = (full_sicd.ImageFormation.TStartProc + full_sicd.ImageFormation.TEndProc) / 2
            
            new_t_center = full_sicd.ImageFormation.TStartProc + (col_center_fraction * original_duration)
            time_offset = new_t_center - original_t_center
            
            chip_sicd = self._update_arp_for_time_offset(chip_sicd, time_offset)
        
        return chip_sicd

    def _update_arp_for_time_offset(
        self, 
        meta: 'SICDType', 
        time_offset: float
    ) -> 'SICDType':
        """
        Update ARP position and velocity based on time offset.
        
        Applies kinematic equations to update the antenna reference point
        position and velocity for the new time center.
        
        Parameters
        ----------
        meta : SICDType
            SICD metadata to update
        time_offset : float
            Time offset in seconds
            
        Returns
        -------
        SICDType
            Updated SICD with new ARP parameters
        """
        new_meta = copy.deepcopy(meta)
        
        for xyz in ['X', 'Y', 'Z']:
            original_pos = getattr(meta.SCPCOA.ARPPos, xyz)
            original_vel = getattr(meta.SCPCOA.ARPVel, xyz)
            original_acc = getattr(meta.SCPCOA.ARPAcc, xyz)
            
            # Calculate new position and velocity using kinematic equations
            new_pos = original_pos + original_vel * time_offset + 0.5 * original_acc * (time_offset ** 2)
            new_vel = original_vel + original_acc * time_offset
            
            setattr(new_meta.SCPCOA.ARPPos, xyz, new_pos)
            setattr(new_meta.SCPCOA.ARPVel, xyz, new_vel)
        
        # Remove calculated angle fields for recalculation
        angle_fields_to_remove = [
            'GrazeAng', 'IncidenceAng', 'TwistAng', 'SlopeAng', 
            'AzimAng', 'LayoverAng', 'SquintAng', 'DopplerConeAng', 'ImRespBW'
        ]
        
        for field in angle_fields_to_remove:
            if hasattr(new_meta.SCPCOA, field):
                setattr(new_meta.SCPCOA, field, None)
        
        return new_meta

    def _update_scene_center(self, chip_sicd: 'SICDType') -> 'SICDType':
        """
        Update scene center position for the chip.
        
        Recalculates the scene center point based on the chip geometry
        and updates the SCPCOA accordingly.
        
        Parameters
        ----------
        chip_sicd : SICDType
            Chip SICD metadata to update
            
        Returns
        -------
        SICDType
            Updated SICD with new scene center
        """
        center_row = chip_sicd.ImageData.SCPPixel.Row
        center_col = chip_sicd.ImageData.SCPPixel.Col

        pos_ecf = image_to_ground([center_row, center_col], chip_sicd)
        return self._update_scpcoa(chip_sicd, pos_ecf)

    def _update_scpcoa(
        self, 
        meta_data: 'SICDType', 
        pos_ecf: NDArray[np.floating]
    ) -> 'SICDType':
        """
        Update SCPCOA with new position.
        
        Updates the Scene Center Point of the Collection Area with a new
        Earth-Centered Fixed coordinate position.
        
        Parameters
        ----------
        meta_data : SICDType
            SICD metadata to update
        pos_ecf : NDArray[np.floating]
            New ECF position [x, y, z]
            
        Returns
        -------
        SICDType
            Updated SICD metadata
        """
        meta_data.GeoData.SCP.ECF.X = pos_ecf[0]
        meta_data.GeoData.SCP.ECF.Y = pos_ecf[1] 
        meta_data.GeoData.SCP.ECF.Z = pos_ecf[2]


        from sarpy.io.complex.sicd_elements.Grid import DirParamType
        # Remove essential fields for recalculation
        essential_fields_to_remove = [
            'SideOfTrack', 'SlantRange', 'GroundRange', 'DopplerConeAng',
            'GrazeAng', 'IncidenceAng', 'AzimAng'
        ]
        
        for field in essential_fields_to_remove:
            if hasattr(meta_data.SCPCOA, field):
                setattr(meta_data.SCPCOA, field, None)

        meta_data.derive()

        return meta_data

    def _update_grid_parameters(
        self, 
        chip_sicd: 'SICDType', 
        k_space_bounds: Dict[str, int], 
        k_rows: int, 
        k_cols: int
    ) -> 'SICDType':
        """
        Update Grid parameters for k-space subset.
        
        Adjusts grid parameters to reflect the reduced aperture size
        and its impact on impulse response characteristics.
        
        Parameters
        ----------
        chip_sicd : SICDType
            Chip SICD metadata to update
        k_space_bounds : Dict[str, int]
            K-space bounds information
        k_rows : int
            Total number of k-space rows
        k_cols : int
            Total number of k-space columns
            
        Returns
        -------
        SICDType
            Updated SICD with corrected grid parameters
        """
        if chip_sicd.Grid:
            row_fraction = k_space_bounds['kheight'] / k_rows
            col_fraction = k_space_bounds['kwidth'] / k_cols
            
            # fast_center = (k_space_bounds['ky'] + k_space_bounds['kheight']/2) / k_rows
        
            # slow_center = (k_space_bounds['kx'] + k_space_bounds['kwidth']/2) / k_cols

            if chip_sicd.Grid.Row:
                self._update_grid_direction(chip_sicd.Grid.Row, row_fraction)
                # chip_sicd.Grid.Row.DeltaKCOAPoly = chip_sicd.Grid.Row.Sgn * (fast_center - 0.5) / chip_sicd.Grid.Row.SS
            
            if chip_sicd.Grid.Col:
                self._update_grid_direction(chip_sicd.Grid.Col, col_fraction)
                # chip_sicd.Grid.Col.DeltaKCOAPoly = -chip_sicd.Grid.Col.Sgn * (slow_center - 0.5) / chip_sicd.Grid.Col.SS
   
        return chip_sicd

    def _update_grid_direction(
        self, 
        grid_direction: Any, 
        fraction: float
    ) -> None:
        """
        Update grid direction parameters.
        
        Updates impulse response width and bandwidth based on the
        fraction of aperture used in processing.
        
        Parameters
        ----------
        grid_direction : Any
            Grid direction object (Row or Col)
        fraction : float
            Fraction of original aperture used
        """
        orig_imp_resp_wid = grid_direction.ImpRespWid
        orig_imp_resp_bw = grid_direction.ImpRespBW
        
        # Update IPR (gets worse with smaller aperture)
        grid_direction.ImpRespWid = orig_imp_resp_wid / fraction
        grid_direction.ImpRespBW = orig_imp_resp_bw * fraction
        
        # Update frequency extents
        grid_direction.DeltaK1 = -grid_direction.ImpRespBW / 2
        grid_direction.DeltaK2 = grid_direction.ImpRespBW / 2

    def _update_cdp(self,
                    meta_data: 'SICDType',
                    aperture_percent
    ):
        """
        Update metadata with updated CDP
        
        Parameters
        ----------
        meta_data : SICDType
            SICD metadata to update
        aperture_percent : float
            Aperture percentage between 0.01 and 1
            
        Returns
        -------
        SICDType
            Updated SICD metadata
        """

        meta_data.Timeline.CollectDuration = meta_data.Timeline.CollectDuration * aperture_percent

        return meta_data
                    