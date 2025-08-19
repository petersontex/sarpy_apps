# Python Application Extension System: Developer Guide

## Overview

This document explains how to use the application extension system defined in `application_extension.py`. This system allows developers to extend the functionality of existing classes without modifying their source code or creating complex inheritance hierarchies.

**This extension system is specifically designed for developers creating applications that integrate with MITM Viewer**. When building applications that will be added to MITM Viewer (the main application that hosts other apps), you'll often need to extend classes from MITM to expand functionality for your specific application needs. This guide shows you how to do that without modifying the core MITM classes.

## Key Concepts

The extension system is built around two main classes:

1. **ExtensibleObject**: A mixin class that makes any class extensible by allowing it to host extensions.
2. **Extension**: An abstract base class that defines the interface for all extensions.

This design follows the *composition over inheritance* principle to achieve flexibility and maintainability.

## Making a Class Extensible

To make a class extensible, have it inherit from `ExtensibleObject`:

```python
from application_extension import ExtensibleObject

class MyClass(SomeParentClass, ExtensibleObject):
    def __init__(self):
        SomeParentClass.__init__(self)
        ExtensibleObject.__init__(self)  # Important!
        
        # Rest of your initialization
```

This enables the class to:
- Register extensions
- Delegate method calls to extensions
- Maintain a registry of extensions

## Creating an Extension

To create an extension, inherit from the `Extension` abstract base class and implement its required methods:

```python
from application_extension import Extension

class MyExtension(Extension):
    def __init__(self):
        # Initialize your extension's attributes
        self._my_data = "Some data"
    
    def init_extension(self, obj):
        # Called when the extension is registered with an object
        # Setup any hooks or initialize based on the object
        pass
    
    def duplicate(self):
        # Create a copy of this extension for object duplication
        new_ext = MyExtension()
        new_ext._my_data = self._my_data
        return new_ext
        
    # Your extension-specific methods
    def do_something(self, obj, param):
        # Note: the first parameter is always the object
        # this extension is attached to
        print(f"Doing something with {obj} and {param}")
        return f"Result: {self._my_data} - {param}"
```

### Understanding the `obj` Parameter

Every method in your extension that will be called via delegation should take the extended object as its first parameter:

```python
def my_method(self, obj, *args, **kwargs):
    # 'self' is the extension instance
    # 'obj' is the object being extended
    # '*args' and '**kwargs' are the additional parameters
```

This is necessary because when a method is called on the extended object and delegated to the extension, the system automatically passes the object as the first argument.

## Using Extensions

### Registering an Extension

```python
# Create an extensible object
my_object = MyExtensibleClass()

# Create an extension
my_extension = MyExtension()

# Register the extension with the object
my_object.register_extension("extension_name", my_extension)
```

### Calling Extension Methods

You can use extension methods in two ways:

1. **Direct method calls on the object** (delegated to the extension):

```python
# This will be delegated to the extension's do_something method
result = my_object.do_something("parameter")
```

2. **Getting the extension explicitly**:

```python
if my_object.has_extension("extension_name"):
    extension = my_object.get_extension("extension_name")
    result = extension.do_something(my_object, "parameter")
```

### Handling Duplication

When objects are duplicated, extensions need to be duplicated too. This is handled automatically if you implement the `duplicate` method in your extensions and call the appropriate code in your object's duplication method:

```python
def duplicate_object(self):
    """Create a duplicate of this object with all extensions."""
    new_object = MyExtensibleClass()
    
    # Copy basic properties
    new_object.some_property = self.some_property
    
    # Copy all extensions
    for name, extension in self._extensions.items():
        new_extension = extension.duplicate()
        new_object.register_extension(name, new_extension)
    
    return new_object
```

## Real-World Example: Extending MITM Viewer Classes

Let's look at a concrete example of extending a `GeometryROI` class from MITM Viewer with RCS functionality for your application:

