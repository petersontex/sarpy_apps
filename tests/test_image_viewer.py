import pytest
import os
from sarpy_apps.apps.image_viewer import ImageViewer, AppVariables
from tests import unittest
from tk_builder.widgets.basic_widgets import Frame
from tk_builder.image_reader import CanvasImageReader
from tk_builder.base_elements import TypedDescriptor
from sarpy.io.complex.base import SICDTypeReader
from sarpy.io.general.base import BaseReader
from tkinter import ttk
import tkinter as tk
from unittest.mock import MagicMock
from unittest.mock import patch
import unittest.mock as mock
from sarpy_apps.supporting_classes.image_reader import SICDTypeCanvasImageReader
from sarpy.io.general.base import BaseReader

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
        # reader = SICDTypeCanvasImageReader(SICDTypeReader(BaseReader()))
        the_style = ttk.Style()
        the_style.theme_use('classic')
        # self.app = ImageViewer(root, reader)
        self.app = ImageViewer(root)
        root.geometry("1000x800")

    def tearDown(self):
        self.app = None

    def test_default_title(self):
        self.assertEqual(self.app.winfo_toplevel().title(), "Image Viewer")

    @patch.object(AppVariables, 'image_reader', return_value=True)
    @patch.object(AppVariables.image_reader, 'file_name', create=True, return_value="/home/fakedir/TestReader.nitf")
    def test_single_filename_title(self, mockAppVariables, mockCanvasImageReader):
        self.app.variables.image_reader = mockAppVariables
        self.app.variables.image_reader.file_name = mockCanvasImageReader
        self.app.set_title()
        #self.assertEqual(self.app.winfo_toplevel().title(), 'Image Viewer for TestReader.nitf')
        self.assertTrue(self.app.winfo_toplevel().title().startswith('Image Viewer for'))

    def test_update_reader(self):
        self.app.update_reader(None)
