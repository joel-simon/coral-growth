#!/usr/bin/env python
import os
import numpy
from setuptools import setup, find_packages
from Cython.Build import cythonize

def find_pyx(path='.'):
    pyx_files = []
    for root, dirs, filenames in os.walk(path):
        for fname in filenames:
            if fname.endswith('.pyx'):
                pyx_files.append(os.path.join(root, fname))
    return pyx_files

setup(
    name = "coral-growth",
    version = '0.1.0',
    author = 'joelsimon.net',
    author_email='joelsimon6@gmail.com',
    install_requires = ['numpy', 'cython'],
    license = 'MIT',
    include_dirs = [numpy.get_include()],

    packages = find_packages(),
    ext_modules = cythonize(
        find_pyx(),
        include_path = [numpy.get_include()],
    ),
    include_package_data = True,
    package_data = {
        'cymesh': ['*.pxd'],
    },
)