```python
# Create an extension for RCS functionality
class RCSExtension(Extension):
    def __init__(self):
        self._rcs_feature_w_voids = None
        self._rcs_feature_wo_voids = None
        self._rcs_display_value = "rcs display value?"
    
    def init_extension(self, obj):
        # Add a menu item for RCS options
        if hasattr(obj, 'register_menu_action'):
            rcs_action = QAction("RCS Options", None)
            rcs_action.triggered.connect(lambda: self._show_rcs_options(obj))
            obj.register_menu_action(rcs_action)
    
    def duplicate(self):
        new_ext = RCSExtension()
        new_ext._rcs_feature_w_voids = self._rcs_feature_w_voids
        new_ext._rcs_feature_wo_voids = self._rcs_feature_wo_voids
        new_ext._rcs_display_value = self._rcs_display_value
        return new_ext
    
    # RCS-specific methods
    def set_rcs_feature_wo_voids(self, obj, feature_wo_voids):
        self._rcs_feature_wo_voids = feature_wo_voids
        if hasattr(obj, '_update_geometry_properties'):
            obj._update_geometry_properties(feature_wo_voids)
    
    def get_rcs_feature_wo_voids(self, obj):
        return self._rcs_feature_wo_voids
    
    # More RCS methods...
```

In your RCS application that integrates with MITM Viewer, register this extension with all GeometryROI objects:

```python
# In your RCS application initialization that's being integrated into MITM Viewer
def initialize_rcs_plugin(mitm_viewer):
    # Get all existing ROIs from MITM Viewer
    for roi in mitm_viewer.get_all_rois():
        rcs_ext = RCSExtension()
        roi.register_extension("rcs", rcs_ext)
    
    # Register for future ROI creation in MITM Viewer
    mitm_viewer.roi_created_signal.connect(add_rcs_extension)

def add_rcs_extension(roi):
    rcs_ext = RCSExtension()
    roi.register_extension("rcs", rcs_ext)
```

## Working with UI Elements

Extensions can add UI elements to the objects they extend:

```python
def init_extension(self, obj):
    # Add menu actions if the object supports menus
    if hasattr(obj, 'register_menu_action'):
        action = QAction("My Extension Action", None)
        action.triggered.connect(lambda: self._do_something(obj))
        obj.register_menu_action(action)
```

## Best Practices

1. **Always implement required methods**:
   - `init_extension(self, obj)`: Called when extension is registered
   - `duplicate(self)`: Creates a copy of the extension

2. **Method signatures**:
   - Always include the extended object as the first parameter
   - Design methods to be clear about what object they're operating on

3. **Check capabilities before using them**:
   ```python
   if hasattr(obj, 'some_method'):
       obj.some_method()
   ```

4. **Use descriptive extension names**:
   ```python
   obj.register_extension("rcs", rcs_extension)  # Good
   obj.register_extension("ext1", some_extension)  # Bad
   ```

5. **Keep extensions focused**:
   - Each extension should handle one specific aspect of functionality
   - Don't create "mega-extensions" that do everything

6. **Document your extensions**:
   - Clearly document what your extension does
   - Specify what types of objects it can extend
   - Document any assumptions about the extended object

## Troubleshooting

### Extension Method Not Found

If you get `AttributeError` when trying to call a method on the extended object:

1. Ensure the extension is registered with the correct name
2. Verify the method exists in the extension
3. Make sure the method in the extension takes the object as its first parameter

### Recursion Errors

If you get `RecursionError: maximum recursion depth exceeded`:

1. Check that you're not accidentally creating an infinite loop in `__getattr__`
2. Ensure you're using `object.__getattribute__` for accessing attributes in `__getattr__`

### Type Errors with Abstract Methods

If you get `TypeError: Can't instantiate abstract class with abstract methods`:

1. Implement all required abstract methods from the `Extension` base class
2. Double-check the signatures of `init_extension` and `duplicate`

## Working with Multiple MITM Viewer Applications

A key benefit of this extension system is that it allows multiple applications integrated with MITM Viewer to extend the same base classes without conflicts.

For example:
- Your RCS application might extend `GeometryROI` with RCS-specific functionality
- Another application might extend the same `GeometryROI` with measurement functionality
- A third application might extend it with export capabilities

All these extensions can coexist on the same object instances without interfering with each other, and without modifying the base MITM Viewer classes.

### What Not To Do

**Wrong approach**: Creating subclasses of MITM Viewer classes for your application

```python
# Don't do this!
class RCSGeometryROI(GeometryROI):
    def __init__(self, positions, closed=False, **kwargs):
        super().__init__(positions, closed=closed, **kwargs)
        self._rcs_feature_w_voids = None
        # More RCS attributes and methods...
```

This approach fails when multiple applications try to extend the same base class, as they would each create their own incompatible subclasses.

## Conclusion

This extension system provides a flexible way to add functionality to MITM Viewer classes without modifying their source code or creating complex inheritance hierarchies. By following the patterns outlined in this guide, you can create applications that integrate seamlessly with MITM Viewer and coexist with other applications that extend the same base components.