import math
from numpy.typing import NDArray
import pyqtgraph as pg
from typing import List, Dict, Tuple, Optional, Union, Any, Callable, TypeVar, Type, cast, Set
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QMainWindow,
    QDockWidget,
    QGridLayout,
    QTabWidget,
    QLabel,
    QToolBar,
    QFileDialog,
    QColorDialog,
    QListWidget,
    QStatusBar,
    QComboBox,
    QMenu,
    QMenuBar,
    QTableWidgetItem,
    QTableWidget,
    QColorDialog,
    QSizePolicy,
    QAbstractItemView,
    QListWidgetItem,
    QInputDialog,
    QVBoxLayout
)

from PySide6.QtGui import (
    QPalette,
    QColor,
    QPixmap,
    QMouseEvent,
    QPen,
    QAction,
    QActionGroup,
    QKeySequence
)

from PySide6.QtCore import (
    Qt,
    QDir,
    QFile,
    QCoreApplication,
    QMetaObject,
    Signal,
    QModelIndex,
    QDirIterator,
    QEvent,
    QRectF
)

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.metaicon.view import View as MetaIconWidget
from sarpy_apps.apps.PySide_tools.apertureTool.src.PyAperture.aperture_ui.ui_aperture_tool import Ui_ApertureTool

pg.setConfigOptions(imageAxisOrder="row-major")  # needed to display image properly


class ApertureViewer(QDockWidget, Ui_ApertureTool):
    """
    Main viewer widget for the SAR Aperture Tool.
    
    This class serves as the primary user interface for the SAR Aperture Tool,
    providing visualization widgets for k-space data, filtered images, and
    metadata display. It inherits from QDockWidget to integrate with the
    main application window and Ui_ApertureTool for the UI layout.
    
    The viewer contains three main display areas:
    1. K-space (phase history) visualization
    2. Filtered image display after IFFT
    3. Metadata icon display with directional information
    
    Attributes
    ----------
    phase_history_view : KSpaceViewWidget
        Widget for displaying k-space (phase history) data
    filtered_view : FilteredViewWidget
        Widget for displaying filtered spatial domain images
    aperture_meta_icon : ApertureMetaIconWidget
        Widget for displaying metadata as visual icons
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the ApertureViewer.
        
        Sets up the UI components and creates the main visualization widgets
        for k-space display, filtered image display, and metadata visualization.
        
        Parameters
        ----------
        parent : Optional[QWidget], optional
            Parent widget, by default None
        """
        QDockWidget.__init__(self, parent)
        self.setupUi(self)
        
        # setup fft view
        self.phase_history_view = KSpaceViewWidget() # after FFT is applied
        self.layout_fft.addWidget(self.phase_history_view)

        # setup animation view
        self.filtered_view = FilteredViewWidget() # this is post IFFT
        self.layout_animation.addWidget(self.filtered_view)

        # setup metaicon
        self.aperture_meta_icon = ApertureMetaIconWidget()
        self.aperture_meta_icon.horizontalFrame.hide()
        self.meta_icon_layout.addWidget(self.aperture_meta_icon.content_frame)

    def preferred_area(self) -> Qt.DockWidgetArea:
        """
        Get the preferred dock area for this widget.
        
        Returns
        -------
        Qt.DockWidgetArea
            The preferred dock area (left side)
        """
        return Qt.LeftDockWidgetArea
    
    def setup_stylesheets(self) -> None:
        """
        Apply custom stylesheets to the UI components.
        
        Sets up visual styling for the major group boxes and metadata icon
        to provide a consistent and professional appearance.
        """
        self.aperture_meta_icon.content_frame.setStyleSheet(ApertureStyleSheet.meta_icon())
        self.animationGroupBox.setStyleSheet(ApertureStyleSheet.major_group_box(self.animationGroupBox.objectName()))
        self.processingGroupBox.setStyleSheet(ApertureStyleSheet.major_group_box(self.processingGroupBox.objectName()))
        self.exportGroupBox.setStyleSheet(ApertureStyleSheet.major_group_box(self.exportGroupBox.objectName()))
        self.metaIconGroupBox.setStyleSheet(ApertureStyleSheet.major_group_box(self.metaIconGroupBox.objectName()))


