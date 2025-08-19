from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QDockWidget
from PySide6.QtGui import QAction
import sys, subprocess

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.controller import Controller \
    as MITMController
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.subapplication import \
    AbstractApp
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.view import View as MITMView
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.utils import styleloader
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.pyui.wrapper import Ui_MainWindow


class Controller:
    """
    A Wrapper class for MITM. Provides an interface between MITM and subapplications.

    Main controller class that connects the viewer UI and data model for Wrapper.

    Attributes
    ----------
    model : Model
        Container for application logic.
    viewer : View
        Container for application GUI.
    mitm_controller : MITMController
        Main MITM application.
    apps : dict{ str : AbstractApp }
        Dictionary of subapplications. Lookup is by application name.

    Methods
    -------
    setup_apps(apps)
        Setup UI and data for each app in list
    """

    def __init__(self, apps: list = []) -> None:
        """
        Constructs a Controller object.

        Parameters
        -----------
        apps : list
            list of MITM subapplications to set up.
        """
        self.apps = {}
        self.mitm_controller = MITMController(sys.argv)
        self.model = Model()
        self.viewer = View(self.mitm_controller.viewer)
        self.viewer.appearance_changed_signal.connect(
            self.mitm_controller.change_appearance
        )
        self.viewer.window_closing_signal.connect(self.mitm_controller.viewer.close)
        self.viewer.help_action.triggered.connect(self.model.open_help_pdf)
        self.viewer.load_app_signal.connect(self.load_app_by_name)
        self.viewer.offload_app_signal.connect(self.offload_app_by_name)
        self.setup_apps(apps)

    def setup_apps(self, apps: list[AbstractApp]) -> None:
        """
        Setup UI and data for each app in list.

        Creates a new entry in Tools menu for each app.
        Gives each app a copy of mitm_controller and apps dict.
        Obtains reference to each app's QDockWidget.
        Sets up connections to handle when MITM appearance changes and to cleanup app on exit.
        Sets up connections to hide and show app.

        Parameters
        -----------
        apps : list[AbstractApp]
            list of MITM subapplications to set up.
        """
        self.apps = {}

        for app in apps:
            # update dictionaries
            self.apps[app.get_name()] = app

            # give app info
            app.set_mitm_controller(self.mitm_controller)
            app.set_app_dict(self.apps)

            # setup toolbar action
            self.viewer.add_tools_action(app.get_name())

            # setup dock widget
            self.viewer.add_dock_widget(
                app.get_name(), app.get_dock_widget(), app.get_preferred_area()
            )

            # connections
            self.viewer.appearance_changed_signal.connect(app.change_appearance)
            self.viewer.window_closing_signal.connect(app.exit_cleanup)
            self.viewer.connect_app_to_toolbar(app.get_name())

    def load_app_by_name(self, name: str) -> None:
        """
        Call the given app's `load()` method if it currently offloaded.

        Parameters
        ---------
        name : str
            The name of the app to load.
        """
        if not self.apps[name].is_loaded:
            self.apps[name].load()

    def offload_app_by_name(self, name: str) -> None:
        """
        Call the given app's `offload()` method if it is currently loaded.

        Parameters
        ---------
        name : str
            The name of the app to offload.
        """
        if self.apps[name].is_loaded:
            self.apps[name].offload()


