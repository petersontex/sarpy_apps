import math
from typing import Any


class ArrowData:
    """
    Container to calculate and store the angle and position for a metaicon arrow
    based on the relevant metadata.

    Attributes
    ----------
    angle : float
        The angle of the arrow.
    x : float
        The x position of the arrow.
    y : float
        The y position of the arrow.
    """

    def __init__(self, data: float = 0) -> None:
        """
        Create an ArrowData object.

        Parameters
        ----------
        data : float
            Relevant metadata used to calculate angle, x, and y.
        """
        self.angle = -data + 90 + 180
        self.x = 65 * math.cos(math.radians(-data + 90))
        self.y = 65 * math.sin(math.radians(-data + 90))

    def set_manually(self, angle: float, x: float, y: float) -> None:
        """
        Set angle, x, and y directly.

        Parameters
        ----------
        angle : float
            The angle of the arrow.
        x : float
            The x position of the arrow.
        y : float
            The y position of the arrow.
        """
        self.angle = angle
        self.x = x
        self.y = y

class Model:
    """The data model component of the metaicon."""

    def __init__(self) -> None:
        """Create a Model object."""
        pass

    def get_arrow_data(
        self, metadata: list[Any]
    ) -> tuple[ArrowData, ArrowData, ArrowData, ArrowData, ArrowData]:
        """
        Calculate and return data for the 5 metaicon arrows from the metadata.

        Parameters
        ----------
        metadata : list[Any]
            Metadata from the file reader object.
        
        Returns
        -------
        tuple
            (a1, a2, a3, a4, a5) where:
            - a1 is the arrow data for the green arrow.
            - a2 is the arrow data for the orange arrow.
            - a3 is the arrow data for the blue arrow.
            - a4 is the arrow data for the red arrow.
            - a5 is the arrow data for the yellow arrow.
        """
        a1 = ArrowData(metadata[9])
        a2 = ArrowData(metadata[10])
        a3 = ArrowData(metadata[11])
        a4 = ArrowData(metadata[12])
        a5 = ArrowData()

        a5.set_manually(180, 55, -75)
        if metadata[13] == "L":
            a5.set_manually(0, -55, -75)

        return a1, a2, a3, a4, a5
