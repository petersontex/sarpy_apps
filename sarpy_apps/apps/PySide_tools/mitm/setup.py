from distutils.core import setup

setup(
    name="mitm",
    version="1.0",
    description="Python More Image Than Memory",
    author="",
    author_email="",
    url="local repo",
    packages=[
        "PyMITM",
        "PyMITM.utils",
        "PyMITM.resources",
        "PyMITM.mitm",
        "PyMITM.plotter",
        "PyMITM.metaicon",
        "PyMITM.annotation",
        "PyMITM.pyui"
    ],
    package_data={"PyMITM.resources": ["style.qss", "SoftwareUserManual.pdf"]},
    py_modules=[],
)