class KSpaceROI(pg.RectROI):
    """
    Custom rectangular ROI for k-space selection.
    
    This class extends pyqtgraph's RectROI to provide specialized functionality
    for selecting regions in k-space (phase history) data. It includes boundary
    constraints and signal emission for ROI changes.
    
    Signals
    -------
    roi_changed_finished_signal : Signal
        Emitted when ROI changes are complete, passes the ROI object
    
    Attributes
    ----------
    maxBounds : QRectF
        Maximum allowable bounds for the ROI
    """
    
    roi_changed_finished_signal = Signal(object, name="roi_changed_finished_signal")
    
    def __init__(self, pos: List[float], size: List[float]) -> None:
        """
        Initialize the k-space ROI.
        
        Creates a rectangular ROI with white border styling and connects
        the region change signal to the finished handler.
        
        Parameters
        ----------
        pos : List[float]
            Initial position [x, y] of the ROI
        size : List[float]
            Initial size [width, height] of the ROI
        """
        super().__init__(pos=pos, size=size)
        self.sigRegionChanged.connect(self.roi_changed_finished)
        self.setPen(pg.mkPen(color='white', width=2, style=Qt.SolidLine))

    def set_boundary(self, boundary: List[int]) -> None:
        """
        Set the allowable bounds for the ROI and center it.
        
        Configures the maximum bounds for the ROI to match the valid k-space
        region (excluding spectral leakage areas) and centers the ROI within
        these bounds.
        
        Parameters
        ----------
        boundary : List[int]
            Boundary limits as [y_start, x_start, y_end, x_end]
        """
        y_start, x_start, y_end, x_end = boundary
        width = x_end - x_start
        height = y_end - y_start

        self.maxBounds = QRectF(x_start, y_start, width, height)
        self.setSize(size=(width, height))
        self.setPos(x_start, y_start)
        
    def roi_changed_finished(self) -> None:
        """
        Handle completion of ROI changes.
        
        Emits the roi_changed_finished_signal when the user finishes
        modifying the ROI. This signal can be used to trigger processing
        updates with debouncing for better performance.
        
        Notes
        -----
        TODO: Add debounce functionality to prevent lag on larger selections.
        """
        self.roi_changed_finished_signal.emit(self)


class KSpaceViewWidget(pg.ImageView):
    """
    Widget for displaying k-space (phase history) data.
    
    This class extends pyqtgraph's ImageView to provide specialized visualization
    for SAR k-space data. It includes colormap configuration and utility methods
    for getting view parameters needed for ROI positioning.
    
    Attributes
    ----------
    _color_map : pg.colormap
        Colormap used for displaying k-space data (jet colormap)
    """
    
    def __init__(self) -> None:
        """
        Initialize the k-space view widget.
        
        Sets up the image view with a jet colormap and hides unnecessary
        UI buttons for a cleaner interface.
        """
        super().__init__()
        self._color_map = pg.colormap.get('jet', source='matplotlib')
        self.setColorMap(self._color_map)

        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()

    def get_color_map(self) -> pg.colormap:
        """
        Get the current colormap.
        
        Returns
        -------
        pg.colormap
            The colormap currently used for display
        """
        return self._color_map

    def get_center_coords(self) -> List[float]:
        """
        Get the center coordinates of the current view.
        
        Calculates the center point of the visible area in data coordinates,
        which is useful for positioning ROIs and other overlays.
        
        Returns
        -------
        List[float]
            Center coordinates as [x, y] in data space
        """
        center_coords = [
            self.getView().viewRect().center().x(),
            self.getView().viewRect().center().y(),
        ]
        return center_coords
    
    def get_view_size_ratio(self) -> float:
        """
        Get a size ratio based on the current view range.
        
        Calculates a representative size based on the current view range,
        which is useful for sizing ROIs appropriately relative to the
        visible area.
        
        Returns
        -------
        float
            Size ratio based on the minimum dimension of the view range,
            divided by 4 for reasonable ROI sizing
        """
        view_range = self.getView().viewRange()

        size_ratio = (
            min(
                view_range[0][1] - view_range[0][0], view_range[1][1] - view_range[1][0]
            )
            // 4
        )
        return size_ratio


