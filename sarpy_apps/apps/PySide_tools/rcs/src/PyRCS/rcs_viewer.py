import warnings
from typing import Any, Dict, List, Optional, Type, Union

import numpy as np
import pyqtgraph as pg
from numpy.typing import NDArray
from PySide6.QtCore import QDir, QEvent, QModelIndex, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColorDialog,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QGridLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QWidget,
)

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.application_extension import \
    Extension, ExtensibleObject
from sarpy_apps.apps.PySide_tools.rcs.src.PyRCS.ui_rcs_tool import Ui_RCSTool

# Configure pyqtgraph for proper image display
pg.setConfigOptions(imageAxisOrder="row-major")


class Viewer(QDockWidget, Ui_RCSTool):
    """
    Main viewer widget for the RCS (radar cross section) tool.
    
    This class serves as the primary user interface component in the MVC architecture
    for the RCS tool. It provides the graphical interface that users interact with
    and emits signals to communicate user actions to the controller.
    
    The viewer contains:
    - RCS measurement unit selection controls
    - Slow time unit selection controls  
    - Plot widgets for displaying RCS profiles
    - Table widget for detailed RCS values
    - Dialog for azimuth angle input
    
    Signals
    -------
    add_geometry_signal : Signal(list)
        Emitted when a new geometry should be added with spawn coordinates.
    voids_toggle_signal : Signal(bool)
        Emitted when the void inclusion toggle state changes.
    app_state_signal : Signal()
        Emitted when the application state changes and UI should be updated.
    """

    # Define signals for communication with controller
    add_geometry_signal = Signal(list, name="add_geometry_signal")
    voids_toggle_signal = Signal(bool, name="voids_toggle_signal")
    app_state_signal = Signal(name="app_state_signal")

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the RCS Viewer.
        
        Sets up the user interface components including plot widgets and
        configures measurement unit labels with Unicode symbols.
        
        Parameters
        ----------
        parent : QWidget, optional
            Parent widget for this dock widget, defaults to None.
        """
        super().__init__(parent)
        self.setupUi(self)

        # Initialize plot widgets for RCS data visualization
        self.rcs_slow_plot_widget = RCSPlotWidget(parent=self)
        self.rcs_slow_plot_view.addWidget(self.rcs_slow_plot_widget)
        
        self.rcs_fast_plot_widget = RCSPlotWidget(parent=self)
        self.rcs_fast_plot_view.addWidget(self.rcs_fast_plot_widget)

        # Set Unicode symbols for measurement units in combo box
        self.rcs_measure_units_combo_box.setItemText(2, "β\u2080")
        self.rcs_measure_units_combo_box.setItemText(3, "γ\u2080")
        self.rcs_measure_units_combo_box.setItemText(4, "σ\u2080")

    def azimuth_reference_angle_dialog(self) -> int:
        """
        Display a dialog for entering a reference azimuth angle.
        
        Opens an input dialog allowing the user to enter an azimuth angle
        between 0 and 180 degrees for use as a reference in calculations.
        
        Returns
        -------
        int
            The reference angle in degrees (0-180), or 0 if user canceled.
        """
        value, ok = QInputDialog.getInt(
            self,
            "Reference Azimuth Angle",  # Dialog title
            "Enter a reference azimuth angle between 0 and 180 degrees.",  # Prompt
            value=0,  # Default value
            minValue=0,  # Minimum value
            maxValue=180,  # Maximum value
        )

        return value if ok else 0


class RCSGeometryTableWidget(Extension):
    """
    Extension for GeometryTableWidget that adds RCS-specific functionality.
    
    This extension adds a column to the geometry table for displaying RCS values
    in various units (RCS, Pixel Power, Beta Zero, Gamma Zero, Sigma Zero).
    It manages the display format and units conversion for RCS data presentation.
    
    Attributes
    ----------
    _rcs_display_units : int
        Index representing current display units:
        0=RCS, 1=PixelPower, 2=BetaZero, 3=GammaZero, 4=SigmaZero
    _units_header : str
        Current header text for the RCS column.
    _column_index : int
        Column index for the RCS data in the table.
    """
    
    def __init__(self) -> None:
        """Initialize RCS table extension with default values."""
        super().__init__()
        self._rcs_display_units: int = 0  # Default to RCS
        self._units_header: str = "RCS"  # Default header
        self._column_index: int = 0  # Will be set during initialization

    def populate_rcs_column(
        self, 
        obj: Any, 
        geometries: List[Any], 
        include_voids: bool
    ) -> None:
        """
        Populate the RCS column with values from geometries.
        
        Parameters
        ----------
        obj : Any
            The table widget object this extension is attached to.
        geometries : List[Any]
            List of geometry objects containing RCS features.
        include_voids : bool
            Whether to include void areas in RCS calculations.
        """
        obj.set_geometries(geometries)
        for i, geometry in enumerate(geometries):
            if include_voids:
                rcs_feature = geometry.get_rcs_feature_w_voids()
            else:
                rcs_feature = geometry.get_rcs_feature_wo_voids()

            # Extract RCS value and convert to dB
            rcs_value = rcs_feature.properties.parameters[self.get_rcs_display_units()].value.mean
            rcs_db = 10 * np.log10(rcs_value)
            
            rcs_item = QTableWidgetItem(f"{rcs_db:.2f}")
            rcs_item.setFlags(rcs_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            obj.setItem(i, 1, rcs_item)

    def init_extension(self, obj: Any) -> None:
        """
        Initialize the extension with the table widget.
        
        Adds an RCS column to the table and sets up the header.
        
        Parameters
        ----------
        obj : Any
            The table widget this extension is attached to.
        """
        # Add RCS column to the table
        obj.setColumnCount(obj.columnCount() + 1)
        obj.add_header(self.get_units_header())
        self._column_index = obj.columnCount()
    
    def duplicate(self) -> 'RCSGeometryTableWidget':
        """
        Create a duplicate of this extension.
        
        Returns
        -------
        RCSGeometryTableWidget
            New extension instance with copied configuration.
        """
        new_ext = RCSGeometryTableWidget()
        new_ext._rcs_display_units = self._rcs_display_units
        new_ext._units_header = self._units_header
        new_ext._column_index = self._column_index
        return new_ext
    
    def set_units_header(self, units_header: str) -> None:
        """
        Set the units header text.
        
        Parameters
        ----------
        units_header : str
            The new header text to display.
        """
        self._units_header = units_header
        
    def get_units_header(self) -> str:
        """
        Get the current units header text.
        
        Returns
        -------
        str
            The current header text.
        """
        return self._units_header
    
    def set_rcs_display_units(self, obj: Any, display_index: int) -> None:
        """
        Set the RCS display units based on the given index.
        
        Updates both the internal units index and the table header to reflect
        the selected measurement type.
        
        Parameters
        ----------
        obj : Any
            The table widget this extension is attached to.
        display_index : int
            Index representing the units:
            0=RCS, 1=PixelPower, 2=BetaZero, 3=GammaZero, 4=SigmaZero
            
        Raises
        ------
        ValueError
            If an invalid display index is provided.
        """
        # Map display index to internal units and header text
        unit_mapping = {
            0: (0, "RCS"),
            1: (1, "PixelPower"), 
            2: (3, "β\u2080"),  # Beta zero
            3: (4, "γ\u2080"),  # Gamma zero
            4: (5, "σ\u2080"),  # Sigma zero
        }
        
        if display_index not in unit_mapping:
            raise ValueError(f"Invalid display index {display_index} for RCS geometry table")
        
        self._rcs_display_units, header_text = unit_mapping[display_index]
        self.set_units_header(header_text)
        obj.update_header(self.get_units_header(), self._column_index - 1)
    
    def get_rcs_display_units(self) -> int:
        """
        Get the current RCS display units index.
            
        Returns
        -------
        int
            The current internal units index for parameter access.
        """
        return self._rcs_display_units


class RCSTableWidget(QTableWidget):
    """
    Specialized table widget for displaying detailed RCS values.
    
    This widget displays RCS statistics (mean, std, min, max) for different
    measurement types with context menu support and keyboard shortcuts for
    copying data to the clipboard.
    
    Features:
    - Context menu with copy functionality
    - Ctrl+C keyboard shortcut for copying
    - Automatic formatting of RCS values in linear and dB scales
    - Support for multi-selection copying
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the RCS table widget.
        
        Sets up the table with context menu and copy functionality.
        
        Parameters
        ----------
        *args : tuple
            Positional arguments passed to QTableWidget.
        **kwargs : dict
            Keyword arguments passed to QTableWidget.
        """
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def show_context_menu(self, pos: Any) -> None:
        """
        Show a context menu for the table at the specified position.
        
        Parameters
        ----------
        pos : QPoint
            Position where the context menu was requested.
        """
        context_menu = QMenu(self)
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_selection)
        context_menu.addAction(copy_action)
        context_menu.exec_(self.mapToGlobal(pos))

    def keyPressEvent(self, event: QEvent) -> None:
        """
        Handle key press events for the table.
        
        Implements copy functionality for Ctrl+C and passes other events
        to the parent class.
        
        Parameters
        ----------
        event : QKeyEvent
            The key press event to handle.
        """
        if event.matches(QKeySequence.StandardKey.Copy):
            self.copy_selection()
        else:
            super().keyPressEvent(event)

    def copy_selection(self) -> None:
        """
        Copy selected table cells to the system clipboard.
        
        Formats the selected data as tab-separated text with rows separated
        by newlines, suitable for pasting into spreadsheet applications.
        """
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return

        copied_text = []
        for sel_range in selected_ranges:
            for row in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                row_data = []
                for col in range(sel_range.leftColumn(), sel_range.rightColumn() + 1):
                    item = self.item(row, col)
                    if item is not None:
                        row_data.append(item.text())
                    else:
                        row_data.append("")
                copied_text.append("\t".join(row_data))

        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(copied_text))

    def populate_rcs_table(self, rcs_feature: Any) -> None:
        """
        Populate the table with RCS feature data.
        
        Fills the table with RCS statistics for different measurement types,
        displaying both linear and dB values where appropriate.
        
        Parameters
        ----------
        rcs_feature : Any
            RCS feature object containing measurement parameters and statistics.
        """
        # Skip the third parameter (index 2) to match MATLAB implementation
        table_params = [
            item for i, item in enumerate(rcs_feature.properties.parameters) if i != 2
        ]

        def format_value(value: Optional[float], is_db: bool = False) -> str:
            """Format a value for display, optionally converting to dB."""
            if value is None:
                return ""
            if is_db:
                return f"{10 * np.log10(value):.2f}"
            return f"{value:.2f}"

        for i, parameters in enumerate(table_params):
            self.setItem(i, 0, QTableWidgetItem(str(parameters.polarization)))
            self.setItem(
                i, 1, QTableWidgetItem(format_value(parameters.value.mean, is_db=True))
            )
            self.setItem(i, 2, QTableWidgetItem(format_value(parameters.value.mean)))
            self.setItem(i, 3, QTableWidgetItem(format_value(parameters.value.std)))
            self.setItem(i, 4, QTableWidgetItem(format_value(parameters.value.min)))
            self.setItem(i, 5, QTableWidgetItem(format_value(parameters.value.max)))

    def update_headers(self) -> None:
        """
        Update table headers with measurement type labels.
        
        Sets the number of rows and vertical header labels for different
        RCS measurement types.
        """
        self.setRowCount(5)
        self.setVerticalHeaderLabels(
            ["RCS", "Pixel Power", "β\u2080", "γ\u2080", "σ\u2080"]
        )


class RCSGeometryROI(Extension):
    """
    Extension for GeometryROI that adds RCS-specific functionality.
    
    This extension stores RCS features calculated with and without void areas,
    allowing geometries to maintain both versions for different analysis needs.
    
    Attributes
    ----------
    _rcs_feature_w_voids : Any
        RCS feature calculated including void areas.
    _rcs_feature_wo_voids : Any  
        RCS feature calculated excluding void areas.
    _rcs_display_value : str
        String representation of RCS value for display purposes.
    """
    
    def __init__(self) -> None:
        """Initialize RCS geometry extension with default values."""
        super().__init__()
        self._rcs_feature_w_voids: Optional[Any] = None
        self._rcs_feature_wo_voids: Optional[Any] = None
        self._rcs_display_value: str = "rcs display value?"
        
    def init_extension(self, obj: Any) -> None:
        """
        Initialize the extension with the geometry object.
        
        Parameters
        ----------
        obj : Any
            The geometry object this extension is attached to.
        """
        pass  # No additional initialization needed
        
    def duplicate(self) -> 'RCSGeometryROI':
        """
        Create a duplicate of this RCS geometry extension.
        
        Returns
        -------
        RCSGeometryROI
            New extension instance with copied RCS data.
        """
        new_ext = RCSGeometryROI()
        new_ext._rcs_feature_w_voids = self._rcs_feature_w_voids
        new_ext._rcs_feature_wo_voids = self._rcs_feature_wo_voids
        new_ext._rcs_display_value = self._rcs_display_value
        return new_ext
    
    # RCS-specific methods for managing features
    def set_rcs_feature_wo_voids(self, obj: Any, feature_wo_voids: Any) -> None:
        """
        Set the RCS feature calculated without void areas.
        
        Parameters
        ----------
        obj : Any
            The geometry object this extension is attached to.
        feature_wo_voids : Any
            RCS feature calculated excluding void areas.
        """
        self._rcs_feature_wo_voids = feature_wo_voids
        if hasattr(obj, '_update_geometry_properties'):
            obj._update_geometry_properties(feature_wo_voids)

    def get_rcs_feature_wo_voids(self, obj: Any) -> Any:
        """
        Get the RCS feature calculated without void areas.
        
        Parameters
        ----------
        obj : Any
            The geometry object this extension is attached to.
            
        Returns
        -------
        Any
            RCS feature calculated excluding void areas.
        """
        return self._rcs_feature_wo_voids

    def set_rcs_feature_w_voids(self, obj: Any, feature_w_voids: Any) -> None:
        """
        Set the RCS feature calculated with void areas included.
        
        Parameters
        ----------
        obj : Any
            The geometry object this extension is attached to.
        feature_w_voids : Any
            RCS feature calculated including void areas.
        """
        self._rcs_feature_w_voids = feature_w_voids
        if hasattr(obj, '_update_geometry_properties'):
            obj._update_geometry_properties(feature_w_voids)

    def get_rcs_feature_w_voids(self, obj: Any) -> Any:
        """
        Get the RCS feature calculated with void areas included.
        
        Parameters
        ----------
        obj : Any
            The geometry object this extension is attached to.
            
        Returns
        -------
        Any
            RCS feature calculated including void areas.
        """
        return self._rcs_feature_w_voids

    def get_rcs_display_value(self, obj: Any) -> str:
        """
        Get the RCS display value for UI presentation.
        
        Parameters
        ----------
        obj : Any
            The geometry object this extension is attached to.
            
        Returns
        -------
        str
            RCS display value as a formatted string.
        """
        return self._rcs_display_value


class RCSPlotWidget(pg.GraphicsLayoutWidget):
    """
    Specialized widget for displaying RCS plots with statistical markers.
    
    This widget extends pyqtgraph's GraphicsLayoutWidget to provide RCS-specific
    plotting functionality including:
    - Line plots for RCS profiles
    - Statistical reference lines (mean, min, max)
    - Configurable axes labels and titles
    - Grid display for easier reading
    
    The widget is designed to display both slow-time and fast-time RCS profiles
    with appropriate statistical annotations.
    """
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the RCS plot widget.
        
        Sets up the widget with antialiasing enabled and a default empty plot.
        
        Parameters
        ----------
        *args : tuple
            Positional arguments passed to pg.GraphicsLayoutWidget.
        **kwargs : dict
            Keyword arguments passed to pg.GraphicsLayoutWidget.
        """
        super().__init__(*args, **kwargs)

        pg.setConfigOptions(antialias=True)
        
        # Create default empty plot
        self.default_plot = self.addPlot(title="")
        self.default_plot.showGrid(x=True, y=True)
        self.default_plot.setLabel("bottom", "")
        self.default_plot.setLabel("left", "")
        self.default_plot.plot([], [], pen="b", name="")
        self.addItem(self.default_plot, row=0, col=0)

    def populate_plot(
        self, 
        x_data: NDArray, 
        y_data: NDArray, 
        x_axis_label: str, 
        y_axis_label: str, 
        plot_title: str
    ) -> None:
        """
        Populate the plot with RCS data and statistical markers.
        
        Replaces any existing plot with new data and adds statistical reference
        lines for mean, minimum, and maximum values when appropriate.
        
        Parameters
        ----------
        x_data : NDArray
            X-axis data points (time, frequency, or angle).
        y_data : NDArray
            Y-axis data points (RCS values in dB).
        x_axis_label : str
            Label text for the X-axis.
        y_axis_label : str
            Label text for the Y-axis.
        plot_title : str
            Title text for the plot.
        """
        # Remove existing plot if present
        if self.ci.getItem(0, 0) is not None:
            self.ci.removeItem(self.ci.getItem(0, 0))

        # Create new plot with data
        plot = self.addPlot(title=plot_title)
        plot.showGrid(x=True, y=True)
        plot.setLabel("bottom", x_axis_label)
        plot.setLabel("left", y_axis_label)

        # Plot main data line
        plot.plot(x_data, y_data, pen="b", name=plot_title)

        # Add statistical reference lines for 1D data
        if x_data.ndim == 1:
            # Calculate statistics excluding infinite values
            valid_data = y_data[~np.isinf(y_data)]
            if len(valid_data) > 0:
                avg_value = np.mean(valid_data)
                max_value = np.max(valid_data)
                min_value = np.min(valid_data)

                # Add horizontal statistical reference lines
                plot.addLine(y=avg_value, pen=pg.mkPen("r", style=Qt.PenStyle.DashLine))
                plot.addLine(y=max_value, pen=pg.mkPen("r", style=Qt.PenStyle.DotLine))
                plot.addLine(y=min_value, pen=pg.mkPen("r", style=Qt.PenStyle.DotLine))

                # Add legend for statistical lines
                legend = plot.addLegend()
                legend.addItem(
                    pg.PlotDataItem(pen=pg.mkPen("r", style=Qt.PenStyle.DashLine)), 
                    "Average"
                )
                legend.addItem(
                    pg.PlotDataItem(pen=pg.mkPen("r", style=Qt.PenStyle.DotLine)), 
                    "Min/Max"
                )

        self.addItem(plot, row=0, col=0)


