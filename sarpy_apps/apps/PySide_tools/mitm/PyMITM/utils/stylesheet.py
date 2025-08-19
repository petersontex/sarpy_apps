from PySide6.QtGui import (
    QColor,
)
from PySide6.QtWidgets import QPushButton
import qdarkstyle.colorsystem


class MITMStyleSheet:
    """
    Manage stylesheet modifications that can't be handled by QSS files alone.

    This class provides static methods and nested classes to handle dynamic styling
    of various UI components based on their state (selected/unselected) and the
    application's appearance mode (light/dark). It centralizes styling logic and
    color definitions to maintain consistency throughout the application.

    The class is organized into nested classes for different widget types:
    - Plotter: Styles for plotter objects, including progress bars,
    view boxes, and widget containers
    - DirectoryButtons: Styles for directory navigation buttons
    - MetaIcon: Styles for the meta-icon widget display

    Each nested class contains color definitions, style sheets, and helper methods
    to generate appropriate styles based on the current state and appearance mode.
    """

    class Plotter:
        progress_bar = (
            "QProgressBar {"
            "    border: 1px solid black;"
            "    border-top-right-radius: 7px;"
            "    border-top-left-radius: 7px;"
            "    border-bottom-right-radius: 7px;"
            "    border-bottom-left-radius: 7px;"
            "}"
            "QProgressBar::chunk {"
            "    background: QLinearGradient(spread:reflect, x1:0, y1:0, x2:0.5, y2:0, stop:0 #D3D3D3, stop:1 #4B9FC1);"
            "    border-top-right-radius: 7px;"
            "    border-top-left-radius: 7px;"
            "    border-bottom-right-radius: 7px;"
            "    border-bottom-left-radius: 7px;"
            "    margin: 2px;"
            "    color: white;"
            "}"
        )

        class ViewBox:
            light = QColor(211, 211, 211)
            dark = QColor(53, 53, 53)
            light_blue = qdarkstyle.colorsystem.Blue.B90
            dark_blue = qdarkstyle.colorsystem.Blue.B20

            def get_color(is_selected: bool, dark_mode: bool) -> QColor | str:
                if is_selected:
                    if dark_mode:
                        return MITMStyleSheet.Plotter.ViewBox.dark_blue
                    else:
                        return MITMStyleSheet.Plotter.ViewBox.light_blue
                else:
                    if dark_mode:
                        return MITMStyleSheet.Plotter.ViewBox.dark
                    else:
                        return MITMStyleSheet.Plotter.ViewBox.light

        class Widget:
            class DockWidgetContents:
                light = qdarkstyle.colorsystem.Blue.B110
                dark = "#12263b"

            class UpperControlsWidget:
                light = qdarkstyle.colorsystem.Blue.B100
                dark = "#415A77"

            class PushButton:
                light = qdarkstyle.colorsystem.Blue.B100
                dark = "#1b263b"

            def selected_style_sheet(dark_mode: bool) -> str:
                dock_widget_contents_color = (
                    MITMStyleSheet.Plotter.Widget.DockWidgetContents.light
                )
                upper_controls_widget_color = (
                    MITMStyleSheet.Plotter.Widget.UpperControlsWidget.light
                )
                push_button_color = MITMStyleSheet.Plotter.Widget.PushButton.light

                if dark_mode:
                    dock_widget_contents_color = (
                        MITMStyleSheet.Plotter.Widget.DockWidgetContents.dark
                    )
                    upper_controls_widget_color = (
                        MITMStyleSheet.Plotter.Widget.UpperControlsWidget.dark
                    )
                    push_button_color = MITMStyleSheet.Plotter.Widget.PushButton.dark

                return """
                    QDockWidget::title {
                        background: palette(highlight);
                        border: 1px solid palette(midlight)
                    }

                    QWidget#dockWidgetContents {
                        background: %s
                    }

                    QWidget#upperControlsWidget {
                        background: %s   
                    }

                    QPushButton {
                        background: %s 
                    }

                    QComboBox {
                        background: %s
                    }
                """ % (
                    dock_widget_contents_color,
                    upper_controls_widget_color,
                    push_button_color,
                    push_button_color,
                )

    class DirectoryButtons:
        class SelectedButton:
            light = "#c9c9c9"
            dark = "#202020"

        def get_style_sheet(selected: bool, dark_mode: bool) -> str:
            color = MITMStyleSheet.DirectoryButtons.SelectedButton.light
            if dark_mode:
                color = MITMStyleSheet.DirectoryButtons.SelectedButton.dark

            fontstr = "font-weight: bold;" if selected else ""
            colorstr = "background: %s;" % color if selected else ""

            return """
                QPushButton {
                    padding-left: 5px;
                    padding-right: 5px;
                    padding-top: 3px;
                    padding-bottom: 3px;
                    %s
                    %s
                }
            """ % (
                fontstr,
                colorstr,
            )

        def change_color(button: QPushButton, dark_mode: bool) -> None:
            if "font-weight" in button.styleSheet():
                button.setStyleSheet(
                    MITMStyleSheet.DirectoryButtons.get_style_sheet(True, dark_mode)
                )
            else:
                button.setStyleSheet(
                    MITMStyleSheet.DirectoryButtons.get_style_sheet(False, dark_mode)
                )

    class MetaIcon:
        stylesheet = (
            "PlotWidget { background: #00000000 }"
            "QTableWidget { background: #1F1F1F }"
            "QTableWidget { color: #FFFFFF }"
            "QTableWidget { border: 2px solid #4B9FC1}"
        )
        plot_background_color = "#00000000"
        view_box_border_color = "#4B9FC1"
        layover_color = "#FF8C00"
        shadow_color = "#00A6FB"
        multipath_color = "#FF031C"
        font = "Consolas"
        font_size = 12
