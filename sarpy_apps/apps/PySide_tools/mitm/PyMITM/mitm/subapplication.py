from abc import ABCMeta, abstractmethod
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.mitm.controller import Controller \
    as MITMController


class AbstractApp(metaclass=ABCMeta):
    """
    This class implements the API that MITM uses to communicate with subapps.
    All subapplications must inherit from this class and must override at least
    the first two methods.

    This class is an abstract class and should not be instantiated on its own.

    Attributes
    ----------
    mitm_controller : MITMController
        Reference to MITM controller object.
    app_dict : dict
        Reference to dictionary of sister applications.

    Methods
    -------
    get_name()
        Returns application name.
    get_dock_widget():
        Returns application GUI in the form of a dock widget.
    set_mitm_controller(controller)
        Store a reference to MITM Controller.
    set_app_dict(appdict)
        Store a reference to application dictionary to interface with other apps
    get_preferred_area()
        Get the dock area that the app should initially appear in
    change_appearance(dark_mode)
        Modify the app's appearance when Dark Mode is toggled
    exit_cleanup()
        Perform any necessary cleanup when the user closes MITM
    load_app()
        Perform any necessary setup now that the application is visible.
    offload_app()
        Perform any necessary teardown now that the app is hidden.
    """

    def __init__(self) -> None:
        """
        Constructs necessary attributes for the AbstractApp object.
        Must only ever be called from child class' constructor.

        Parameters
        -----------
        self : object
            The class instance.
        """
        self.mitm_controller = None
        self.app_dict = None
        self.is_loaded = False

    @abstractmethod
    def get_name(self) -> str:
        """
        Abstract method to retrieve app name.
        Must be overridden in the child class

        Parameters
        -----------
        self : object
            The class instance.

        Returns
        -------
        str
        """
        pass

    @abstractmethod
    def get_dock_widget(self) -> QDockWidget:
        """
        Abstract method to retrieve app dock widget.
        Must be overridden in the child class

        Parameters
        -----------
        self : object
            The class instance.

        Returns
        -------
        QDockWidget
        """
        pass

    def set_mitm_controller(self, controller: MITMController) -> None:
        """
        Store a reference to MITM Controller.
        Responsible for setting up connections between this app and MITM Controller.
        Overriding is optional.

        Parameters
        -----------
        controller : mitm_controller.Controller
            MITM Controller object
        """
        self.mitm_controller = controller

    def set_app_dict(self, appdict: dict[str, Any]) -> None:
        """
        Stores a reference to the dictonary of other apps.
        Responsible for setting up connections between this app and others.
        Overriding is optional.

        Parameters
        -----------
        appdict : dict[str, AbstractApp]
            dictionary of sister apps
        """
        self.app_dict = appdict

    def get_preferred_area(self) -> Qt.DockWidgetArea:
        """
        Returns the preferred area for the QDockWidget to appear in MITM.
        Overriding is optional.

        Returns
        -------
        Qt.DockWidgetArea
        """
        return Qt.BottomDockWidgetArea

    def change_appearance(self, dark_mode: bool) -> None:
        """
        Modify the app's appearance when Dark Mode is toggled
        Overriding is optional.

        Parameters
        -----------
        dark_mode : bool
            whether the current mode is Dark Mode or not
        """
        pass

    def load(self) -> None:
        """
        Perform any setup neccessary after the app becomes visible.
        Overriding is optional.
        """
        self.is_loaded = True

    def offload(self) -> None:
        """
        Perform any teardown necessary after the app becomes hidden. 
        
        This is a courtesy to other applications to ensure the app is not 
        consuming resources or competing for processing power while it is not
        being used. For example, it could disconnect signals to expensive
        slots.
        
        Overriding is optional.
        """
        self.is_loaded = False

    def exit_cleanup(self) -> None:
        """
        Perform any necessary final cleanup when the user closes MITM
        Overriding is optional.
        """
        pass
