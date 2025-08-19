from abc import ABC, abstractmethod

from typing import (
    List,
    Dict,
    Tuple,
    Optional,
    Union,
    Any,
    Callable,
    TypeVar,
    Type,
    cast,
    Set,
)

# TODO: need to write up documentation on how to use these classes to extend functionality of MITM classes for other applications


class ExtensibleObject:
    """
    Mixin class that provides extension functionality to any class.
    """

    def __init__(self) -> None:
        """Initialize extension system."""
        self._extensions = {}
        self._additional_menu_actions = []

    def register_extension(self, name: str, extension: "Extension") -> None:
        """
        Register an extension with this object.

        Parameters
        ----------
        name : str
            Unique name for the extension.
        extension : Extension
            Extension object.
        """
        self._extensions[name] = extension
        extension.init_extension(self)

        # Add menu actions if the extension provides them and we support menus
        if hasattr(extension, "get_menu_actions") and hasattr(
            self, "register_menu_action"
        ):
            actions = extension.get_menu_actions(self)
            for action in actions:
                self.register_menu_action(action)

    def has_extension(self, name: str) -> bool:
        """
        Check if an extension is registered.

        Parameters
        ----------
        name : str
            Extension name.

        Returns
        -------
        bool
            True if extension exists.
        """
        return name in self._extensions

    def get_extension(self, name: str) -> Any:
        """
        Get an extension by name.

        Parameters
        ----------
        name : str
            Extension name.

        Returns
        -------
        Any
            Extension object.

        Raises
        ------
        KeyError
            If extension not found.
        """
        if name not in self._extensions:
            raise KeyError(f"Extension '{name}' not found")
        return self._extensions[name]

    def __getattr__(self, name) -> Any:
        """
        Delegate attribute access to extensions if not found in this class.

        Parameters
        ----------
        name : str
            Attribute name.

        Returns
        -------
        Any
            Attribute value from extension.

        Raises
        ------
        AttributeError
            If attribute not found in extensions.
        """
        # Avoid recursion with _extensions attribute
        if name == "_extensions":
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '_extensions'"
            )

        # Get extensions safely without triggering __getattr__ again
        try:
            extensions = object.__getattribute__(self, "_extensions")
        except AttributeError:
            # If _extensions doesn't exist, we can't delegate
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{name}'"
            )

        # Check if any extension has this attribute
        for extension in extensions.values():
            if hasattr(extension, name):
                attr = getattr(extension, name)
                # If it's a method, bind it to pass self as first argument
                if callable(attr):
                    return lambda *args, **kwargs: attr(self, *args, **kwargs)
                return attr

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


class Extension(ABC):
    """
    Abstract base class for object extensions.

    This defines the interface that all extensions should implement.
    """

    @abstractmethod
    def init_extension(self, obj: Any) -> None:
        """
        Initialize the extension with the object.

        Called when the extension is registered with an object.

        Parameters
        ----------
        obj : Any
            The object this extension is attached to.
        """
        pass

    @abstractmethod
    def duplicate(self) -> "Extension":
        """
        Create a duplicate of this extension.

        Called when the object is duplicated to create a copy of the extension.

        Returns
        -------
        Extension
            New extension instance with copied data.
        """
        pass
