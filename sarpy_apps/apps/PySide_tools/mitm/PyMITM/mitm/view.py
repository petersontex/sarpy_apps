from PySide6.QtCore import (
    Qt,
    QDir,
    Signal,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QFileDialog,
    QFileDialog,
    QApplication,
    QWidget,
)
from PySide6.QtGui import (
    QIcon,
    QCloseEvent,
)

# from PySide6.QtUiTools import QUiLoader
import os, sys

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.pyui.mitm_mainwindow import \
    Ui_MainWindow
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.tooltips import ToolTips
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils.stylesheet import \
    MITMStyleSheet
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.customwidgets import \
    CustomFileDialog, CustomMessageBox
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.view import View as \
    PlotterView


class View(QMainWindow, Ui_MainWindow):
    """
        The main view application window for MITM.

        Creates the main application window. Sets up the UI components, signal 
        connections, and event handling for the entire application.

        Features include:
        - Area for dockable plot widgets
        - File browser with custom navigation controls
        - Directory breadcrumb navigation
        - Dark/light mode support
        - File open dialog integration

        Attributes
        ----------
        dark_mode : bool
            Tracks the application's current appearance. `True` if dark mode, else `False`.
        directory_buttons : list[QPushButton]
            List of buttons displaying the current directory, and providing
            direct links to each folder making up the current directory path.
        app_started : bool
            Tracks the application's state. Becomes `True` the first time the application is active.

        Methods
        -------
        notify_user_application_is_starting()
            Create and display a message box indicating to the user that the application is starting up.
        change_appearance(dark_mode)
            Change the application's appearance between light and dark mode.
        add_plot_to_gui(new_plot)
            Add the new plot's dockwidget to the application's dock area.
        move_down_directory()
            Navigate down into a subdirectory when a directory is double-clicked in the file tree.
        move_up_directory()
            Navigate up to a parent directory when a directory button is clicked in the navigation bar.
        _add_directory_buttons()
            Create and configure the directory navigation buttons based on the current path.
        handle_app_state_changed()
            Handle application state changes and detect the first activation.

        Signals
        -------
        widget_creation_signal(PlotterController)
            Emits the new PlotterController object when a new one is created.
        widget_interacted_signal(PlotterController)
            Emits the relevant PlotterController object any time that plotter is interacted with.
        widget_changed_signal(PlotterController)
            Emits the new PlotterController object any time the current plotter widget changed.
        widget_closed_signal(PlotterController)
            Emits the relevant PlotterController object any time a plotter widget is closed.
        request_aspect_ratio_signal(PlotterController)
            Emits the relevant PlotterController object any time its aspect ratio is changed.
        window_closed_signal(list, list)
            Emits a list of the sidebar directories when the window is closed.
        application_started_signal(str)
            Emits the name of the file to open (or an empty string) when the application state
            becomes active for the first time.
        open_meta_icon_signal(str)
            Emits the filename of the displayed image when the metaicon button is pressed.
        file_load_requested_signal(str, object, bool)
            Emitted when a plotter is ready for an image to be loaded. Emits the filename, 
            the PlotterController, and a bool indicating whether the file was dropped (True)
            or double-clicked (False).
    """
    widget_creation_signal = Signal(object, name="widget_creation_signal")
    widget_interacted_signal = Signal(object, name="widget_interacted_signal")
    widget_changed_signal = Signal(object, name="widget_changed_signal")
    widget_closed_signal = Signal(object, name="widget_closed_signal")

    request_aspect_ratio_signal = Signal(object, name="request_aspect_ratio_signal")
    window_closed_signal = Signal(list, list, name="window_closed_signal")
    application_started_signal = Signal(object, name="application_started_signal")

    open_meta_icon_signal = Signal(str, name="open_meta_icon_signal")
    file_load_requested_signal = Signal(
        str, object, bool, name="file_load_requested_signal"
    )

    def __init__(
        self, parent: QWidget | None = None, file_open: str | None = None
    ) -> None:
        """
        Initializes the View object.

        The constructor displays a temporary notification during initialization and
        sets up the initial application state, including loading a file if specified
        via command line.

        Parameters
        ----------
        parent : QWidget, optional
            The parent widget. Default is None.
        file_open : str, optional
            Path to a file to open on startup. Default is None.
        """
        msgbox = self.notify_user_application_is_starting()

        QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.resize(1200, 700)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)

        self.directory_buttons = []
        self.dark_mode = False

        # check if there is an initial file to open
        self.file_open = file_open
        if self.file_open and os.path.isfile(self.file_open):
            self.current_directory_path = os.path.dirname(self.file_open)
        else:
            self.current_directory_path = QDir.currentPath()

        self.file_dialog = CustomFileDialog(self.dockWidgetContents_2, Qt.Widget)
        self.file_dialog.setDirectory(self.current_directory_path)
        self.file_dialog.setWindowFlags(self.file_dialog.windowFlags() & ~Qt.Dialog)
        self.file_dialog.setViewMode(QFileDialog.Detail)
        self.file_dialog.setFileMode(
            QFileDialog.ExistingFile
        )  # prevents selecting dirs or > 1 file
        self.file_dialog.setObjectName("file_dialog")
        self.file_dialog.setAcceptDrops(True)
        self.file_dialog.setProperty("showDropIndicator", True)

        self.gridLayout_2.addWidget(self.file_dialog, 0, 0, 1, 1)

        self._add_directory_buttons(self.file_dialog.directory().path().split("/"))

        # Hide unused widgets
        self.plotDockWidgetLeft.hide()
        self.plotDockWidgetRight.hide()
        self.metaIconDock.hide()
        self.controlsWidget.hide()
        self.line.hide()
        self.fileLineEdit.hide()

        # add any tooltips
        self.directoryWidget.setToolTip(ToolTips.directories_buttons())
        self.newPlotButton.setToolTip(ToolTips.add_plot_button())

        # startup signal
        self.app_started = False
        QApplication.instance().applicationStateChanged.connect(
            self.handle_app_state_changed
        )

        msgbox.hide()

    def notify_user_application_is_starting(self) -> CustomMessageBox:
        """
        Display a message box informing the user that the application is starting.

        Creates and configures a custom message box with a title indicating that
        the MITM View is starting up.

        Returns
        -------
        CustomMessageBox
            The displayed message box instance that can be referenced later to
            hide or close the notification when initialization completes.
        """
        titlestr = "   Starting MITM Viewer. Please wait..."
        msg_box = CustomMessageBox()
        msg_box.setWindowModality(Qt.WindowModal)
        msg_box.setWindowTitle(titlestr)
        msg_box.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        msg_box.show()
        return msg_box

    def change_appearance(self, dark_mode: bool):
        """
        Change the application's appearance between light and dark modes.

        Updates the visual appearance of all directory buttons based on the specified mode. 

        Parameters
        ----------
        dark_mode : bool
            Flag indicating whether to use dark mode (True) or light mode (False).
        """
        self.dark_mode = dark_mode

        for button in self.directory_buttons:
            MITMStyleSheet.DirectoryButtons.change_color(button, dark_mode)

    def add_plot_to_gui(self, new_plot: PlotterView) -> None:
        """
        Add the new plot's dock widget to the application's dock area.

        Parameters
        ----------
        new_plot : PlotterViewer
            The dock widget to add.

        """
        self.addDockWidget(Qt.BottomDockWidgetArea, new_plot)

    def move_down_directory(self) -> None:
        """
        Navigate down into a subdirectory when a directory is double-clicked in the file tree.

        Updates the current directory path to the selected directory and adds new
        directory buttons to the navigation bar representing the path hierarchy.
        The last button (representing the current directory) is styled differently
        to indicate it's the active directory.
        """
        self.current_directory_path = self.file_dialog.directory().path()
        self._add_directory_buttons(self.file_dialog.directory().path().split("/"))
        self.directory_buttons[-1].setStyleSheet(
            MITMStyleSheet.DirectoryButtons.get_style_sheet(True, self.dark_mode)
        )

    def move_up_directory(self) -> None:
        """
        Navigate up to a parent directory when a directory button is clicked in the navigation bar.

        Changes the current directory to the selected parent directory based on which
        navigation button was clicked. Updates the file dialog to display the contents
        of the selected directory and applies appropriate styling to the directory buttons,
        highlighting the newly active directory.

        Platform-specific handling is implemented for root directory navigation
        on Windows vs. other operating systems.
        """
        sender = self.sender().text()
        if sender == "":
            new_root_path = "root"
        else:
            new_root_path = (
                self.current_directory_path.split(self.sender().text())[0]
                + self.sender().text()
            )
        if new_root_path == "root":
            if sys.platform == "win32":
                self.file_dialog.setDirectory("My Computer")
            else:
                self.file_dialog.setDirectory("/")
        else:
            self.file_dialog.setDirectory(new_root_path)

        for button in self.directory_buttons:
            button.setStyleSheet(
                MITMStyleSheet.DirectoryButtons.get_style_sheet(False, self.dark_mode)
            )

        self.sender().setStyleSheet(
            MITMStyleSheet.DirectoryButtons.get_style_sheet(True, self.dark_mode)
        )

    def _add_directory_buttons(self, directories: list[str]) -> None:
        """
        Create and configure the directory navigation buttons based on the current path.

        Clears existing directory buttons and rebuilds them according to the provided
        directory path. Handles platform-specific differences between Windows and Linux
        file systems, including special cases for network locations and root directories.
        Sets up event connections for each button and applies appropriate styling,
        with the current directory button highlighted.

        Parameters
        ----------
        directories : list[str]
            List of directory names representing the path hierarchy to display as buttons.
        """
        b = self.directoryWidget.layout().takeAt(0)
        while b:
            b.widget().deleteLater()
            b = self.directoryWidget.layout().takeAt(0)
        self.directory_buttons.clear()

        if sys.platform == "win32":
            if "" in directories:
                # network locations in Windows begin with '//'
                # which results in two empty strings at the start of the list
                directories = list(filter(None, directories))

            if "." in directories:
                # 'My Computer' shows up as '.' if navigated to from within filedialog (Windows)
                directories.remove(".")

            directories.insert(0, "")
        elif sys.platform == "linux" or sys.platform == "linux2":
            directories.insert(0, "/")

        computer_icon = QIcon.fromTheme(QIcon.ThemeIcon.Computer)

        for directory in directories:
            button = QPushButton()
            if directory == "":
                button.setIcon(computer_icon)
            else:
                button.setText(directory)
            button.setStyleSheet(
                MITMStyleSheet.DirectoryButtons.get_style_sheet(False, self.dark_mode)
            )
            self.directoryWidget.layout().addWidget(button)
            button.clicked.connect(self.move_up_directory)
            self.directory_buttons.append(button)

        self.directory_buttons[-1].setStyleSheet(
            MITMStyleSheet.DirectoryButtons.get_style_sheet(True, self.dark_mode)
        )

    def handle_app_state_changed(self, state: Qt.ApplicationState) -> None:
        """
        Handle application state changes and detect the first activation.

        Monitors the application state and emits a signal when the application
        becomes active for the first time. Ignores state changes where the
        application is not becoming active.

        Parameters
        ----------
        state : Qt.ApplicationState
            The new state of the application. Only Qt.ApplicationState.ApplicationActive
            triggers further actions.
        """
        if state != Qt.ApplicationState.ApplicationActive:
            return

        if not self.app_started:
            self.app_started = True
            self.application_started_signal.emit(self.file_open)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Handle application close events.

        Performs cleanup actions when the application is closing, including closing
        the meta-icon widget and emitting a signal with the current sidebar URLs and
        file filters to save application state.

        Parameters
        ----------
        event : QCloseEvent
            The close event object.
        """
        self.window_closed_signal.emit(
            [x.path() + "\n" for x in self.file_dialog.sidebarUrls()],
            self.file_dialog.nameFilters(),
        )
        super().closeEvent(event)
