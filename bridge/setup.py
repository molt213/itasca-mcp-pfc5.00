#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script for itasca-mcp-bridge PFC 5.0 compatible version."""
from __future__ import absolute_import, print_function

import os
from setuptools import find_packages, setup

here = os.path.abspath(os.path.dirname(__file__))

# Read README for long description
with open(os.path.join(here, "..", "README.md"), "rb") as f:
    long_description = f.read().decode("utf-8", "replace")

setup(
    name="itasca-mcp-bridge",
    version="0.4.1-pfc5",
    description="PFC 5.0 compatible HTTP bridge for ITASCA codes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/molt213/itasca-mcp-pfc5.00",
    author="Yusong Han, itasca-mcp-pfc5 contributors",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
    ],
    packages=find_packages(),
    package_data={"itasca_mcp_bridge": ["_compat_marker.txt"]},
    include_package_data=True,
    python_requires=">=2.7",
    zip_safe=False,
)