class FilteredViewWidget(pg.ImageView):
    """
    Widget for displaying filtered spatial domain images.
    
    This class extends pyqtgraph's ImageView to display the results of
    inverse FFT operations on selected k-space regions. It provides a
    clean interface for viewing the filtered SAR images.
    """
    
    def __init__(self) -> None:
        """
        Initialize the filtered view widget.
        
        Sets up the image view and hides unnecessary UI buttons for
        a streamlined display interface.
        """
        super().__init__()

        self.ui.roiBtn.hide()
        self.ui.menuBtn.hide()


class ApertureMetaIconWidget(MetaIconWidget):
    """
    Widget for displaying SAR metadata as visual icons.
    
    This class extends the base MetaIconWidget to provide specialized
    visualization of SAR metadata including directional arrows for
    north, layover, shadow, multipath angles, and side-of-track indicators.
    
    The visualization uses color-coded arrows to represent different
    geometric relationships in the SAR collection geometry.
    """
    
    def __init__(self) -> None:
        """
        Initialize the aperture metadata icon widget.
        
        Sets up the base metadata visualization widget for displaying
        SAR-specific metadata as visual icons.
        """
        super().__init__()

    def display_metaicon(self, metaData: List[Union[str, float]]) -> None:
        """
        Display relevant metadata information in a transparent metaicon window.

        Creates a visual representation with directional arrows using the provided metadata.
        The visualization includes:
        - North (Green arrow)
        - Layover Angle (Orange arrow)
        - Shadow Angle (Blue arrow)
        - Multipath Angle (Red arrow)
        - Yellow arrow indicating side of track (left/right)
        
        Also populates upper and lower information tables with relevant metadata values.

        Parameters
        ----------
        metaData : List[Union[str, float]]
            A list containing metadata values where:
            - metaData[0:4]: Values for the upper table
            - metaData[4:9]: Values for the lower table
            - metaData[9:13]: Angular positions for the directional arrows (in degrees)
            - metaData[13]: Side of track indicator ('L' for left, 'R' for right)

        Notes
        -----
        The arrows are positioned using polar coordinates and colored according to:
        - Green (#8ED15A): North direction
        - Orange (#FF8C00): Layover angle
        - Blue (#00A6FB): Shadow angle
        - Red (#FF031C): Multipath angle
        - Yellow (#FFFF00): Side of track direction
        
        Table column widths are automatically adjusted based on the font metrics
        to accommodate up to 6-digit values (0-360 degrees with 2 decimal places).
        """
        self.metaicon_plot.clear()

        # Green - North direction
        a1 = pg.ArrowItem(angle=-metaData[9]+90+180, tipAngle=30, baseAngle=0, headLen=15, tailLen=50, tailWidth=2, pen=None, brush='#8ED15A', pxMode=False)
        a1.setPos(65*math.cos(math.radians(-metaData[9]+90)), 65*math.sin(math.radians(-metaData[9]+90)))
        
        # Orange - Layover angle
        a2 = pg.ArrowItem(angle=-metaData[10]+90+180, tipAngle=30, baseAngle=0, headLen=15, tailLen=50, tailWidth=2, pen=None, brush='#FF8C00', pxMode=False)
        a2.setPos(65*math.cos(math.radians(-metaData[10]+90)), 65*math.sin(math.radians(-metaData[10]+90)))
        
        # Blue - Shadow angle
        a3 = pg.ArrowItem(angle=-metaData[11]+90+180, tipAngle=30, baseAngle=0, headLen=15, tailLen=50, tailWidth=2, pen=None, brush='#00A6FB', pxMode=False)
        a3.setPos(65*math.cos(math.radians(-metaData[11]+90)), 65*math.sin(math.radians(-metaData[11]+90)))
        
        # Red - Multipath angle
        a4 = pg.ArrowItem(angle=-metaData[12]+90+180, tipAngle=30, baseAngle=0, headLen=15, tailLen=50, tailWidth=2, pen=None, brush='#FF031C', pxMode=False)
        a4.setPos(65*math.cos(math.radians(-metaData[12]+90)), 65*math.sin(math.radians(-metaData[12]+90)))
        
        # Yellow - Side of track indicator
        if metaData[13] == 'L':
            a5 = pg.ArrowItem(angle=0, tipAngle=30, baseAngle=0, headLen=15, tailLen=95, tailWidth=2, pen=None, brush='#FFFF00', pxMode=False)
            a5.setPos(-55, -75)
        else:
            a5 = pg.ArrowItem(angle=180, tipAngle=30, baseAngle=0, headLen=15, tailLen=95, tailWidth=2, pen=None, brush='#FFFF00', pxMode=False)
            a5.setPos(55, -75)

        # Add text labels
        side_of_track_text = pg.TextItem(metaData[13], color='#FFFF00')
        side_of_track_text.setParentItem(a5)

        northText = pg.TextItem("N", color='#8ED15A')
        northText.setParentItem(a1)

        # Helper function to format values with labels and degree symbols
        def format_labeled_value(value):
            if isinstance(value, str) and ':' in value:
                label, angle_part = value.split(':', 1)
                # Remove degree symbol and convert to float
                angle_str = angle_part.replace('°', '')
                try:
                    angle_float = float(angle_str)
                    return f"{label}:{angle_float:.1f}°"
                except ValueError:
                    return value  # Return original if conversion fails
            else:
                # Handle non-labeled numeric values
                try:
                    return f"{float(value):.1f}"
                except (ValueError, TypeError):
                    return str(value)

        # Populate data tables with decimal formatting
        self.upper_table.item(0, 0).setText(str(metaData[0]))
        self.upper_table.item(1, 0).setText(str(metaData[1]))
        self.upper_table.item(2, 0).setText(str(metaData[2]))
        self.upper_table.item(3, 0).setText(str(metaData[3]))

        self.lower_table.item(0, 0).setText(format_labeled_value(metaData[4]))
        self.lower_table.item(1, 0).setText(format_labeled_value(metaData[5]))
        self.lower_table.item(2, 0).setText(format_labeled_value(metaData[6]))
        self.lower_table.item(3, 0).setText(format_labeled_value(metaData[7]))
        self.lower_table.item(4, 0).setText(format_labeled_value(metaData[8]))

        # Auto-size table columns
        char_width = self.upper_table.fontMetrics().horizontalAdvance('9') 
        padding = 100 # padding for comfortable reading
        col_width = char_width * 6 + padding # accommodate 6 digits (0-360.00)
        self.upper_table.setColumnWidth(0, col_width)
        self.lower_table.setColumnWidth(0, col_width)

        # Add all arrows to the plot
        self.metaicon_plot.addItem(a1)
        self.metaicon_plot.addItem(a2)
        self.metaicon_plot.addItem(a3)
        self.metaicon_plot.addItem(a4)
        self.metaicon_plot.addItem(a5)


