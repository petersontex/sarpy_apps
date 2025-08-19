# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Aperture Tool'
copyright = '2025, N/A'
author = 'N/A'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys

# Add the path to your Python package
sys.path.insert(0, os.path.abspath('../../src/'))

# Debug: Print paths to verify
print("Current working directory:", os.getcwd())
print("Added to Python path:", os.path.abspath('../../src/'))

# Test import
try:
    import PyRCS
    print("✓ Successfully imported PyAperture")
    print("PyAperture location:", PyRCS.__file__)
except ImportError as e:
    print("✗ Failed to import PyAperture:", e)

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',  # For Google/NumPy style docstrings
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'  # Using RTD theme
html_static_path = ['_static']

# -- Autodoc configuration ---------------------------------------------------

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'special-members': '__init__',
}

# Mock imports for packages that might not be available during doc build
autodoc_mock_imports = [
    # Add any packages your code imports that might not be installed
    # 'numpy', 'pandas', 'requests', etc.
]