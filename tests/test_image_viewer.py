import pytest
from sarpy_apps.apps.image_viewer import ImageViewer
from tests import unittest
from tk_builder.widgets.basic_widgets import Frame
from tk_builder.image_reader import CanvasImageReader
from sarpy.io.complex.base import SICDTypeReader
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

class TestImageViewerClass(unittest.TestCase):
    def setUp(self):
        root = tk.Tk()
        self.app = ImageViewer(root, None)

    def test_default_title(self):
        self.assertEqual(self.app.winfo_toplevel().title(), "Image Viewer")

    def test_single_filename_title(self):
        with mock.patch.object(self.app.set_title, 'file_name') as mock_file_name: 
            mock_file_name = "TestReader.nitf"
            self.app.set_title()
            self.assertEqual(self.app.winfo_toplevel().title(), 'Image Viewer for TestReader.nitf')

    def test_multiple_filenames_title(self):
        with mock.patch("sarpy_apps.apps.image_viewer.AppVariables.image_reader") as reader:
            self.app.set_title()
            self.assertEqual(self.app.winfo_toplevel().title(), 'Image Viewer, Multiple Files')
        
    # def test_menu(self):
    #     root = tk.Tk()
    #     app = ImageViewer(root, None)
    #     menu_items = get_menu_items(app)
    #     assert "Open Image" in menu_items

    def test_exit(self):
        self.app.exit()
        try:
            assert self.app.winfo_exists() == False
        except tk.TclError:
            assert True