class UiLoader(QUiLoader):
    """
    Custom UI loader for loading Qt UI files with custom widgets.
    
    This class extends PySide6.QtUiTools.QUiLoader to provide enhanced
    functionality for loading UI files generated from Qt Designer while
    supporting custom widget registration and base instance connection.
    
    Attributes
    ----------
    baseinstance : Optional[QWidget]
        The instance to set as the parent for all loaded widgets
    customWidgets : Optional[Dict[str, Type]]
        Dictionary mapping widget class names to their types for custom widgets
    """

    def __init__(self, baseinstance: Optional[QWidget], customWidgets: Optional[Dict[str, Type]] = None) -> None:
        """
        Initialize the UI loader.
        
        Sets up the UI loader with optional base instance connection and
        custom widget registration capabilities.
        
        Parameters
        ----------
        baseinstance : Optional[QWidget]
            The instance to set as the parent for all widgets, allows
            connecting loaded UI to existing class instances
        customWidgets : Optional[Dict[str, Type]], optional
            Dictionary of custom widgets to register with the loader,
            maps widget class names to their types, by default None
        """
        QUiLoader.__init__(self, baseinstance)
        self.baseinstance = baseinstance
        self.customWidgets = customWidgets


def load_ui(uifile: str, baseinstance: Optional[QWidget] = None, 
            customWidgets: Optional[Dict[str, Type]] = None, 
            workingDirectory: Optional[str] = None) -> QWidget:
    """
    Load a Qt Designer UI file and connect it to an existing instance.
    
    This function provides a convenient way to load UI files created with
    Qt Designer and optionally connect them to existing widget instances.
    It supports custom widget registration and working directory specification.
    
    Parameters
    ----------
    uifile : str
        Path to the UI file (.ui file created with Qt Designer)
    baseinstance : Optional[QWidget], optional
        Instance to set as the parent for all widgets, allows the loaded
        UI to be connected to an existing class instance, by default None
    customWidgets : Optional[Dict[str, Type]], optional
        Dictionary of custom widgets to register with the loader,
        maps widget class names to their types, by default None
    workingDirectory : Optional[str], optional
        Working directory for resolving relative paths in the UI file,
        by default None
        
    Returns
    -------
    QWidget
        The loaded UI widget with all connections established
        
    Notes
    -----
    This function automatically calls QMetaObject.connectSlotsByName()
    to establish signal-slot connections based on naming conventions.
    
    Example
    -------
    >>> widget = load_ui("myform.ui", self)
    >>> # The loaded UI is now connected to 'self' as the base instance
    """
    loader = UiLoader(baseinstance, customWidgets)
    # loader.registerCustomWidget(pg.PlotWidget)  # Example custom widget registration
    if workingDirectory is not None:
        loader.setWorkingDirectory(workingDirectory)
    widget = loader.load(uifile)
    QMetaObject.connectSlotsByName(widget)
    return widget


