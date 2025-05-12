import pytest
from sarpy_apps.apps.image_viewer import ImageViewer
from tests import unittest
from tk_builder.widgets.basic_widgets import Frame
from tk_builder.image_reader import CanvasImageReader
from tkinter import ttk
import tkinter as tk
from unittest.mock import MagicMock
from unittest.mock import patch
import unittest.mock as mock
from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader

def get_menu_items(app):
    items = []
    for index in range(app.file_menu.index('end') + 1):
        try:
            label = app.file_menu.entrycget(index, 'label')
            items.append(label)
        except tk.TclError:
            pass # Ignore separators or other non-command entries
    return items

class TestImageViewerClass:
    def test_default_title(self):
        root = tk.Tk()
        app = ImageViewer(root, None)
        assert app.winfo_toplevel().title() == "Image Viewer"

    #@mock.patch('sarpy_apps.supporting_classes.image_reader')
    #@mock.patch('sarpy_apps.supporting_classes.image_reader.SICDTypeCanvasImageReader')
    #, mock_sarpy_apps
    def test_multiple_filenames_title(self):
        root = tk.Tk()
        app = ImageViewer(root, None)
        with mock.patch("sarpy_apps.apps.image_viewer.AppVariables.image_reader") as reader:
            reader.__get__ = mock.Mock(return_value=True)
            reader.file_name.__get__ = mock.Mock(return_value=['TestImage01.nitf, TestImage02.nitf'])
            assert ImageViewer().winfo_toplevel().title() == 'Image Viewer, Multiple Files'
        #app.variables.image_reader = mock_sarpy_apps.supporting_classes.image_reader()
        #app.variables.image_reader.base_reader.file_name.return_value = ['TestImage01.nitf, TestImage02.nitf']
        #mock_sarpy_apps.supporting_classes.image_reader.SICDTypeCanvasImageReader().file_name.return_value = ['TestImage01.nitf, TestImage02.nitf']
        #mock_a().method_a.return_value = 'Mocked A'
        
        #the_reader = SICDTypeCanvasImageReader(fnames)
        #mock = MagicMock()
        #mock. = 'TestImage01.nitf, TestImage02.nitf'
        #app.variables.image_reader = the_reader
        #with patch('file_name', return_value='TestImage01.nitf, TestImage02.nitf'):
        #app.set_title()
        #assert app.winfo_toplevel().title() == 'Image Viewer, Multiple Files'
        #app.image_reader.base_reader.file_name = ["First file name", "Second file name"]
        #app.set_title()
        #assert app.winfo_toplevel().title() == "First file name, Second file name"
    
    # def test_menu(self):
    #     root = tk.Tk()
    #     app = ImageViewer(root, None)
    #     menu_items = get_menu_items(app)
    #     assert "Open Image" in menu_items

    def test_exit(self):
        root = tk.Tk()
        app = ImageViewer(root, None)
        app.exit()
        try:
            assert app.winfo_exists() == False
        except tk.TclError:
            assert True