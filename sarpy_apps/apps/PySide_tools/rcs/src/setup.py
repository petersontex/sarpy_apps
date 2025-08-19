from distutils.core import setup

setup(
    name="mitm-rcs-tool",
    version="1.0",
    description="Python Radar Cross Section Tool",
    author="",
    author_email="",
    url="local repo",
    packages=["PyRCS"],
    py_modules=["rcs_model", "rcs_controller", "rcs_viewer", "ui_rcs_tool"],
)
