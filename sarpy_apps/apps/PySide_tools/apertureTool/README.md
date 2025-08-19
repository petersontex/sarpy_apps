# Aperture Tool
The Aperture tool is a continuation of sarpy's Aperture tool (found at https://github.com/ngageoint/sarpy_apps) with added features and utilizing PySide6 instead of tkinter. This tool is intended as an application/plugin to be used with MITM (more image than memory) Viewer tool. The main features and capabilities of this tool are listed below.

- Evaluate the k-space of polygon geometries with or without voids
- Apply windowing filters on the k-space
- Select rectangular sub-aperture regions
- Create, play, and export animations showing changes in the k-space and resulting post-processed spatial domain with various options
- Export images of the k-space/filtered view
- Switch between various geometries and selections quickly on vairous images
- Display resulting metadata changes with the meta icon view for each frame
- Export resulting filtered chip as a SICD

## System Requirements

- Python 3.11
- Dependencies listed in requirements.txt (or use standalone)

## Download
### Gitlab
```console
git clone <repo URL>
```
## Installation

### Python
1. Navigate to the main aperture-tool repo.
2. ```console
   pip install -r requirements.txt
   ```
3. ```console
   pip install src/.
   ```
4. Install PyMITM

### Standalone Application
## Packaging
PyRCS can be packaged as a standalone executable using PyInstaller:

1. Install PyMITM if not already installed:

2. Navigate to the aperture-tool directory:
   ```
   pip install pyinstaller
   ```

   ```
   pyinstaller ApertureApplication.py
   ```

3. Create the executable:
   ```
   pyinstaller ApertureApplication.spec
   ```
## Running Standalone Application
1. Run the executable:
   ```
   ./dist/ApertureApplication
   ```

## Project Structure

```
APERTURE-TOOL/
├── ApertureApplication.py     # Application entry point
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── mitm.cfg                   # Configuration file
├── setup.py                   # Package setup script
├── docs/                      # Documentation, generated docs and makefiles for generating docs
│   ├── build/                 # Built documentations
│   │   ├── doctrees/          # Built doctrees documentation
│   │   ├── html/              # Built html documentation
│   │   └── latex/             # Built latex documentation
│   └── source/                # Source directory for sphinx
├── dist/                      # Distribution files
│   └── ApertureApplication/   # Built application
└── src/                       # Source code directory
    ├── build/                 # Build artifacts
    ├── PyAperture/            # PyAperture module
    │   ├── aperture_ui/       # UI components
    │   │   └── aperture_tool.ui  # UI definition file
    │   ├── controller/        # Controller components for MVC architecture
    │   │   ├── __init__.py
    │   │   └── aperture_controller.py
    │   ├── model/             # Model components for MVC architecture
    │   │   ├── __init__.py
    │   │   └── aperture_model.py
    │   ├── services/          # Service layer components
    │   │   ├── __init__.py
    │   │   ├── animation_service.py
    │   │   ├── export_service.py
    │   │   ├── roi_service.py
    │   │   └── validation_service.py
    │   ├── view/              # View components for MVC architecture
    │   │   ├── __init__.py
    │   │   └── aperture_viewer.py
    │   ├── ui_aperture_tool.py  # Compiled UI file
    │   └── __init__.py
    └── python_aperture_tool.egg-info/  # Package metadata
```

## Architecture

Aperture Tool follows the Model-View-Controller (MVC) architectural pattern:

- **Model**: Manages data loading and application state
- **View**: Handles UI rendering and user interaction
- **Controller**: Coordinates between Model and View components

The application uses PySide (Qt for Python) for its graphical interface and PyQtGraph for specialized scientific image display, providing a responsive UI even with large datasets.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a new Pull Request

## Project status
PyAperture is currently not actively being worked on.