class UiLoader(QUiLoader):
    """
    Custom UI loader for loading Qt Designer UI files.
    
    This class extends PySide6's QUiLoader to support loading UI files
    and connecting them to existing Python instances, enabling separation
    of UI design and business logic.
    
    Attributes
    ----------
    baseinstance : Optional[QWidget]
        The instance to set as parent for loaded widgets.
    customWidgets : Optional[Dict[str, Type]]
        Dictionary mapping custom widget names to their classes.
    """

    def __init__(
        self, 
        baseinstance: Optional[QWidget], 
        customWidgets: Optional[Dict[str, Type]] = None
    ) -> None:
        """
        Initialize the UI loader.
        
        Parameters
        ----------
        baseinstance : Optional[QWidget]
            The instance to set as parent for all loaded widgets.
        customWidgets : Optional[Dict[str, Type]]
            Dictionary of custom widget classes to register with the loader.
        """
        super().__init__(baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets


def load_ui(
    uifile: str, 
    baseinstance: Optional[QWidget] = None, 
    customWidgets: Optional[Dict[str, Type]] = None, 
    workingDirectory: Optional[str] = None
) -> QWidget:
    """
    Load a Qt Designer UI file and connect it to an existing instance.
    
    This function provides a convenient way to load UI files created with
    Qt Designer and integrate them with Python application logic.
    
    Parameters
    ----------
    uifile : str
        Path to the .ui file to load.
    baseinstance : Optional[QWidget]
        Instance to set as parent for all loaded widgets.
    customWidgets : Optional[Dict[str, Type]]
        Dictionary of custom widget classes to register.
    workingDirectory : Optional[str]
        Working directory for resolving relative paths in the UI file.
        
    Returns
    -------
    QWidget
        The loaded UI widget ready for use.
        
    Notes
    -----
    This function automatically connects slots by name using Qt's
    QMetaObject.connectSlotsByName() method.
    """
    loader = UiLoader(baseinstance, customWidgets)
    
    if workingDirectory is not None:
        loader.setWorkingDirectory(workingDirectory)
        
    widget = loader.load(uifile)
    
    # Automatically connect slots by name
    from PySide6.QtCore import QMetaObject
    QMetaObject.connectSlotsByName(widget)
    
    return widget