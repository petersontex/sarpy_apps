import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.io
import shapely
from numpy.typing import NDArray
from PySide6.QtGui import QColor

from sarpy.annotation.base import AnnotationCollection, AnnotationFeature, FileAnnotationCollection
from sarpy.annotation.rcs import FileRCSCollection, RCSFeature, _get_polygon_bounds
from sarpy.geometry.geocoords import ecf_to_geodetic, geodetic_to_ecf, wgs_84_norm
from sarpy.geometry.geometry_elements import Polygon


class Model:
    """
    Model for Radar Cross Section (RCS) Analysis.
    
    This class implements the Model component in the MVC (Model-View-Controller) 
    architecture for radar cross section (RCS) analysis. It manages SAR (Synthetic 
    Aperture Radar) data processing and RCS calculations.
    
    The Model provides functionality for:
    - RCS calculations with various calibration options
    - Data visualization preparation (slow/fast time profiles)
    - Calibration with different measurement units (RCS, σ₀, β₀, γ₀)
    
    Attributes
    ----------
    _reference_azimuth_angle : float
        Reference angle in degrees for azimuth calculations, defaults to 0.
    """

    def __init__(self) -> None:
        """
        Initialize the Model class with default values.
        
        Sets up the reference azimuth angle for calculations.
        """
        self._reference_azimuth_angle: float = 0.0

    def set_reference_azimuth_angle(self, reference_azimuth_angle: float) -> None:
        """
        Set the reference azimuth angle for calculations.
        
        Parameters
        ----------
        reference_azimuth_angle : float
            The reference azimuth angle in degrees.
        """
        self._reference_azimuth_angle = reference_azimuth_angle

    def get_reference_azimuth_angle(self) -> float:
        """
        Get the current reference azimuth angle.
        
        Returns
        -------
        float
            The current reference azimuth angle in degrees.
        """
        return self._reference_azimuth_angle

    def calculate_rcs(self, selected_widget: Any, geometry: Any) -> RCSFeature:
        """
        Calculate radar cross section for a given geometry.
        
        Parameters
        ----------
        selected_widget : Any
            The widget containing the SAR image data and reader.
        geometry : Any
            The geometry object to calculate RCS for.
            
        Returns
        -------
        RCSFeature
            An RCS feature object containing the calculated RCS parameters.
        """
        reader = selected_widget.reader

        rcs_feature = RCSFeature()
        rcs_feature.geometry = geometry
        rcs_feature.set_rcs_parameters_from_reader(reader) 

        return rcs_feature
        
    def compute_slow_time_axis(
        self, 
        meta_data: Dict[str, Any], 
        selected_widget: Any, 
        units: str, 
        center_rowcol: Optional[List[float]] = None, 
        relative_azimuth: Optional[float] = None
    ) -> Tuple[NDArray[np.float64], str]:
        """
        Compute slow time axis information for plotting.
        
        Parameters
        ----------
        meta_data : Dict[str, Any]
            SICD metadata dictionary containing Grid and SCPCOA information.
        selected_widget : Any
            Widget containing the reader and image data.
        units : str
            Units for the axis ('Collect Time', 'Polar Angle', 'Azimuth Angle', 
            'Aperture Relative', 'Target Relative').
        center_rowcol : List[float], optional
            Center pixel coordinates [row, col] for calculations.
        relative_azimuth : float, optional
            Relative azimuth angle in degrees.
            
        Returns
        -------
        Tuple[NDArray[np.float64], str]
            A tuple containing:
            - Array of axis values [min, max]
            - String label for the axis
            
        Raises
        ------
        ValueError
            If invalid units are provided.
        """
        azimuth_padding = 1 / (
            meta_data['Grid']['Col']['ImpRespBW'] * meta_data['Grid']['Col']['SS']
        )
        
        if units == "Collect Time":
            theta = meta_data['Grid']['Col']['ImpRespBW'] / meta_data['Grid']['Row']['KCtr']
            velocity = np.linalg.norm(np.array([
                meta_data['SCPCOA']['ARPVel']['X'], 
                meta_data['SCPCOA']['ARPVel']['Y'], 
                meta_data['SCPCOA']['ARPVel']['Z']
            ]))
            effective_duration = (
                theta * (meta_data['SCPCOA']['SlantRange'] / velocity) 
                / np.sin(np.radians(meta_data['SCPCOA']['DopplerConeAng']))
            )

            image_formation = meta_data.get('ImageFormation', {})
            collection_info = meta_data.get('CollectionInfo', {})
            radar_mode = collection_info.get('RadarMode', {})

            if (
                image_formation.get('ImageFormAlgo') == 'PFA' and
                all(key in image_formation for key in ('TStartProc', 'TEndProc')) and
                radar_mode.get('ModeType') == 'SPOTLIGHT'
            ):
                effective_duration = image_formation['TEndProc'] - image_formation['TStartProc']

            axis_range = np.array([0, effective_duration]) + (
                np.array([-1, 1]) * 0.5 * effective_duration * (azimuth_padding - 1)
            )
            label = "Collection Time (sec)"

        elif units == "Polar Angle":
            orientation = np.array([1, -1])
            if meta_data['SCPCOA']['SideOfTrack'][0] != 'R':
                orientation = -1 * orientation
            axis_range = np.degrees(np.arctan(
                (orientation / (2 * meta_data['Grid']['Col']['SS']) 
                 / meta_data['Grid']['Row']['KCtr'])
            ))
            label = 'Polar Angle <deg>'

        elif units == "Azimuth Angle":
            st_mid_end = self.compute_azimuth(
                meta_data, selected_widget, np.array([0, 50, 100]), center_rowcol
            )
            st_mid_end = np.unwrap(st_mid_end * np.pi / 180) * 180 / np.pi
            relative_azimuth = 0
            label = "Azimuth Angle \u00B0"
            delta_azimuth = np.diff([st_mid_end[0], st_mid_end[-1]])[0]
            axis_range = (
                np.array([st_mid_end[0], st_mid_end[-1]])
                + np.array([-1, 1]) * 0.5 * delta_azimuth * (azimuth_padding - 1)
                - relative_azimuth
            )
            
        elif units == "Aperture Relative":
            st_mid_end = self.compute_azimuth(
                meta_data, selected_widget, np.array([0, 50, 100]), center_rowcol
            )
            st_mid_end = np.unwrap((st_mid_end * np.pi / 180)) * 180 / np.pi
            relative_azimuth = st_mid_end[1]
            label = "Azimuth Angle Relative To Aperture Center \u00B0"
            delta_azimuth = np.diff([st_mid_end[0], st_mid_end[-1]])[0]
            axis_range = (
                np.array([st_mid_end[0], st_mid_end[-1]])
                + np.array([-1, 1]) * 0.5 * delta_azimuth * (azimuth_padding - 1)
                - relative_azimuth
            )
            
        elif units == "Target Relative":
            relative_azimuth = self.get_reference_azimuth_angle()
            st_mid_end = self.compute_azimuth(
                meta_data, selected_widget, np.array([0, 50, 100]), center_rowcol
            )
            st_mid_end = np.unwrap((st_mid_end * np.pi / 180)) * 180 / np.pi
            label = f'Azimuth Angle Relative To Target @ {relative_azimuth} <deg>'
            delta_azimuth = np.diff([st_mid_end[0], st_mid_end[-1]])[0]
            axis_range = (
                np.array([st_mid_end[0], st_mid_end[-1]])
                + np.array([-1, 1]) * 0.5 * delta_azimuth * (azimuth_padding - 1)
                - relative_azimuth
            )
        else:
            raise ValueError(f"Invalid units '{units}' for slow time axis.")

        return axis_range, label

    def compute_fast_time_axis(self, meta: Dict[str, Any]) -> Tuple[List[float], str]:
        """
        Compute fast time axis information for range frequency plotting.

        Parameters
        ----------
        meta : Dict[str, Any]
            Metadata dictionary containing Grid and Row information.

        Returns
        -------
        Tuple[List[float], str]
            A tuple containing:
            - List of frequency values [min, max] in GHz
            - String label for the axis
        """
        SPEED_OF_LIGHT = 299792458  # meters per second

        # Check if all required nested keys exist
        has_grid = "Grid" in meta
        has_row = has_grid and "Row" in meta.get("Grid", {})
        has_required_fields = has_row and all(
            key in meta.get("Grid", {}).get("Row", {}) for key in ["SS", "KCtr"]
        )

        if has_required_fields:
            # Frequency calculations
            bw_rg = SPEED_OF_LIGHT / (2 * meta["Grid"]["Row"]["SS"])
            vfrq_c = meta["Grid"]["Row"]["KCtr"] * SPEED_OF_LIGHT / 2

            range_vals = [
                (vfrq_c + sign * bw_rg / 2) / 1e9  # Convert to GHz
                for sign in [-1, 1]
            ]

            return range_vals, "Frequency (GHz)"
        else:
            # Resort to unitless axis and warn the user
            warnings.warn(
                "Insufficient metadata to determine receive frequencies.", 
                UserWarning,
                stacklevel=2
            )
            return [0, 1], ""

    def compute_azimuth(
        self, 
        meta: Dict[str, Any], 
        selected_widget: Any, 
        percent: Optional[Union[float, NDArray[np.float64]]] = None, 
        pixel_coords: Optional[List[float]] = None
    ) -> NDArray[np.float64]:
        """
        Compute azimuth angle (angle from north) across spatial frequency.

        Parameters
        ----------
        meta : Dict[str, Any]
            SICD metadata structure.
        selected_widget : Any
            Widget containing the reader for coordinate transformations.
        percent : Union[float, NDArray[np.float64]], optional
            Array of values from 0 to 100. Indicates the fraction across 
            the spatial frequency in azimuth for which to compute azimuth angle.
            Defaults to 50 (center of aperture).
        pixel_coords : List[float], optional
            [column_index, row_index] (az,rng) index to point of interest.
            Defaults to scene center point (SCP).

        Returns
        -------
        NDArray[np.float64]
            Computed azimuth angle for each percent value in degrees.
            
        Notes
        -----
        Should work generically for many types of SAR complex data, not just
        spotlight collects. If pixel_coords is None, defaults to scene center point (SCP).
        
        Raises
        ------
        ValueError
            If unable to compute SICD Grid.TimeCOAPoly field from complex data.
        """
        # Handle default values for input parameters
        if percent is None:
            # SCPCOA.AzimAng is an actual field in latest SICD spec
            if "SCPCOA" in meta and "AzimAng" in meta["SCPCOA"]:
                return np.array([meta["SCPCOA"]["AzimAng"]])
            percent = 50  # If SCPCOA.AzimAng not available, compute it
        
        # Ensure percent is a numpy array
        percent = np.asarray(percent)
        original_percent_shape = percent.shape
        percent = percent.flatten()  # Flatten for calculations, reshape at the end
        
        if 'Grid' not in meta or 'TimeCOAPoly' not in meta['Grid']:
            # For spotlight, we can take some shortcuts with missing metadata
            if ('CollectionInfo' in meta and 
                'RadarMode' in meta['CollectionInfo'] and
                'ModeType' in meta['CollectionInfo']['RadarMode'] and
                meta['CollectionInfo']['RadarMode']['ModeType'].upper() == 'SPOTLIGHT'):
                
                if ('SCPCOA' in meta and 'SCPTime' in meta['SCPCOA'] and
                    'Position' in meta and 'ARPPoly' in meta['Position']):
                    meta['Grid'] = {'TimeCOAPoly': meta['SCPCOA']['SCPTime']}
                
                elif ('SCPCOA' in meta and 'ARPPos' in meta['SCPCOA'] and
                    'ARPVel' in meta['SCPCOA']):
                    meta['Grid'] = {'TimeCOAPoly': 0}
                    meta['Position'] = {
                        'ARPPoly': {
                            'X': {'Coefs': [meta['SCPCOA']['ARPPos']['X'], meta['SCPCOA']['ARPVel']['X']]},
                            'Y': {'Coefs': [meta['SCPCOA']['ARPPos']['Y'], meta['SCPCOA']['ARPVel']['Y']]},
                            'Z': {'Coefs': [meta['SCPCOA']['ARPPos']['Z'], meta['SCPCOA']['ARPVel']['Z']]}
                        }
                    }
            
            if 'Grid' not in meta or 'TimeCOAPoly' not in meta['Grid']:
                raise ValueError('Unable to compute SICD Grid.TimeCOAPoly field from complex data.')

        # Point of interest (POI) only required for spatially variant COA
        if pixel_coords is not None:
            # Convention for point_slant_to_ground() pixel coordinates is reverse
            # of what is passed to this function (column/row), so we swap values.
            undecimated_geo_coord = (
                selected_widget.reader.sicd_meta.project_image_to_ground_geo(
                    pixel_coords, projection_type="PLANE"
                ).tolist()
            )
            
            poi_ecf = geodetic_to_ecf(undecimated_geo_coord).transpose()
            
            # Calculate center of aperture (COA) for given point
            time_coa = self.sicd_polyval2d(
                meta['Grid']['TimeCOAPoly'], 
                pixel_coords[0],  # Single scalar value for column
                pixel_coords[1],  # Single scalar value for row
                meta
            )
            
            # If the result is an array with multiple values but we only need one
            if hasattr(time_coa, '__len__') and len(time_coa) > 0:
                time_coa = time_coa.item() if time_coa.size == 1 else time_coa[0]
        else:
            # Default to SCP
            poi_ecf = np.array([
                meta['GeoData']['SCP']['ECF']['X'],
                meta['GeoData']['SCP']['ECF']['Y'],
                meta['GeoData']['SCP']['ECF']['Z']
            ])
            
            # Handle both cases where TimeCOAPoly might be a number or a nested dictionary
            if isinstance(meta["Grid"]["TimeCOAPoly"], (int, float)):
                time_coa = meta["Grid"]["TimeCOAPoly"]
            else:
                if 'Coefs' in meta['Grid']['TimeCOAPoly']:
                    time_coa = meta['Grid']['TimeCOAPoly']['Coefs'][0][0]
                else:
                    # Assuming it's just a scalar value in this case
                    time_coa = meta['Grid']['TimeCOAPoly']
                
            # Check for spatially variant COA
            if isinstance(meta['Grid']['TimeCOAPoly'], dict) and 'Coefs' in meta['Grid']['TimeCOAPoly']:
                coefs = np.array(meta['Grid']['TimeCOAPoly']['Coefs'])
                if np.any(coefs[1:] != 0):
                    warnings.warn(
                        "For non-spotlight data, point of interest must be specified for accurate azimuth angles.",
                        UserWarning,
                        stacklevel=2
                    )

        # Calculate geometry info for center of aperture
        # Extract coefficients from the nested structure
        if 'Coefs' in meta['Position']['ARPPoly']['X']:
            pos_x = np.array(meta['Position']['ARPPoly']['X']['Coefs'])[::-1]
            pos_y = np.array(meta['Position']['ARPPoly']['Y']['Coefs'])[::-1]
            pos_z = np.array(meta['Position']['ARPPoly']['Z']['Coefs'])[::-1]
        else:
            pos_x = np.array(meta['Position']['ARPPoly']['X'])[::-1]
            pos_y = np.array(meta['Position']['ARPPoly']['Y'])[::-1]
            pos_z = np.array(meta['Position']['ARPPoly']['Z'])[::-1]
        
        pos_coefs = np.column_stack([pos_x, pos_y, pos_z])

        # Position at COA
        arp = np.array([
            np.polyval(pos_coefs[:, 0], time_coa),
            np.polyval(pos_coefs[:, 1], time_coa),
            np.polyval(pos_coefs[:, 2], time_coa),
        ])

        # Velocity polynomial is derivative of position polynomial
        vel_coefs = (
            pos_coefs[:-1, :] * np.arange(len(pos_coefs) - 1, 0, -1)[:, np.newaxis]
        )

        # Aperture velocity at COA
        arv = np.array([
            np.polyval(vel_coefs[:, 0], time_coa),
            np.polyval(vel_coefs[:, 1], time_coa),
            np.polyval(vel_coefs[:, 2], time_coa),
        ])

        # Line of sight vector at COA
        los = poi_ecf - arp

        # Range from sensor to POI at COA
        r = np.linalg.norm(los)

        # Speed at COA
        v = np.linalg.norm(arv)

        # Doppler Cone Angle to POI at COA
        dca = np.arccos(np.dot(arv / v, los / r))

        # Compute effective aperture positions for each percentage
        theta = meta["Grid"]["Col"]["ImpRespBW"] / meta["Grid"]["Row"]["KCtr"]
        effective_duration = (theta * r / v) / np.sin(dca)

        # Convert percent to numpy array if it isn't already
        percent = np.asarray(percent)

        # Compute time offsets
        t = effective_duration * ((-1/2) + (percent / 100))

        # Compute positions - each row is a position for a different percent value
        pos = np.column_stack([
            arp[0] + (t * arv[0]),
            arp[1] + (t * arv[1]),
            arp[2] + (t * arv[2])
        ])

        # Calculate actual azimuth angles
        gpn = wgs_84_norm(poi_ecf)  # Ground plane normal

        # Project north onto ground plane
        north_ground = np.array([0, 0, 1]) - (np.dot([0, 0, 1], gpn) * gpn)

        # Range vectors for each time
        range_vec = pos - np.tile(poi_ecf, (len(t), 1))
        
        # Project range vector onto ground plane
        range_ground = range_vec - np.outer(np.dot(range_vec, gpn), gpn)

        # Cross products for each range ground vector with north ground
        cross_products = np.cross(range_ground, np.tile(north_ground, (len(t), 1)))

        # Angle calculation
        dot_products = np.sum(range_ground * np.tile(north_ground, (len(t), 1)), axis=1)
        cross_dot = np.sum(cross_products * gpn, axis=1)

        az = np.arctan2(cross_dot, dot_products) * 180 / np.pi
        
        # Ensure angles are in [0, 360]
        az[az < 0] += 360

        # Reform to shape of original input
        return az.reshape(original_percent_shape)

    def sicd_polyval2d(
        self, 
        poly_coefs: Union[float, int, Dict[str, Any], NDArray], 
        dim1_ind: Union[float, NDArray[np.float64]], 
        dim2_ind: Union[float, NDArray[np.float64]], 
        sicd_meta: Optional[Dict[str, Any]] = None
    ) -> Union[float, NDArray[np.float64]]:
        """
        Evaluate a SICD field of type 2D_POLY.

        Parameters
        ----------
        poly_coefs : Union[float, int, Dict[str, Any], NDArray]
            A SICD field of type 2D_POLY, scalar value, or coefficient array.
        dim1_ind : Union[float, NDArray[np.float64]]
            Value(s) in the first dimension (azimuth).
        dim2_ind : Union[float, NDArray[np.float64]]
            Value(s) in the second dimension (range).
        sicd_meta : Dict[str, Any], optional
            SICD metadata structure. If provided, dim1_ind and dim2_ind will be 
            converted from image indices to image coordinates (meters from SCP).

        Returns
        -------
        Union[float, NDArray[np.float64]]
            Result values of the evaluated polynomial.
            
        Notes
        -----
        Python doesn't have a builtin function for evaluating 2D polynomials, so
        this function evaluates 2D polynomials in SICD over a grid of input values.
        """
        # Convert inputs to numpy arrays for consistent handling
        dim1_ind = np.asarray(dim1_ind)
        dim2_ind = np.asarray(dim2_ind)

        # Handle poly_coefs based on input type
        if isinstance(poly_coefs, (int, float)):
            # If poly_coefs is a scalar, just return it
            return poly_coefs
        elif isinstance(poly_coefs, dict) and 'Coefs' in poly_coefs:
            # If poly_coefs is a SICD structure with 'Coefs' field
            poly_coefs = np.array(poly_coefs["Coefs"])
        else:
            # Otherwise, convert to numpy array
            poly_coefs = np.asarray(poly_coefs)

        # SICD uses the first dimension of its polynomials to refer to the "row"
        # index (range) and the second dimension to refer to the "column" index
        # (azimuth). Transpose to match this convention.
        poly_coefs = poly_coefs.T
        
        # Convert inputs to numpy arrays for consistent handling
        dim1_ind = np.asarray(dim1_ind, dtype=float)
        dim2_ind = np.asarray(dim2_ind, dtype=float)
        
        if sicd_meta is not None:
            # Convert image indices to image coordinates (meters from SCP)
            dim1_vals = (
                (dim1_ind - 1 + 
                 float(sicd_meta['ImageData']['FirstCol']) - 
                 float(sicd_meta['ImageData']['SCPPixel']['Col'])) * 
                float(sicd_meta['Grid']['Col']['SS'])
            )
            
            dim2_vals = (
                (dim2_ind - 1 + 
                 float(sicd_meta['ImageData']['FirstRow']) - 
                 float(sicd_meta['ImageData']['SCPPixel']['Row'])) * 
                float(sicd_meta['Grid']['Row']['SS'])
            )
        else:
            # No conversion requested
            dim1_vals = dim1_ind
            dim2_vals = dim2_ind
        
        # Handle the special case where both inputs are scalar
        if np.isscalar(dim1_vals) and np.isscalar(dim2_vals):
            result = 0.0
            for i in range(poly_coefs.shape[0]):
                for j in range(poly_coefs.shape[1]):
                    result += poly_coefs[i, j] * (dim1_vals ** i) * (dim2_vals ** j)
            return result
        
        # Handle the case where one input is scalar and the other is an array
        if np.isscalar(dim1_vals) and not np.isscalar(dim2_vals):
            dim2_vals = np.asarray(dim2_vals)
            result = np.zeros_like(dim2_vals, dtype=float)
            for i in range(poly_coefs.shape[0]):
                for j in range(poly_coefs.shape[1]):
                    result += poly_coefs[i, j] * (dim1_vals ** i) * (dim2_vals ** j)
            return result
        
        if not np.isscalar(dim1_vals) and np.isscalar(dim2_vals):
            dim1_vals = np.asarray(dim1_vals)
            result = np.zeros_like(dim1_vals, dtype=float)
            for i in range(poly_coefs.shape[0]):
                for j in range(poly_coefs.shape[1]):
                    result += poly_coefs[i, j] * (dim1_vals ** i) * (dim2_vals ** j)
            return result
        
        # Both are arrays - if they have the same length, evaluate point-by-point
        if len(dim1_vals) == len(dim2_vals):
            result = np.zeros_like(dim1_vals, dtype=float)
            for i in range(poly_coefs.shape[0]):
                for j in range(poly_coefs.shape[1]):
                    result += poly_coefs[i, j] * (dim1_vals ** i) * (dim2_vals ** j)
            return result
        
        # If dimensions don't match, create a mesh grid
        dim1_vals = np.asarray(dim1_vals)
        dim2_vals = np.asarray(dim2_vals)
        
        # Create 2D meshgrid
        x_2d, y_2d = np.meshgrid(dim1_vals, dim2_vals, indexing='ij')
        
        # Initialize output array
        output = np.zeros((len(dim1_vals), len(dim2_vals)))

        # Evaluate polynomial
        for i in range(poly_coefs.shape[0]):
            for j in range(poly_coefs.shape[1]):
                output += poly_coefs[i, j] * (x_2d ** i) * (y_2d ** j)
        
        return output

    def rcs_st_ft(
        self, 
        complex_data: NDArray[np.complex128], 
        lookdir: str = 'R', 
        oversample_ratio: Optional[Union[List[float], NDArray[np.float64]]] = None, 
        cal_sf: Optional[Union[float, NDArray[np.float64]]] = None, 
        mask: Optional[NDArray[np.bool_]] = None, 
        meta: Optional[Dict[str, Any]] = None
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Compute total calibrated RCS and slow/fast time RCS data profiles.
        
        Parameters
        ----------
        complex_data : NDArray[np.complex128]
            Complex valued SAR dataset in the image domain.
            First dimension is azimuth, second range.
            Third dimension could be for multi-channel data.
        lookdir : str, default='R'
            Look direction: "Left" or "Right".
        oversample_ratio : Union[List[float], NDArray[np.float64]], optional
            Oversample or zeropad factor. Required for calibrated RCS.
            Defaults to [1, 1] which gives uncalibrated values.
        cal_sf : Union[float, NDArray[np.float64]], optional
            Calibration scale factor (linear). Either a constant or an array 
            the same size as complex_data with per-pixel values.
            Defaults to 1 which gives uncalibrated values.
        mask : NDArray[np.bool_], optional
            Binary image which is ones over the region of interest.
            Defaults to all ones.
        meta : Dict[str, Any], optional
            SICD metadata structure.
        
        Returns
        -------
        Tuple[NDArray[np.float64], NDArray[np.float64]]
            - profile_slow: Slow-time profile
            - profile_fast: Fast-time profile
        """
        # Default parameter values
        if oversample_ratio is None:
            oversample_ratio = np.array([1, 1])  # RCS values will be uncalibrated
        else:
            oversample_ratio = np.asarray(oversample_ratio)

        if cal_sf is None:
            cal_sf = 1  # RCS values will be uncalibrated

        if mask is None:
            mask = np.ones_like(complex_data, dtype=bool)

        # Apply shape mask to rectangular data
        if complex_data.ndim == 3:
            filtimg = complex_data * np.repeat(
                mask[:, :, np.newaxis], complex_data.shape[2], axis=2
            )
        else:
            filtimg = complex_data * mask

        if not np.isscalar(cal_sf):
            # Only works if the radiometric scale factors are same for both channels
            if complex_data.ndim == 3:
                cal_sf = np.repeat(
                    cal_sf[:, :, np.newaxis], complex_data.shape[2], axis=2
                )

        # Inverse polar formatting breaks on some data, so it is disabled
        inverse_polar = False

        # Determine fft size to use based on size of imagery
        data_size = complex_data.shape
        fftsize = (2 ** np.ceil(np.log2(data_size[:2])) * 4).astype(int)

        if inverse_polar:  # Inverse polar formatting is the most precise way
            # Placeholder for future implementation
            raise NotImplementedError("Inverse polar formatting not yet implemented")
        else:
            # Use polar format approximation
            # Columns approximate time/azimuth angle and rows approximate receive frequency
            nz_data_points = (fftsize / oversample_ratio).astype(int)

            rgcomp = np.fft.fftshift(
                np.fft.fft(filtimg, fftsize[0], axis=0, norm='backward'),
                axes=0) / np.sqrt(fftsize[0])

            azcomp = np.fft.fftshift(
                np.fft.fft(filtimg, fftsize[1], axis=1, norm='backward'),
                axes=1) / np.sqrt(fftsize[1])

            profile_slow = (
                np.sum(np.abs(rgcomp) ** 2, axis=1) * 
                nz_data_points[0] ** 2 / oversample_ratio[1]
            )
            profile_fast = (
                np.sum(np.abs(azcomp) ** 2, axis=0) * 
                nz_data_points[1] ** 2 / oversample_ratio[0]
            )
        
        # Handle look direction
        if lookdir.upper().startswith("R"):
            profile_slow = profile_slow[::-1]

        # Handle multi-channel data
        profile_slow = np.squeeze(profile_slow)

        if profile_fast.ndim == 1:
            profile_fast = profile_fast.flatten()  # Just flatten, don't reshape to column
        else:
            profile_fast = np.squeeze(profile_fast)
        
        return profile_slow, profile_fast

    def rcs_range_profile(
        self, 
        complex_data: NDArray[np.complex128], 
        oversample_ratio: Optional[Union[List[float], NDArray[np.float64]]] = None, 
        cal_sf: Optional[Union[float, NDArray[np.float64]]] = None, 
        mask: Optional[NDArray[np.bool_]] = None
    ) -> NDArray[np.float64]:
        """
        Compute calibrated range profile.

        Parameters
        ----------
        complex_data : NDArray[np.complex128]
            Complex valued SAR dataset in the image domain.
            First dimension is azimuth, second range.
            Third dimension could be for multi-channel data.
        oversample_ratio : Union[List[float], NDArray[np.float64]], optional
            Oversample or zeropad factor. Required for calibrated RCS.
            Defaults to [1, 1] which gives uncalibrated values.
        cal_sf : Union[float, NDArray[np.float64]], optional
            Calibration scale factor (linear). Either a constant or an array 
            the same size as complex_data with per-pixel values.
            Defaults to 1 which gives uncalibrated values.
        mask : NDArray[np.bool_], optional
            Binary image which is ones over the region of interest.
            Defaults to all ones.

        Returns
        -------
        NDArray[np.float64]
            Range profile array.
        """
        # Handle default parameters
        if oversample_ratio is None:
            oversample_ratio = np.array([1, 1])
        if cal_sf is None:
            cal_sf = 1
        if mask is None:
            mask = np.ones_like(complex_data, dtype=bool)

        # Apply shape mask to rectangular data
        if complex_data.ndim == 3:
            filtimg = complex_data * np.repeat(
                mask[:, :, np.newaxis], complex_data.shape[2], axis=2
            )
        else:
            filtimg = complex_data * mask

        # Handle calibration scale factor for multi-channel data
        if not np.isscalar(cal_sf) and complex_data.ndim == 3:
            cal_sf = np.repeat(cal_sf[:, :, np.newaxis], complex_data.shape[2], axis=2)

        # Compute range profile
        range_profile = (1 / np.prod(oversample_ratio)) * np.sum(
            cal_sf * np.abs(filtimg) ** 2, axis=0
        )

        # Format output
        if range_profile.ndim == 1:
            range_profile = range_profile.reshape(-1, 1)  # Ensure in first dimension
        else:
            range_profile = np.squeeze(range_profile)  # For multi-channel data

        return range_profile

    def rcs_compute(
        self, 
        complex_data: NDArray[np.complex128], 
        oversample_ratio: Optional[Union[List[float], NDArray[np.float64]]] = None, 
        cal_sf: Optional[Union[float, NDArray[np.float64]]] = None, 
        mask: Optional[NDArray[np.bool_]] = None
    ) -> Union[float, NDArray[np.float64]]:
        """
        Compute area-based calibrated RCS for a region of interest.

        Parameters
        ----------
        complex_data : NDArray[np.complex128]
            Complex valued SAR dataset in the image domain.
            First dimension is azimuth, second range.
            Third dimension could be for multi-channel data.
        oversample_ratio : Union[List[float], NDArray[np.float64]], optional
            Oversample or zeropad factor. Required for calibrated RCS.
            Defaults to [1, 1] which gives uncalibrated values.
        cal_sf : Union[float, NDArray[np.float64]], optional
            Calibration scale factor (linear). Either a constant or an array 
            the same size as complex_data with per-pixel values.
            Defaults to 1 which gives uncalibrated values.
        mask : NDArray[np.bool_], optional
            Binary image which is ones over the region of interest.
            Defaults to all ones.

        Returns
        -------
        Union[float, NDArray[np.float64]]
            Total calibrated RCS of ROI. Returns array for multi-channel data.
        """
        # Handle default parameters
        if oversample_ratio is None:
            oversample_ratio = np.array([1, 1])  # RCS values will be uncalibrated
        else:
            oversample_ratio = np.asarray(oversample_ratio)

        if cal_sf is None:
            cal_sf = 1  # RCS values will be uncalibrated

        if mask is None:
            mask = np.ones_like(complex_data, dtype=bool)

        # Apply shape mask to rectangular data
        if complex_data.ndim == 3:
            filtimg = complex_data * np.repeat(
                mask[:, :, np.newaxis], complex_data.shape[2], axis=2
            )
        else:
            filtimg = complex_data * mask

        # Handle calibration scale factor for multi-channel data
        if not np.isscalar(cal_sf) and complex_data.ndim == 3:
            cal_sf = np.repeat(cal_sf[:, :, np.newaxis], complex_data.shape[2], axis=2)

        # Image domain computation of total RCS
        # The oversample ratio (or zeropad) factor is the ratio between the sum of
        # squared (power detected) samples of an ideal sinc function and the peak
        # of that ideal sinc^2 function
        total_rcs = (1 / np.prod(oversample_ratio)) * np.sum(
            np.sum(cal_sf * np.abs(filtimg) ** 2, axis=0), axis=0
        )

        # Handle multi-channel data
        total_rcs = np.squeeze(total_rcs)

        return total_rcs

    def compute_rcs_figures(
        self, 
        selected_widget: Any, 
        meta_data: Dict[str, Any], 
        geometry: Any, 
        slow_units: str, 
        measure_units: str
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], 
               NDArray[np.float64], str, str]:
        """
        Compute RCS figures for plotting and visualization.
        
        Parameters
        ----------
        selected_widget : Any
            Widget containing the SAR image data and reader.
        meta_data : Dict[str, Any]
            SICD metadata dictionary.
        geometry : Any
            Geometry object defining the region of interest.
        slow_units : str
            Units for slow time axis.
        measure_units : str
            Units for RCS measurements.
            
        Returns
        -------
        Tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], 
              NDArray[np.float64], str, str]
            - slow_data: Slow time RCS data in dB
            - fast_data: Fast time RCS data in dB  
            - slow_x_data: Slow time axis data
            - fast_x_data: Fast time axis data
            - slow_axis_label: Label for slow time axis
            - fast_axis_label: Label for fast time axis
        """
        bounding_box = geometry.get_bbox()
        central_row_col = [
            (bounding_box[1] + bounding_box[3]) / 2,
            (bounding_box[0] + bounding_box[2]) / 2,
        ]

        look_direction = meta_data["SCPCOA"]["SideOfTrack"]

        oversample_ratio = [
            1.0 / (meta_data["Grid"]["Col"]["SS"] * meta_data["Grid"]["Col"]["ImpRespBW"]),
            1.0 / (meta_data["Grid"]["Row"]["SS"] * meta_data["Grid"]["Row"]["ImpRespBW"]),
        ]

        cal_sf = self.get_calibration_scale_factor(meta_data, measure_units)

        row_bounds, col_bounds, mask = _get_polygon_bounds(
            geometry, selected_widget.reader.get_data_size_as_tuple()[0]
        )

        complex_data = selected_widget.reader[
            row_bounds[0] : row_bounds[1], col_bounds[0] : col_bounds[1]
        ]

        # Transpose the complex data to account for MATLAB's column-major vs Python's row-major order
        complex_data = complex_data.T
        mask = mask.T if mask is not None else None

        # If cal_sf is a 2D array, it needs to be transposed too
        if isinstance(cal_sf, np.ndarray) and cal_sf.ndim == 2:
            cal_sf = cal_sf.T

        slow_data, fast_data = self.rcs_st_ft(
            complex_data, look_direction, oversample_ratio, cal_sf, mask, meta_data
        )

        range_data = self.rcs_range_profile(
            complex_data, oversample_ratio, cal_sf, mask
        )
        total_rcs = self.rcs_compute(complex_data, oversample_ratio, cal_sf, mask)

        scale_factor = self.compute_scale_factor(
            meta_data, measure_units, mask, oversample_ratio
        )

        slow_data = 10 * np.log10(slow_data * scale_factor)
        fast_data = 10 * np.log10(fast_data * scale_factor)
        total_rcs = 10 * np.log10(total_rcs * scale_factor)

        relative_azimuth = self.get_reference_azimuth_angle()
        slow_range, slow_axis_label = self.compute_slow_time_axis(
            meta_data, selected_widget, slow_units, central_row_col, relative_azimuth
        )
        fast_range, fast_axis_label = self.compute_fast_time_axis(meta_data)

        # Create axis data for plotting
        slow_x_data = np.linspace(slow_range[0], slow_range[1], len(slow_data))
        fast_x_data = np.linspace(fast_range[0], fast_range[1], len(fast_data))

        return (
            self.ensure_1d_array(slow_data),
            self.ensure_1d_array(fast_data),
            self.ensure_1d_array(slow_x_data),
            self.ensure_1d_array(fast_x_data),
            slow_axis_label,
            fast_axis_label,
        )

    def ensure_1d_array(self, arr: Union[List[Any], NDArray]) -> NDArray:
        """
        Convert array to 1D shape that pyqtgraph expects.
        
        Parameters
        ----------
        arr : Union[List[Any], NDArray]
            The array to convert.
            
        Returns
        -------
        NDArray
            The flattened 1D array.
        """
        arr = np.asarray(arr)
        if arr.ndim > 1:
            return arr.flatten()
        return arr

    def get_calibration_scale_factor(
        self, 
        meta_data: Dict[str, Any], 
        measure_units: str
    ) -> Optional[Union[float, NDArray[np.float64]]]:
        """
        Get calibration scale factor based on desired measurement units.
        
        Parameters
        ----------
        meta_data : Dict[str, Any]
            Metadata dictionary containing Radiometric information.
        measure_units : str
            Units for the measurements. Valid options:
            - 'Pixel Power': Raw pixel power
            - 'RCS': Radar cross section
            - 'σ₀': Sigma naught (backscattering coefficient)
            - 'β₀': Beta naught (radar brightness)  
            - 'γ₀': Gamma naught (backscattering coefficient normalized by projected area)
            
        Returns
        -------
        Optional[Union[float, NDArray[np.float64]]]
            The calibration scale factor, or None if invalid units provided.
            
        Raises
        ------
        ValueError
            If invalid measurement units are provided.
        """
        if measure_units == "Pixel Power":
            cal_sf = 1.0
        elif measure_units == "RCS":
            cal_sf = meta_data["Radiometric"]["RCSSFPoly"]["Coefs"][0][0]
        elif measure_units == "σ\u2080":
            cal_sf = meta_data["Radiometric"]["SigmaZeroSFPoly"]["Coefs"][0][0]
        elif measure_units == "β\u2080":
            cal_sf = meta_data["Radiometric"]["BetaZeroSFPoly"]["Coefs"][0][0]
        elif measure_units == "γ\u2080":
            cal_sf = meta_data["Radiometric"]["GammaZeroSFPoly"]["Coefs"][0][0]
        else:
            raise ValueError(f"Invalid measurement units: {measure_units}")
        
        return cal_sf

    def compute_scale_factor(
        self, 
        meta_data: Dict[str, Any], 
        units: str, 
        mask: NDArray[np.bool_], 
        oversample_ratio: Union[List[float], NDArray[np.float64]]
    ) -> float:
        """
        Compute scale factor based on measurement type.
        
        Parameters
        ----------
        meta_data : Dict[str, Any]
            Metadata dictionary containing Grid and SCPCOA information.
        units : str
            Units for the measurements. Valid options:
            - 'RCS': Radar cross section
            - 'σ₀': Sigma naught (normalized by ground area)
            - 'β₀': Beta naught (normalized by area)
            - 'γ₀': Gamma naught (normalized by projected area)
            - 'Pixel Power': Raw pixel power
        mask : NDArray[np.bool_]
            Binary image which is ones over the region of interest.
        oversample_ratio : Union[List[float], NDArray[np.float64]]
            Oversample or zeropad factor.
            
        Returns
        -------
        float
            The computed scale factor.
            
        Raises
        ------
        ValueError
            If unknown measurement type is provided.
        """
        # Check for and compute range weighting factor
        if "WgtFunct" in meta_data["Grid"]["Row"]:
            rng_wgt = np.array(meta_data["Grid"]["Row"]["WgtFunct"])
            rng_wght_f = np.mean(rng_wgt**2) / (np.mean(rng_wgt) ** 2)
        else:
            # If no weight in metadata, assume uniform weighting
            rng_wght_f = 1.0

        # Check for and compute azimuth weighting factor
        if "WgtFunct" in meta_data["Grid"]["Col"]:
            az_wgt = np.array(meta_data["Grid"]["Col"]["WgtFunct"])
            az_wght_f = np.mean(az_wgt**2) / (np.mean(az_wgt) ** 2)
        else:
            # If no weight in metadata, assume uniform weighting
            az_wght_f = 1.0

        # Compute area with weighting factors
        area_sp = (
            np.sum(mask)
            * meta_data["Grid"]["Row"]["SS"]
            * meta_data["Grid"]["Col"]["SS"]
            * (rng_wght_f * az_wght_f)
        )

        # Compute scale factor based on measurement type
        if units == "RCS":
            # No weighting compensation here since totalRCS was computed
            # with weighting, although slow/fast-time curves removed
            # weighting (but were then scaled appropriately).
            scale_factor = 1.0

        elif units == "σ\u2080":
            # Normalize by ground area if sigma-0 requested
            scale_factor = np.cos(np.radians(meta_data["SCPCOA"]["SlopeAng"])) / area_sp

        elif units == "β\u2080":
            scale_factor = 1.0 / area_sp

        elif units == "γ\u2080":
            slope_ang = meta_data["SCPCOA"]["SlopeAng"]
            graze_ang = meta_data["SCPCOA"]["GrazeAng"]
            scale_factor = np.cos(np.radians(slope_ang)) / (
                np.sin(np.radians(graze_ang)) * area_sp
            )

        elif units == "Pixel Power":
            # Raw pixel power
            scale_factor = np.prod(oversample_ratio) / np.sum(mask)

        else:
            raise ValueError(f"Unknown measurement type: {units}")

        return scale_factor