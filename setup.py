import os
import shutil
import setuptools


setuptools.setup(
    name="openmetra",
    version="0.0.1",
    author="Ho-Ro",
    author_email="horo@localhost",
    url="http://github.com/Ho-Ro/OpenMetra",
    description="Gossen METRAHit 29s data readout via BD232 serial interface",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPLv3",
        "Operating System :: Debian Bullseye",
    ],
    python_requires='>=3.6',
    install_requires=[],
    data_files=[
        ("/usr/bin/", ["OpenMetra"]),
        ("/usr/share/doc/openmetra/", ["README.md"]),
        ("/usr/share/doc/openmetra/", ["LICENSE"]),
    ],
)
