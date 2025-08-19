from PySide6.QtWidgets import (
    QMessageBox,
)
from PySide6.QtCore import (
    Qt,
)
from urllib.parse import unquote, urlparse
import sys, os

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.view import View
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.model import Model
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.annotation.controller import \
    Controller as AnnotationController
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.plotter.controller import \
    Controller as PlotterController
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.metaicon.controller import \
    Controller as MetaIconController


class Controller:
    """
    Main controller class that connects the viewer UI and data model for MITM.

    Establishes the application's MVC (Model-View-Controller) architecture by
    connecting the View (UI) and Model (data) components through signal handlers
    and callback methods. The controller handles all interactions between the UI
    and the underlying data.

    Responsibilities include:
    - Initial setup of application components
    - Configuration loading and saving
    - File loading and processing
    - Event handling for UI interactions
    - Metadata extraction and display
    - Aspect ratio calculation and application
    - Plotter management
    - MetaIcon management
    - Annotation management

    The controller is responsible for the core application logic, translating
    user interactions in the viewer into data operations in the model, and
    updating the UI based on the results of those operations.

    Attributes
    ----------
    viewer : View
        The GUI for the application.
    model : Model
        The data handling for the application.
    plots : List[PlotterController]
        List of plotter controllers.
    metaicon : MetaIconController
        The controller for the metaicon.
    annotation_controller
        The controller for annotations.

    """

    def __init__(self, sys_args: list[str] | None = None) -> None:
        """
        Constructs a Controller object.

        Parameters
        ----------
        sys_args : list, optional
            Command line arguments passed to the application. Default is None.
            sys_args[0] is used for configuration file path
            sys_args[1] is used for initial file to open
        """

        self.viewer = View(
            file_open=(
                sys_args[1] if sys_args is not None and len(sys_args) >= 2 else None
            )
        )
        self.model = Model(
            sys_args[0] if sys_args is not None and len(sys_args) > 0 else None
        )

        ## Plotter Start
        self.plots = []
        self._current_plot = None
        ## Plotter End

        ## MetaIcon Start
        self.metaicon = MetaIconController()
        self.viewer.window_closed_signal.connect(self.metaicon.viewer.close)
        ## MetaIcon End

        ## Annotation Start
        self.annotation_controller = AnnotationController(self)
        self.viewer.addDockWidget(
            Qt.RightDockWidgetArea, self.annotation_controller.viewer
        )  # TODO: Have the visiblity of this widget togglable via menu option

        self.viewer.widget_interacted_signal.connect(
            self.annotation_controller.plot_widget_interaction_controller
        )
        self.viewer.widget_changed_signal.connect(
            self.annotation_controller.update_geometry_table
        )
        ## Annnoation End

        # Setup Connections
        self.viewer.open_meta_icon_signal.connect(self.open_metaicon_handler)
        self.viewer.newPlotButton.clicked.connect(self.add_plot)

        self.viewer.file_dialog.directoryEntered.connect(self.double_clicked_handler)
        self.viewer.file_dialog.accepted.connect(
            lambda: self.double_clicked_new_plot(
                self.viewer.file_dialog.selectedFiles()[0]
            )
        )

        self.viewer.widget_changed_signal.connect(self.update_ui_element_handler)
        self.viewer.widget_interacted_signal.connect(self.handle_widget_interaction)
        self.viewer.widget_creation_signal.connect(self.handle_widget_interaction)
        self.viewer.widget_closed_signal.connect(self.check_if_current_widget_closed)

        self.viewer.request_aspect_ratio_signal.connect(self.get_aspect_ratio)
        self.viewer.window_closed_signal.connect(self.model.config.write_config_file)
        self.viewer.application_started_signal.connect(self.create_plot_on_startup)
        self.viewer.file_load_requested_signal.connect(self.load_file_onto_plot)

        self.model.setup_config("mitm.cfg")
        self.viewer.file_dialog.setNameFilters(self.model.config.file_formats)
        self.viewer.file_dialog.set_sidebar_directories(
            self.model.config.favorite_directories
        )

    def load_file_onto_plot(
        self, file_name: str, plot: PlotterController, file_is_dropped: bool
    ) -> None:
        """
        Handle loading files onto a plot.

        Processes files by parsing the URL (if necessary), adjusting for platform-specific 
        path formatting, reading the file using the model, and displaying it in the 
        specified plotter widget.

        Parameters
        ----------
        file_name : str
            URL or path of the dropped file.
        plot : PlotterController
            The plotter widget that is loading the file.
        """
        filepath = file_name
        if file_is_dropped:
            filepath = unquote(urlparse(file_name).path)
            if sys.platform == "win32":
                filepath = filepath[1:]

        reader, size = self.model.basic_file_read(filepath)
        plot.set_size(size)
        plot.threaded_display_image(reader)

    def open_metaicon_handler(self, file_name: str) -> None:
        """
        Handle requests to open the meta-icon display.

        Retrieves metadata for the specified file and passes it to the
        viewer to display in the meta-icon widget.

        Parameters
        ----------
        file_name : str
            Name of the file whose metadata should be displayed.
        """
        meta_data = self.model.get_metadata_from_open_reader(file_name)
        self.metaicon.display(meta_data)

    def update_ui_element_handler(self, plot: PlotterController) -> None:
        """
        Update UI elements when the current plotter widget changes.

        If the plot has a file loaded and the meta-icon widget is visible,
        updates the meta-icon to display metadata for the current file.

        Parameters
        ----------
        plot : PlotterController
            The plotter widget that was interacted with or changed.
        """
        if plot and plot.get_file_name() and self.metaicon.viewer.isVisible():
            self.open_metaicon_handler(plot.get_file_name())

    def double_clicked_handler(self) -> None:
        """
        Handle directory double-click events in the file browser.

        Navigates down into the selected directory by updating the
        directory path and navigation controls.
        """
        self.viewer.move_down_directory()

    def get_aspect_ratio(self, plot: PlotterController) -> None:
        """
        Get and apply the aspect ratio for an image.

        Retrieves the correct aspect ratio for the image from the model
        and applies it to the specified plot widget.

        Parameters
        ----------
        plot : PlotterController
            The plotter widget whose image aspect ratio should be set.
        """
        aspectRatio = self.model.get_aspect_ratio(plot.get_file_name())
        plot.viewer.apply_aspect_ratio_to_image(aspectRatio)

    def create_plot_on_startup(self, file_open: str) -> None:
        """
        Create an initial plotter widget when the application starts.

        If a file was specified to open during startup, attempts to load that file into a
        new plotter widget. If the specified file doesn't exist, displays a warning message.
        If no file was specified, creates an empty plotter widget.

        Parameters
        ----------
        file_open : str
            The file to be loaded onto a plotter widget.
        """
        if file_open is not None and not os.path.isfile(file_open):
            QMessageBox.information(
                None, "Warning", "File '" + file_open + "' does not exist."
            )
            file_open = ""

        if not file_open:
            self.add_plot()
            return

        self.double_clicked_new_plot(file_open)

    def get_current_file_name(self) -> str:
        """
        Get the file name of the current plotter widget.

        Retrieves the current plotter widget and returns its file name.

        Returns
        -------
        str
            The name of the file in the current plotter widget.
        """
        current_widget = self.get_current_widget()
        file_name = current_widget.get_file_name()
        return file_name

    def get_current_widget(self) -> PlotterController:
        """
        Get the currently active plotter widget.

        Returns the plotter widget that is currently selected in the viewer.

        Returns
        -------
        PlotterController
            The currently active plotter widget.
        """
        return self._current_plot

    def change_appearance(self, dark_mode: bool) -> None:
        """
        Change the application's appearance between light and dark modes.

        Updates the visual appearance of the plotter widgets and all directory buttons
        based on the specified mode. Indicates which plotter is selected by rendering 
        it differently.
        """
        self.viewer.change_appearance(dark_mode)

        for plot in self.plots:
            plot.change_color(False, dark_mode)

        self._current_plot.change_color(True, dark_mode)

    def add_plot(self) -> PlotterController:
        """
        Create and add a new plotter widget to the application's dock area.

        Instantiates a new PlotterController, adds it to the collection of 
        plotter widgets, places it in the bottom dock widget area, and
        emits a signal to notify listeners about the widget creation.

        Returns
        -------
        PlotterController
            The newly created plotter instance that was added to the dock.
        """

        new_plot = PlotterController(
            add_geometry_action=self.annotation_controller.right_click_add_geometry,
            parent=self.viewer,
        )
        self.plots.append(new_plot)
        self.viewer.add_plot_to_gui(new_plot.viewer)
        self.viewer.widget_creation_signal.emit(new_plot)
        return new_plot

    def double_clicked_new_plot(self, file: str) -> None:
        """
        Create a new plotter widget and load a file into it when a file is double-clicked.

        Creates a new PlotterController and positions it in the bottom dock widget area. 
        The new plot is initialized with dimensions from the first plot widget, and populated
        with the selected file's data.

        This method handles only files, not directories, and updates the plot widget's
        title based on the selected file.

        Parameters
        ----------
        file : str
            Path to the file that was double-clicked.
        """
        if not os.path.isdir(file):
            new_plot = self.add_plot()
            new_plot.viewer.show()
            new_plot.viewer.raise_()

            new_plot.setup_file(file, False)

    def render_widget_selection(self, selected_widget: PlotterController) -> None:
        """
        Update widget styling to indicate which plotter widget is currently selected.

        Applies the default styling to all plotter widgets, then applies the selected
        styling to the specified widget. This provides a visual indication of which
        plotter widget is currently active.

        Parameters
        ----------
        selected_widget : PlotterController
            The plotter widget that is currently selected and should be highlighted.
        """
        for plot in self.plots:
            plot.change_color(False, self.viewer.dark_mode)

        selected_widget.change_color(True, self.viewer.dark_mode)

    def handle_widget_interaction(self, selected_widget: PlotterController):
        """
        Handle user interactions with plotter widgets and update selection accordingly.

        Processes plotter interaction events by attempting to set the specified widget
        as the current selection. If the selection actually changes, updates the
        visual styling to highlight the newly selected plotter widget.

        Parameters
        ----------
        selected_widget : PlotterController
            The plotter widget that the user interacted with and should be made current.
        """
        changed = self.__set_current_widget(selected_widget)
        if changed:
            self.render_widget_selection(selected_widget)

    def __set_current_widget(self, current_widget: PlotterController | None) -> bool:
        """
        Set a new plotter widget as the current selection.

        Updates the internal reference to the currently selected widget and emits
        a signal to notify listeners of the change. Only emits the signal if the
        widget actually changes.

        Parameters
        ----------
        current_widget : PlotterController or None
            The plotter widget to set as current, or None if no widget is selected.

        Returns
        -------
        bool
            True if the current widget changed, False if it remained the same.
        """
        if current_widget != self._current_plot:
            self._current_plot = current_widget
            self.viewer.widget_changed_signal.emit(self._current_plot)
            return True
        return False

    def check_if_current_widget_closed(self, widget: PlotterController) -> None:
        """
        Handle the case when the currently selected widget is closed.

        Checks if the closed widget is the currently selected one, and if so,
        clears the current selection and closes the meta-icon widget.

        Parameters
        ----------
        widget : PlotterController
            The plotter widget that was closed.
        """
        if self._current_plot == widget:
            self.__set_current_widget(None)
            self.metaicon.viewer.close()
