from typing import Any

from sarpy_apps.apps.PySide_tools.mitm.PyMITM.metaicon.view import View
from sarpy_apps.apps.PySide_tools.mitm.PyMITM.metaicon.model import Model


class Controller:
    """
    Main controller class that connects the viewer UI and data model for the MetaIcon.

    Attributes
    ----------
    viewer : View
        The GUI for the application.
    model : Model
        The data handling for the application.
    """
    def __init__(self) -> None:
        self.model = Model()
        self.viewer = View()

    def display(self, metadata: list[Any]) -> None:
        """
        Display relevant metadata information in a transparent metaicon window

        Creates a visual representation with directional arrows using the provided metadata.
        The visualization includes:
        - North (Green)
        - Layover Angle (Orange)
        - Shadow Angle (Blue)
        - Multipath Angle (Red)
        - Yellow arrow indicating side of track (left/right)
        Also populates upper and lower information tables with relevant metadata values.

        Parameters
        ----------
        metaData : list
            A list containing metadata values where:
            - metaData[0:4]: Values for the upper table
            - metaData[4:9]: Values for the lower table
            - metaData[9:13]: Angular positions for the directional arrows (in degrees)
            - metaData[13]: Side of track indicator
        """
        self.viewer.metaicon_plot.clear()
        d1, d2, d3, d4, d5 = self.model.get_arrow_data(metadata)
        self.viewer.draw_arrows(metadata, d1, d2, d3, d4, d5)
