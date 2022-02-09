__version__ = "0.2"

import os
import shutil
import setuptools


setuptools.setup(
    name="openmetra",
    version=__version__,
    author="Ho-Ro",
    author_email="horo@localhost",
    url="http://github.com/Ho-Ro/OpenMetra",
    description="Gossen METRAHit 29s data readout",
    long_description="Receive serial data, decode and print it with optional timestamp and unit",
    license="GPLv3",
    platforms=["all"],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3",
        "Operating System :: Debian Bullseye",
    ],
    python_requires=">=3.6",
    install_requires=["matplotlib"],
    data_files=[
        ("/usr/bin/", ["OpenMetra", "MetraPlot"]),
        ("/usr/share/doc/openmetra/", ["README.md"]),
        ("/usr/share/doc/openmetra/", ["LICENSE"]),
    ],
)
