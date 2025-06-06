# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from codecs import open

import os


# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
# Get the long description from the README file
with open(os.path.join(here, 'README.md'), 'r') as f:
    long_description = f.read()

path_to_sarpyapps = 'users/529965/Documents/NGA/RDC/Radar/Code/GitHub/petersontex/sarpyapps'
# Get the relevant setup parameters from the package
parameters = {}

setup(name='sarpy_apps',
      version='1.1.25',
      install_requires=[
          f"sarpyapps @ file://localhost/{path_to_sarpyapps}#egg=sarpyapps"]
      )