class View(QMainWindow, Ui_MainWindow):
    """
    The View class for Wrapper.
    
    Creates a window with a toolbar to provide a GUI for toggling apps and dark mode.

    Attributes
    ----------
    tools_actions : dict{ str : QAction }
        Dictionary of app name to QAction toggling the app's visiblity.
    dock_widgets : dict{ str : QDockWidget }
        Dictionary of app name to QDockWidget providing app GUI.

    Methods
    -------
    add_tools_action(name)
        Set up a new QAction and add it to the Tools menu.
    add_dock_widget(name, dock_widget, preferred_area)
        Add an app's dock widget to the main window by name.
    connect_app_to_toolbar(name)
        Connect an app's dock widget's visibility to the QAction's checkbox and vice versa.
    show_or_hide_app(checked)
        Changes application visibility to follow whether relevant QAction is checked.
    uncheck_tool_application()
        Unchecks an app's QAction when its dock widget is closed..

    Signals
    -------
    appearance_changed_signal(bool)
        Emitted when appearance is changed from light (False) to dark (True) or vice-versa.
    window_closing_signal
        Emitted when the main window is closed.
    load_app_signal(str)
        Emitted when an app's QAction becomes checked to signal that the app should be 
        loaded. Emits the name of the app to load.
    offload_app_signal(str)
        Emitted when an app's QAction becomes unchecked or the app's dock widget is 
        closed. Emits the name of the app to offload.
    """
    appearance_changed_signal = Signal(bool)
    window_closing_signal = Signal()
    load_app_signal = Signal(str)
    offload_app_signal = Signal(str)

    def __init__(self, central_widget: MITMView, parent: QWidget | None = None) -> None:
        """
        Constructs necessary attributes for the View object.

        Parameters
        -----------
        central_widget : MITMView
           MITM View object to set as Wrapper's central widget.
        """
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.setDockOptions(
            QMainWindow.AnimatedDocks
            | QMainWindow.AllowNestedDocks
            | QMainWindow.AllowTabbedDocks
        )
        self.setWindowTitle("MITM Viewer")
        self.setCentralWidget(central_widget)

        # start in light mode
        self.change_appearance(False)
        dark_action = QAction("Dark Mode", self)
        dark_action.setEnabled(True)
        dark_action.setCheckable(True)

        # help menu button
        self.help_action = QAction("Help", self)
        self.help_action.setEnabled(True)
        self.help_action.setCheckable(False)

        self.menuMenu_Button.addAction(dark_action)
        self.menuMenu_Button.addAction(self.help_action)
        dark_action.toggled.connect(self.change_appearance)

        self.tools_actions = {}
        self.dock_widgets = {}

    def change_appearance(self, checked: bool) -> None:
        """
        Change the appearance of the app from light to dark or vice versa.

        Parameters
        -----------
        checked : bool
            True if dark_mode, else False.
        """
        if checked:
            styleloader.dark(QApplication.instance())
        else:
            styleloader.light(QApplication.instance())
        self.appearance_changed_signal.emit(checked)

    def add_tools_action(self, name: str) -> None:
        """
        Set up a new QAction and add it to the Tools menu.

        Parameters
        -----------
        name : str
            Name of app.
        """
        self.tools_actions[name] = QAction(name, self)
        self.tools_actions[name].setCheckable(True)
        self.tools_actions[name].setEnabled(True)
        self.menuTools.addAction(self.tools_actions[name])

    def add_dock_widget(
        self, name: str, dock_widget: QDockWidget, preferred_area: Qt.DockWidgetArea
    ) -> None:
        """
        Add an app's dock widget to the main window in its preferred area.

        Parameters
        -----------
        name : str
            Name of app.
        dock_widget : QDockWidget
            App's dock widget.
        preferred_area : Qt.DockWidgetArea
            Area to add app's dock widget.
        """
        self.dock_widgets[name] = dock_widget
        self.dock_widgets[name].setVisible(False)
        if self.dock_widgets[name].windowTitle() == "":
            self.dock_widgets[name].setWindowTitle(name)
        self.addDockWidget(preferred_area, self.dock_widgets[name])

    def connect_app_to_toolbar(self, name: str) -> None:
        """
        Connect a dock widget's visibility to the QAction's checkbox and vice versa.

        Parameters
        -----------
        name : str
            Name of app.
        """
        self.tools_actions[name].toggled.connect(self.show_or_hide_app)
        self.dock_widgets[name].visibilityChanged.connect(self.uncheck_tools_action)

    def show_or_hide_app(self, checked: bool) -> None:
        """
        Changes application visibility to follow whether relevant QAction is checked.

        Parameters
        -----------
        checked : bool
            State of sending QAction.
        """
        sender = self.sender()
        if sender:
            dock = self.dock_widgets[sender.text()]
            dock.setVisible(checked)
            if checked and dock.isFloating():
                dock.raise_()

            if checked:
                self.load_app_signal.emit(sender.text())
            else:
                self.offload_app_signal.emit(sender.text())

    def uncheck_tools_action(self, checked: bool) -> None:
        """
        Unchecks relevant QAction when user closes QDockWidget.

        Parameters
        -----------
        checked : bool
            Whether or not the sending dock is visible.
        """
        dock = self.sender()
        if dock:
            name = [key for key, value in self.dock_widgets.items() if value == dock][0]
            self.tools_actions[name].setChecked(checked)
            self.offload_app_signal.emit(name)

    def closeEvent(self, event: QCloseEvent) -> None:
        """
        Emits a signal upon application close to enable sub-applications to respond.

        Parameters
        -----------
        event : QCloseEvent
            Qt close event object.
        """
        self.window_closing_signal.emit()
        super().closeEvent(event)


class Model:
    """
    The Model class for Wrapper.

    Attributes
    ----------
    pdf_path : os.path
        Path to location of PDF file containing help documentation.

    Methods
    -------
    open_help_pdf()
        open the help pdf in the default pdf browser.
    """

    def __init__(self) -> None:
        """Constructs necessary attributes for the Model object"""
        self.pdf_path = styleloader.resource_path(
            "./../resources/MITM-SoftwareUserManual.pdf"
        )

    def open_help_pdf(self) -> None:
        """Opens help pdf in default pdf viewer"""
        subprocess.Popen([self.pdf_path], shell=True)
