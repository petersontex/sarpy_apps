import numpy as np
from typing import List, Tuple, Union, Optional, Any, Callable, Dict
from numpy.typing import NDArray
import shapely
import scipy.io
import scipy
from PySide6.QtGui import QColor

from sarpy.annotation.rcs import _get_polygon_bounds
from sarpy.annotation.base import (
    AnnotationFeature,
    FileAnnotationCollection,
)
from sarpy.geometry.geometry_elements import Polygon
from sarpy.geometry.geocoords import wgs_84_norm, geodetic_to_ecf, ecf_to_geodetic
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.canvas import GeometryROI


class Model:
    """
    Data model for annotation operations.

    Handles geometry processing, annotation feature creation, import/export
    operations, and coordinate transformations.

    Attributes
    ----------
    _file_annotation_collection : Optional[FileAnnotationCollection]
        The current file annotation collection.
    _include_voids : bool
        Whether to include void geometries in calculations.
    """

    def __init__(self) -> None:
        """Initialize the model with default settings."""
        self._file_annotation_collection: Optional[FileAnnotationCollection] = None
        self._include_voids: bool = False  # default to false

    def set_include_voids(self, arg: bool) -> None:
        """
        Set whether to include voids in calculations.

        Parameters
        ----------
        arg : bool
            True to include voids, False to exclude them.
        """
        self._include_voids = arg

    def get_include_voids(self) -> bool:
        """
        Get whether voids are included in calculations.

        Returns
        -------
        bool
            True if voids are included, False otherwise.
        """
        return self._include_voids

    def check_for_interior_geometries(
        self,
        get_undecimated_pixel_coordinates: Callable,
        current_geometry: GeometryROI,
        geometries: List[GeometryROI],
    ) -> bool:
        """
        Check if a geometry contains interior geometries.

        Parameters
        ----------
        get_undecimated_pixel_coordinates : Callable
            Function to convert scene coordinates to pixel coordinates.
        current_geometry : Any
            The geometry to check for interior geometries.
        geometries : List[Any]
            List of all geometries to check against.

        Returns
        -------
        bool
            True if the current geometry contains interior geometries, False otherwise.
        """
        interior_geometries: List[Any] = self.get_interior_geometries(
            get_undecimated_pixel_coordinates, current_geometry, geometries
        )
        return len(interior_geometries) > 0

    def get_interior_geometries(
        self,
        get_undecimated_pixel_coordinates: Callable,
        current_geometry: Optional[GeometryROI],
        geometries: List[GeometryROI],
    ) -> List[GeometryROI]:
        """
        Get geometries that are contained within the current geometry.

        Uses Shapely's contains_properly method to determine spatial relationships.

        Parameters
        ----------
        get_undecimated_pixel_coordinates : Callable
            Function to convert scene coordinates to pixel coordinates.
        current_geometry : Optional[Any]
            The geometry to check for interior geometries.
        geometries : List[Any]
            List of all geometries to check against.

        Returns
        -------
        List[Any]
            List of geometries contained within the current geometry.
        """
        interior_geometries: List[Any] = []

        if current_geometry is not None:
            exterior_geometry = current_geometry
            interior_geometries: List[GeometryROI] = []
            for geometry in geometries:
                if geometry == exterior_geometry:
                    continue

                exterior_coords: List[List[int]] = (
                    self.get_pixel_vertex_image_coordinates(
                        get_undecimated_pixel_coordinates, exterior_geometry
                    )
                )
                geometry_coords: List[List[int]] = (
                    self.get_pixel_vertex_image_coordinates(
                        get_undecimated_pixel_coordinates, geometry
                    )
                )

                if shapely.contains_properly(
                    shapely.Polygon(exterior_coords),
                    shapely.Polygon(geometry_coords),
                ):
                    interior_geometries.append(geometry)

        return interior_geometries

    def create_preview_image(
        self,
        reader: Any,
        remap_function: Callable,
        background_color: Union[List[int], Tuple[int, int, int]],
        geometry: GeometryROI,
    ) -> NDArray[np.uint8]:
        """
        Create a preview image of a geometry overlaid on the image data.

        Parameters
        ----------
        reader : Any
            Image data reader object with array-like access.
        remap_function : Callable
            Function to remap image data to displayable format.
        background_color : Union[List[int], Tuple[int, int, int, int]]
            The RGB(A) color for the background.
        geometry : Any
            The geometry to visualize (must have coordinate list).

        Returns
        -------
        NDArray[np.uint8]
            The preview image with the geometry overlaid as RGBA.
        """
        background_color_rgb: List[int] = list(background_color)[:3]

        row_bounds, col_bounds, mask = _get_polygon_bounds(
            geometry, reader.get_data_size_as_tuple()[0]
        )

        data: NDArray[np.float64] = reader[
            row_bounds[0] : row_bounds[1], col_bounds[0] : col_bounds[1]
        ]
        image_data: NDArray[np.uint8] = remap_function(data)

        masked_image_data: NDArray[np.uint8] = np.where(mask, image_data, 0)

        background: NDArray[np.uint8] = np.full(
            (*masked_image_data.shape, 3), background_color_rgb, dtype=np.uint8
        )

        rgba_image: NDArray[np.uint8] = np.zeros(
            (*masked_image_data.shape, 4), dtype=np.uint8
        )

        rgba_image[..., 0] = masked_image_data
        rgba_image[..., 1] = masked_image_data
        rgba_image[..., 2] = masked_image_data
        rgba_image[..., 3] = np.where(mask, 255, 0)

        final_image: NDArray[np.uint8] = background.copy()
        mask_3d: NDArray[np.bool_] = np.expand_dims(rgba_image[..., 3] > 0, axis=-1)
        final_image = np.where(mask_3d, rgba_image[..., :3], final_image)

        return final_image

    def get_size_ratio(self, view_range: List[List[float]]) -> float:
        """
        Calculate the size ratio for geometry creation based on the view range.

        Parameters
        ----------
        view_range : List[List[float]]
            View range as [[x_min, x_max], [y_min, y_max]].

        Returns
        -------
        float
            The calculated size ratio, with a minimum value of 0.25.
        """
        size_ratio: float = (
            min(
                view_range[0][1] - view_range[0][0], view_range[1][1] - view_range[1][0]
            )
            / 4
        )

        if size_ratio < 0.25:  # prevents creating a tiny unselectable geometry
            size_ratio = 0.25

        return size_ratio

    def parse_geojson(
        self, filename: str
    ) -> Tuple[List[List[List[float]]], List[str], List[str]]:
        """
        Parse a GeoJSON file and extract geometries, colors, and names.

        Parameters
        ----------
        filename : str
            Path to the GeoJSON file to parse.

        Returns
        -------
        Tuple[List[List[List[float]]], List[str], List[str]]
            A tuple containing:
            - List of undecimated geo geometries (coordinate lists)
            - List of geometry colors (hex strings)
            - List of geometry names
        """
        file_annotation_collection = FileAnnotationCollection()
        data: FileAnnotationCollection = file_annotation_collection.from_file(filename)

        undecimated_geo_geometries_list: List[List[List[float]]] = []
        geometry_colors: List[str] = []
        geometry_names: List[str] = []

        for feature in data.annotations.features:
            undecimated_geo_geometries_list.append(
                feature.geometry.get_coordinate_list()
            )
            geometry_colors.append(feature.properties.geometry_properties[0].color)
            geometry_names.append(feature.properties.geometry_properties[0].name)

        return undecimated_geo_geometries_list, geometry_colors, geometry_names

    def parse_matlab(
        self, filename: str
    ) -> Tuple[List[List[List[float]]], List[str], List[str]]:
        """
        Parse a MATLAB file and extract geometries, colors, and names.

        Parameters
        ----------
        filename : str
            Path to the MATLAB file to parse.

        Returns
        -------
        Tuple[List[List[List[float]]], List[str], List[str]]
            A tuple containing:
            - List of geometries (coordinate lists)
            - List of geometry colors (hex strings)
            - List of geometry names
        """
        matlab_data: Dict[str, Any] = scipy.io.loadmat(filename)
        geometries: List[List[List[float]]] = []
        geometry_colors: List[str] = []
        geometry_names: List[str] = []

        for i, data in enumerate(matlab_data["shape_struct"].tolist()[0]):
            geo_coords: List[List[float]] = []
            for lat, long, hav in zip(data[3][0], data[3][1], data[3][2]):
                geo_coord: List[float] = [lat, long, hav]
                geo_coords.append(geo_coord)
            geometries.append([geo_coords])
            geometry_colors.append(QColor(data[1][0]).name())
            geometry_names.append(data[0][0])

        return geometries, geometry_colors, geometry_names

    def parse_import(
        self,
        project_ground_to_image_geo: Callable[[List[float], str], NDArray[np.float64]],
        decimation_factor: int,
        filename: str,
    ) -> Tuple[List[List[List[List[float]]]], List[str], List[str]]:
        """
        Parse an imported file based on its extension and extract geometries.

        Parameters
        ----------
        project_ground_to_image_geo : Callable
            Function to project ground coordinates to image coordinates.
        decimation_factor : int
            Factor used for coordinate decimation/scaling.
        filename : str
            Path to the file to parse.

        Returns
        -------
        Tuple[List[List[List[List[float]]]], List[str], List[str]]
            A tuple containing:
            - List of decimated image geometries
            - List of geometry colors (hex strings)
            - List of geometry names

        Notes
        -----
        Supports GeoJSON, JSON, and MATLAB file formats.
        """
        file_exten: str = filename.split(".")[-1]

        if file_exten in ("geojson", "json"):
            undecimated_geo_geometries_list, geometry_colors, geometry_names = (
                self.parse_geojson(filename)
            )
        elif file_exten == "mat":
            undecimated_geo_geometries_list, geometry_colors, geometry_names = (
                self.parse_matlab(filename)
            )
        else:
            raise ValueError(f"Unsupported file extension: {file_exten}")

        decimated_image_geometries_list: List[List[List[List[float]]]] = []

        for geometries in undecimated_geo_geometries_list:
            decimated_image_geometries: List[List[List[float]]] = []
            for geometry in geometries:
                undecimated_image_coords: List[List[float]] = []
                for coord in geometry:
                    undecimated_image_coord: NDArray[np.float64] = (
                        project_ground_to_image_geo(coord, "latlong")
                    )
                    undecimated_image_coords.append(undecimated_image_coord[0].tolist())

                # Coordinate adjustment - seems to work consistently but is somewhat hacky
                # needed to match other legacy tools
                error_adjusted_coords: List[List[float]] = []
                adjustment_factor: float = 0.55
                for coord in undecimated_image_coords:
                    error_adjusted_coords.append(
                        [coord[0] + adjustment_factor, coord[1] + adjustment_factor]
                    )

                decimated_image_coords: List[List[float]] = [
                    [
                        i[1] / decimation_factor,
                        i[0] / decimation_factor,
                    ]
                    for i in error_adjusted_coords
                ]

                decimated_image_geometries.append(decimated_image_coords)
            decimated_image_geometries_list.append(decimated_image_geometries)

        return decimated_image_geometries_list, geometry_colors, geometry_names

    def check_geometry_void(
        self,
        interior_geometry_list: List[List[List[float]]],
        exterior_geometry: List[List[float]],
    ) -> bool:
        """
        Check if a geometry is a void of another geometry.

        Compares coordinate sets to determine if exterior geometry coordinates
        are a subset of any interior geometry coordinates.

        Parameters
        ----------
        interior_geometry_list : List[List[List[float]]]
            List of interior geometries to check against.
        exterior_geometry : List[List[float]]
            The exterior geometry to check.

        Returns
        -------
        bool
            True if the exterior geometry is a void of any interior geometry,
            False otherwise.
        """
        # Flatten interior geometry coordinates and create a set
        flattened_set: set[Tuple[float, float]] = set(
            tuple(coord) for sublist in interior_geometry_list for coord in sublist[1:]
        )
        # Create set from exterior geometry coordinates (skip first if duplicated)
        single_set: set[Tuple[float, float]] = set(
            tuple(coord) for coord in exterior_geometry[1:]
        )

        return single_set.issubset(flattened_set)

    def create_file_annotation_collection(
        self, geometries: List[Any], filename: str
    ) -> FileAnnotationCollection:
        """
        Create a file annotation collection from geometries.

        Parameters
        ----------
        geometries : List[Any]
            List of geometries to include in the collection.
        filename : str
            Name of the image file associated with the collection.

        Returns
        -------
        FileAnnotationCollection
            The created file annotation collection object.
        """
        file_annotation_collection = FileAnnotationCollection(image_file_name=filename)
        include_voids: bool = self.get_include_voids()

        if include_voids:
            interior_geometries: List[List[List[float]]] = []
            for geometry in geometries:
                annotation_feature = geometry.get_annotation_feature_w_voids()
                if annotation_feature and annotation_feature.geometry.inner_rings:
                    for interior_geometry in annotation_feature.geometry.inner_rings:
                        interior_geometries.append(
                            interior_geometry.coordinates.tolist()
                        )

            for geometry in geometries:
                annotation_feature = geometry.get_annotation_feature_w_voids()
                if annotation_feature:
                    exterior_geometry: List[List[float]] = (
                        annotation_feature.geometry.outer_ring.coordinates.tolist()
                    )
                    if not self.check_geometry_void(
                        interior_geometries, exterior_geometry
                    ):
                        file_annotation_collection.add_annotation(annotation_feature)
        else:
            for geometry in geometries:
                annotation_feature = geometry.get_annotation_feature_wo_voids()
                if annotation_feature:
                    file_annotation_collection.add_annotation(annotation_feature)

        return file_annotation_collection

    def export_geometry(
        self,
        project_image_to_ground_geo: Callable[[List[float], str], NDArray[np.float64]],
        filename: str,
        file_annotation_collection: FileAnnotationCollection,
    ) -> None:
        """
        Export geometry to a file.

        Transforms image coordinates to geographic coordinates and saves
        the annotation collection to a GeoJSON file.

        Parameters
        ----------
        project_image_to_ground_geo : Callable
            Function to project image coordinates to ground coordinates.
        filename : str
            Path where the file will be saved.
        file_annotation_collection : FileAnnotationCollection
            The annotation collection containing the geometries to export.
        """
        for feature in file_annotation_collection.annotations.features:
            undecimated_image_geometries: List[List[List[float]]] = (
                feature.geometry.get_coordinate_list()
            )
            undecimated_geo_geometries: List[List[List[float]]] = []

            for idx, geometry in enumerate(undecimated_image_geometries):
                undecimated_geo_coords: List[List[float]] = []
                for coord in geometry:
                    try:
                        undecimated_geo_coord: List[float] = (
                            project_image_to_ground_geo(coord, "PLANE").tolist()
                        )
                    except Exception:
                        undecimated_geo_coord = coord
                    undecimated_geo_coords.append(undecimated_geo_coord)
                undecimated_geo_geometries.append(undecimated_geo_coords)

            # Set outer ring
            feature.geometry.set_outer_ring(undecimated_geo_geometries[0])
            feature.geometry._inner_rings = None

            # Add inner rings
            for geometry in undecimated_geo_geometries[1:]:
                feature.geometry.add_inner_ring(geometry)

        file_annotation_collection.to_file(filename)

    def get_pixel_vertex_image_coordinates(
        self, get_undecimated_pixel_coordinates: Callable, geometry: Any
    ) -> list[list[int]] | list[int]:
        """
        Get pixel vertex coordinates in image space from scene coordinates.

        Parameters
        ----------
        get_undecimated_pixel_coordinates : Callable
            Function to convert scene coordinates to pixel coordinates.
        geometry : Any
            The geometry to get coordinates for (must have getSceneHandlePositions method).

        Returns
        -------
        List[List[int]]
            List of pixel coordinates in image space.
        """
        scene_coordinates: List[Tuple[Any, List[float]]] = (
            geometry.getSceneHandlePositions()
        )
        coords: List[List[float]] = [x[1] for x in scene_coordinates]
        undecimated_pixel_coordinates: List[List[int]] = (
            get_undecimated_pixel_coordinates(coords)
        )
        return undecimated_pixel_coordinates

    def create_geometry(
        self,
        get_undecimated_pixel_coordinates: Callable[
            [List[List[float]]], List[List[int]]
        ],
        exterior_geometry: Optional[Any],
        interior_geometries: List[Any],
    ) -> Optional[Polygon]:
        """
        Create a Polygon geometry from exterior and interior geometries.

        Parameters
        ----------
        get_undecimated_pixel_coordinates : Callable
            Function to convert scene coordinates to pixel coordinates.
        exterior_geometry : Optional[Any]
            The exterior geometry to use as the outer ring.
        interior_geometries : List[Any]
            List of interior geometries to use as inner rings.

        Returns
        -------
        Optional[Polygon]
            The created Polygon geometry, or None if no exterior geometry was provided.
        """
        if exterior_geometry is not None:
            geometry = Polygon()
            exterior_ring_image_coords: List[List[int]] = (
                self.get_pixel_vertex_image_coordinates(
                    get_undecimated_pixel_coordinates, exterior_geometry
                )
            )

            if self.get_polygon_orientation(exterior_ring_image_coords) == "ccw":
                geometry.set_outer_ring(exterior_ring_image_coords)
            else:
                geometry.set_outer_ring(exterior_ring_image_coords[::-1])

            for interior_geometry in interior_geometries:
                interior_ring_image_coords: List[List[int]] = (
                    self.get_pixel_vertex_image_coordinates(
                        get_undecimated_pixel_coordinates, interior_geometry
                    )
                )
                if self.get_polygon_orientation(interior_ring_image_coords) == "cw":
                    geometry.add_inner_ring(interior_ring_image_coords)
                else:
                    geometry.add_inner_ring(interior_ring_image_coords[::-1])
        else:
            geometry = None

        return geometry

    def get_polygon_orientation(self, coords: List[List[float]]) -> str:
        """
        Determine the orientation of a polygon (clockwise or counterclockwise).

        Uses the Jordan curve theorem to determine orientation by finding
        the point with minimum row and maximum column, then calculating
        the cross product of adjacent vectors.

        Parameters
        ----------
        coords : List[List[float]]
            List of coordinate pairs defining the polygon.

        Returns
        -------
        str
            'cw' for clockwise, 'ccw' for counterclockwise.
        """
        coord_rows: List[float] = [coord[0] for coord in coords]
        min_row: float = min(coord_rows)
        min_row_indices: List[int] = [
            index for index, value in enumerate(coord_rows) if value == min_row
        ]

        min_coords: List[List[float]] = [coords[index] for index in min_row_indices]
        coord_cols: List[float] = [coord[1] for coord in min_coords]
        max_col: float = max(coord_cols)
        max_col_indices: List[int] = [
            index for index, value in enumerate(coord_cols) if value == max_col
        ]

        a_ind: int = coords.index(
            [coord_rows[min_row_indices[0]], coord_cols[max_col_indices[0]]]
        )
        a: List[float] = coords[a_ind]

        try:
            b: List[float] = coords[a_ind - 1]
        except IndexError:
            b = coords[-1]

        try:
            c: List[float] = coords[a_ind + 1]
        except IndexError:
            c = coords[0]

        vect_ab: NDArray[np.float64] = np.array(b) - np.array(a)
        vect_ac: NDArray[np.float64] = np.array(c) - np.array(a)

        if np.cross(vect_ab, vect_ac) < 0:
            return "ccw"
        else:
            return "cw"

    def get_related_geometries(
        self,
        get_undecimated_pixel_coordinates: Callable[
            [List[List[float]]], List[List[int]]
        ],
        current_geometry: Any,
        geometries: List[Any],
    ) -> Tuple[Any, List[Any]]:
        """
        Get geometries related to the current geometry.

        Determines if the current geometry is contained within another geometry
        (making it an interior geometry) or if it contains other geometries.

        Parameters
        ----------
        get_undecimated_pixel_coordinates : Callable
            Function to convert scene coordinates to pixel coordinates.
        current_geometry : Any
            The geometry to find related geometries for.
        geometries : List[Any]
            List of all geometries to check against.

        Returns
        -------
        Tuple[Any, List[Any]]
            A tuple containing:
            - The exterior geometry (either the current geometry or its container)
            - List of interior geometries
        """
        for geometry in geometries:
            interior_geometries: List[Any] = self.get_interior_geometries(
                get_undecimated_pixel_coordinates, geometry, geometries
            )

            # Check if the current geometry is one of these interior geometries
            if current_geometry in interior_geometries:
                exterior_geometry = geometry
                break
        else:
            exterior_geometry = current_geometry
            interior_geometries = []

        return exterior_geometry, interior_geometries

    def update_geometry_features(
        self,
        get_undecimated_pixel_coordinates: Callable[
            [List[List[float]]], List[List[int]]
        ],
        exterior_geometry: Any,
        interior_geometries: List[Any],
    ) -> None:
        """
        Update annotation features for geometries with and without voids.

        Parameters
        ----------
        get_undecimated_pixel_coordinates : Callable
            Function to convert scene coordinates to pixel coordinates.
        exterior_geometry : Any
            The exterior geometry to update.
        interior_geometries : List[Any]
            List of interior geometries (voids).
        """
        geometry_w_voids: Optional[Polygon] = self.create_geometry(
            get_undecimated_pixel_coordinates, exterior_geometry, interior_geometries
        )

        geometry_wo_voids: Optional[Polygon] = self.create_geometry(
            get_undecimated_pixel_coordinates, exterior_geometry, []
        )

        annotation_feature_w_voids: AnnotationFeature = self.create_feature(
            geometry_w_voids
        )
        annotation_feature_wo_voids: AnnotationFeature = self.create_feature(
            geometry_wo_voids
        )

        exterior_geometry.set_annotation_feature_w_voids(annotation_feature_w_voids)
        exterior_geometry.set_annotation_feature_wo_voids(annotation_feature_wo_voids)

    def create_feature(self, geometry: Optional[Polygon]) -> AnnotationFeature:
        """
        Create an annotation feature from a geometry.

        Parameters
        ----------
        geometry : Optional[Polygon]
            The geometry to create a feature from.

        Returns
        -------
        AnnotationFeature
            The created annotation feature.
        """
        annotation_feature = AnnotationFeature()
        annotation_feature.geometry = geometry
        return annotation_feature

    def recreate_geometries_after_resize(
        self, geometries: List[Any], decimation_factor: int
    ) -> List[Dict[str, Any]]:
        """
        Process geometries after a resize event.

        Recreates geometries with proper scaling and positions to maintain
        correct visualization after window resize.

        Parameters
        ----------
        geometries : List[Any]
            List of geometries to process.
        decimation_factor : int
            Factor used for coordinate decimation/scaling.

        Returns
        -------
        List[Dict[str, Any]]
            List of processed geometry information dictionaries containing:
            - decimated_coords: scaled coordinates
            - original_color: geometry color
            - original_name: geometry name
            - original_annotation_w_voids: annotation feature with voids
            - original_annotation_wo_voids: annotation feature without voids
        """
        processed_geometries: List[Dict[str, Any]] = []

        # Process each geometry
        for geometry in geometries:
            try:
                # Skip geometries without annotation features
                if (
                    not hasattr(geometry, "get_annotation_feature_wo_voids")
                    or not geometry.get_annotation_feature_wo_voids()
                ):
                    continue

                # Get undecimated coordinates
                annotation_feature = geometry.get_annotation_feature_wo_voids()
                undecimated_pixel_coords: List[List[List[float]]] = (
                    annotation_feature.geometry.get_coordinate_list()
                )

                if not undecimated_pixel_coords or len(undecimated_pixel_coords[0]) < 3:
                    continue

                # Convert to decimated coordinates
                decimated_coords: List[List[float]] = [
                    [
                        i[1] / decimation_factor,
                        i[0] / decimation_factor,
                    ]
                    for i in undecimated_pixel_coords[0]
                ]

                # Remember original properties
                original_color: str = geometry.get_color()
                original_name: str = geometry.get_name()
                original_annotation_w_voids: Any = (
                    geometry.get_annotation_feature_w_voids()
                )
                original_annotation_wo_voids: Any = (
                    geometry.get_annotation_feature_wo_voids()
                )

                # Store processed information for recreating geometry
                processed_geometries.append(
                    {
                        "decimated_coords": decimated_coords,
                        "original_color": original_color,
                        "original_name": original_name,
                        "original_annotation_w_voids": original_annotation_w_voids,
                        "original_annotation_wo_voids": original_annotation_wo_voids,
                    }
                )
            except Exception as e:
                print(f"Error processing geometry: {e}")

        return processed_geometries
