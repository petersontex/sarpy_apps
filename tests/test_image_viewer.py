import pytest
from sarpy_apps.apps.image_viewer import ImageViewer
from tests import unittest
from tk_builder.widgets.basic_widgets import Frame
import tkinter as tk

def get_menu_items(app):
    items = []
    for index in range(app.file_menu.index('end') + 1):
        try:
            label = app.file_menu.entrycget(index, 'label')
            items.append(label)
        except tk.TclError:
            pass # Ignore separators or other non-command entries
    return items

@pytest.fixture
def test_app():
    root = tk.Tk()
    app = ImageViewer(root, None)
    return app

class TestImageViewerClass:
    def test_initial_title(self):
        root = tk.Tk()
        app = ImageViewer(root, None)
        assert app.winfo_toplevel().title() == "Image Viewer"

    def test_default_title(self):
        assert test_app.app.winfo_toplevel().title() == "Image Viewer"
    
    def test_multiple_filenames_title(self):
        test_app.variables.image_reader.base_reader.file_name = ["First file name", "Second file name"]
        test_app.set_title()
        assert test_app.winfo_toplevel().title() == "First file name, Second file name"
    
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