class ApertureStyleSheet:
    """
    Collection of stylesheet definitions for the Aperture Tool UI.
    
    This class provides static methods that return CSS-like stylesheet
    strings for consistent styling across the aperture tool interface.
    The stylesheets define the visual appearance of major UI components.
    """
    
    @staticmethod
    def major_group_box(boxname: str) -> str:
        """
        Generate stylesheet for major group boxes.
        
        Creates a stylesheet string for styling QGroupBox widgets with
        professional appearance including borders, margins, and title styling.
        
        Parameters
        ----------
        boxname : str
            Object name of the group box to style (used for CSS selectors)
            
        Returns
        -------
        str
            CSS stylesheet string for the specified group box
            
        Notes
        -----
        The generated stylesheet includes:
        - 3px solid border using palette colors
        - Bold font for the title
        - Proper margins and padding
        - Title positioning with left alignment and padding
        """
        return '''
            QGroupBox#%s {
                background-color: none;
                border: 3px solid palette(midlight);
                margin-top: 1ex; 
                font: bold;
            }

            QGroupBox#%s::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0px 5px 0px 5px;
            }
        ''' % (boxname, boxname)
    
    @staticmethod
    def meta_icon() -> str:
        """
        Generate stylesheet for the metadata icon display.
        
        Creates a stylesheet for the metadata visualization components
        including the plot widget and data tables with dark theme styling.
        
        Returns
        -------
        str
            CSS stylesheet string for metadata icon components
            
        Notes
        -----
        The stylesheet provides:
        - Black background for the plot widget
        - Dark gray background for tables
        - Blue border for table widgets
        - Professional dark theme appearance
        """
        return ('PlotWidget { background: #000000 }'
                'QTableWidget { background: #1F1F1F }'
                'QTableWidget { border: 2px solid #4B9FC1}')