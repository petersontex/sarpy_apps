from sarpy_apps.supporting_classes.metaicon.metaicon_data_container import (
    MetaIconDataContainer,
)
from sarpy.io.complex.converter import SICDTypeReader, open_complex
import numpy as np
import psutil
import sys
import os
from typing import Any

if sys.platform == "win32":
    import win32api


class Model:
    """
    The data model component of the MITM application.

    Manages file reading and metadata extraction. Establishes a 
    configuration handler based on the application path.

    Attributes
    ----------
    open_readers : [list[SICDTypeReader]]
        Reader objects for all currently open files.
    config : Config
        Object to handle reading from and writing to configuration file.
    """

    def __init__(self, sys_arg0: str):
        """
        Initialize the model object.

        Parameters
        ----------
        sys_arg0 : str
            The application executable path (sys.argv[0]).
        """
        self.open_readers = []
        self.config = Config(sys_arg0)

    def basic_file_read(self, file_name: str) -> tuple[SICDTypeReader, int]:
        """
        Read and process an image file.

        Opens a complex image file using the appropriate reader, records the
        reader in the list of open readers, and returns the reader along with
        the file size.

        Parameters
        ----------
        file_name : str
            Path to the file to be read.

        Returns
        -------
        tuple
            (reader, size) where:
            - reader: The file reader object that provides access to the image data
            - size: The size of the file in bytes
        """
        reader = open_complex(file_name)

        self.open_readers.append((file_name.split("/")[-1], reader))
        size = os.path.getsize(file_name)

        return reader, size

    def get_metadata_from_open_reader(self, file_name: str) -> list[Any]:
        """
        Extract metadata from an open reader for display in the meta-icon.

        Finds the reader for the specified file and extracts relevant metadata
        fields for display, including image identification, geographic information,
        resolution, collection data parameters, and various angles.

        Parameters
        ----------
        file_name : str
            Name of the file whose metadata should be extracted.

        Returns
        -------
        list
            A list of metadata values formatted for display in the meta-icon widget.
        """

        for file, reader in self.open_readers:
            if file == file_name:
                meta_reader = reader

        sicd = meta_reader.get_sicds_as_tuple()[0]
        data_container = MetaIconDataContainer.from_sicd(sicd)

        return [
            data_container.iid_line,
            data_container.geo_line,
            data_container.res_line,
            data_container.cdp_line,
            data_container.get_angle_line("azimuth"),
            data_container.get_angle_line("graze"),
            data_container.get_angle_line("layover"),
            data_container.get_angle_line("shadow"),
            data_container.get_angle_line("multipath"),
            data_container.north,
            data_container.layover,
            data_container.shadow,
            data_container.multipath,
            data_container.side_of_track,
        ]

    def get_metadata_from_sicd(self, sicd):
        """
        Extract metadata from SICD for display in the meta-icon.

        Parameters
        ----------
        sicd : SICD
            SICD data.

        Returns
        -------
        list
            A list of metadata values formatted for display in the meta-icon widget.
        """

        data_container = MetaIconDataContainer.from_sicd(sicd)

        return [
            data_container.iid_line,
            data_container.geo_line,
            data_container.res_line,
            data_container.cdp_line,
            data_container.get_angle_line("azimuth"),
            data_container.get_angle_line("graze"),
            data_container.get_angle_line("layover"),
            data_container.get_angle_line("shadow"),
            data_container.get_angle_line("multipath"),
            data_container.north,
            data_container.layover,
            data_container.shadow,
            data_container.multipath,
            data_container.side_of_track,
        ]

    def get_aspect_ratio(self, file_name):
        """
        Calculate the correct aspect ratio for an image.

        Determines the proper aspect ratio for display based on the image's
        pixel spacing in row and column directions, adjusting for slant or
        ground plane imagery.

        Parameters
        ----------
        file_name : str
            Name of the file whose aspect ratio should be calculated.

        Returns
        -------
        float
            The aspect ratio (width/height) to use for displaying the image.
        """

        for file, reader in self.open_readers:
            if file == file_name:
                meta_reader = reader
        sicd = meta_reader.get_sicds_as_tuple()[0]

        aspect_ratio_x = sicd.Grid.Col.SS
        aspect_ratio_y = sicd.Grid.Row.SS

        if sicd.Grid.ImagePlane == "Slant":
            aspect_ratio_y = aspect_ratio_y / np.cos(np.deg2rad(sicd.SCPCOA.GrazeAng))
        elif sicd.Grid.ImagePlane == "Ground":
            aspect_ratio_y = aspect_ratio_y * np.cos(np.deg2rad(sicd.SCPCOA.GrazeAng))
        else:
            aspect_ratio = 1

        aspect_ratio = aspect_ratio_x / aspect_ratio_y

        return aspect_ratio

    def get_avail_mem(self) -> float:
        """
        Get the amount of available system memory.

        Returns the current available memory in gigabytes using psutil.

        Returns
        -------
        float
            Available memory in gigabytes.
        """
        return psutil.virtual_memory()[1] / 1000000000

    def setup_config(self, file_name: str) -> None:
        """
        Set up the application configuration.

        Reads the configuration file, validates network shortcuts,
        and ensures file format filters are properly configured.

        Parameters
        ----------
        file_name : str
            Name of the configuration file to read.
        """
        self.config.read_config_file(file_name)
        self.config.check_network_shortcuts()
        self.config.check_file_formats()


