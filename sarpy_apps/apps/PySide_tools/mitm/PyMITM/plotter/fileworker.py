from PySide6.QtCore import (
    Signal,
    QObject,
)

from typing import (
    Callable,
)

from sarpy.io.complex.converter import SICDTypeReader


class FileOpenWorker(QObject):
    """
    Worker for asynchronously loading and processing image files.

    Creates a worker object that runs in a separate thread to load and process
    image data without freezing the UI. Handles initial decimation and remapping
    of the image data.

    Attributes
    ----------
    reader : SICDTypeReader
        The object used to read the SICD file.
    load_image_function : Callable
        The function that handles the loading, decimation, remapping, and
        display of image data.

    Signals
    -------
    started_signal
        Emitted before load_image_function is called.
    finished_signal
        Emitted after load_image_function has returned.

    Methods
    -------
    run()
        Call load_image_function and emit signals.
    """

    started_signal = Signal(name="started_signal")
    finished_signal = Signal(name="finished_signal")

    def __init__(self, reader: SICDTypeReader, function: Callable) -> None:
        """
        Constructs a FileOpenWorker object

        Parameters
        ----------
        reader : SICDTypeReader
            The file reader that provides access to the image data.
        function : Callable
            The function that handles the loading, decimation, remapping,
            display of image data.
        """
        super().__init__()
        self.reader = reader
        self.load_image_function = function

    def run(self) -> None:
        """
        Execute the file loading and processing operation.

        Emits a signal, calls image_load_function, and emits a signal
        upon completion.
        """
        self.started_signal.emit()

        self.load_image_function(self.reader)

        self.finished_signal.emit()