class Config:
    """
    Sets up the configuration manager with default values and determines
    the appropriate file path for the configuration file based on the
    application path and platform.

    Allows the user to configure what directories appear in the sidebar, 
    and what file format filters to apply.

    Handles both reading and writing.

    Attributes
    ----------
    formats_key : str
        Header to search for in configuration file for file formats.
    directories_key : str
        Header to search for in configuration file for sidebar directories.
    file_formats : list[str]
        Allowed file formats read from the config file.
    favorite_directories : list[str]
        List of directories read from the config file.
    file_name : str
        Name of the config file to read/write.
    make_file : bool
        Whether to make a new configuration file (True) or overwrite the existing one (False).
    default_file_formats : list[str]
        List of file formats to include by default.
    filepath : str
        The directory the application is stored in (the path to main.py or the executable).
    """

    def __init__(self, sys_arg0: str) -> None:
        """
        Initialize the configuration manager.

        Parameters
        ----------
        sys_arg0 : str
            The application executable path (sys.argv[0]).
        """

        # headers to search for in cfg file
        self.formats_key = "File Formats"
        self.directories_key = "Favorite Directories"

        # header contents
        self.file_formats = []
        self.favorite_directories = []

        self.headers = {
            self.formats_key: self.file_formats,
            self.directories_key: self.favorite_directories,
        }

        self.file_name = ""
        self.make_file = False
        self.default_file_formats = ["SICD Files (*.nitf *.ntf)"]

        # if windows and running inside bundled EXE
        if sys.platform == "win32" and getattr(sys, "_MEIPASS", False):
            # Ensure cfg file ends up in same directory as exe
            self.filepath = os.path.dirname(win32api.GetModuleFileName(0))
        else:
            self.filepath = os.path.dirname(sys_arg0)

    def read_config_file(self, file_name: str) -> None:
        """
        Read and parse the configuration file.

        Opens the specified configuration file and parses its contents,
        populating the headers dictionary with values for file formats
        and favorite directories.

        Parameters
        ----------
        file_name : str
            Name of the configuration file to read.
        """

        self.file_name = os.path.join(self.filepath, file_name)

        try:
            file = open(self.file_name, "r")
        except:
            self.make_file = True
            return

        current_header = ""

        # read through config file
        for line in file:
            line = line.strip()

            # found header
            if line and line[0] == "[" and line[-1] == "]":
                line = line[1:-1].strip()
                # validate header
                if type(self.headers[line]) is list:
                    current_header = line

            elif current_header:
                if line and line[0] != "#":  # line is not a comment or empty
                    self.headers[current_header].append(line)

        file.close()

    def check_network_shortcuts(self) -> None:
        """
        Add Windows network shortcuts to favorite directories.

        On Windows platforms, scans the Network Shortcuts directory and
        adds any shortcuts found there to the list of favorite directories.
        """
        if sys.platform == "win32":
            app_data_dir = os.getenv("APPDATA")
            shortcuts_dir = app_data_dir + "\\Microsoft\\Windows\\Network Shortcuts"
            for filepath in os.listdir(shortcuts_dir):
                f = os.path.join(shortcuts_dir, filepath)
                if f not in self.favorite_directories:
                    self.favorite_directories.append(f)

    def check_file_formats(self) -> None:
        """
        Ensure file format filters are properly configured.

        If no file format filters were found in the configuration file,
        applies the default filters.
        """
        if not self.file_formats:
            self.file_formats.extend(self.default_file_formats)

    def write_config_file(self, dirs: list[str], filters: list[str]) -> None:
        """
        Save the current configuration to the configuration file.

        Writes the current favorite directories and file format filters
        to the configuration file, either creating a new file or modifying
        an existing one.

        Parameters
        ----------
        dirs : list[str]
            List of favorite directory paths to save.
        filters : list[str]
            List of file format filter strings to save.
        """
        outlines = []

        if self.make_file:  # write new config file
            outlines.append("[" + self.directories_key + "]\n")
            outlines.extend(dirs)
            outlines.append("\n")

            outlines.append("[" + self.formats_key + "]\n")
            outlines.extend(filters)
            outlines.append("\n")

        else:  # modfiy existing config file
            file = open(self.file_name, "r")
            lines = file.readlines()
            file.close()

            # read through config file
            underDirsHeader = False
            for line in lines:
                if not underDirsHeader:
                    outlines.append(line)
                line = line.strip()

                # found header
                if line and line[0] == "[" and line[-1] == "]":
                    if underDirsHeader:
                        outlines.append("\n")
                        outlines.append(line + "\n")
                        underDirsHeader = False
                    line = line[1:-1].strip()

                    # validate header
                    if self.directories_key == line:
                        outlines.extend(dirs)
                        underDirsHeader = True
        try:
            with open(self.file_name, "w") as file:
                file.writelines(outlines)
        except Exception as diag:
            print("Warning: could not save configuration.", diag)
