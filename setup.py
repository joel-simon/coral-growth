#!/usr/bin/python3

try:
  from setuptools import setup
  from setuptools.extension import Extension
except Exception:
  from distutils.core import setup
  from distutils.extension import Extension

from Cython.Build import cythonize
from Cython.Distutils import build_ext
import numpy

_extra = ['-ffast-math']

extensions = [
    Extension(
      'plant_growth/vec2D',
      sources = ['./plant_growth/vec2D.pyx'],
      extra_compile_args = _extra
      ),
    ]

setup(
    name = "plant-growth",
    version = '0.1.0',
    author = 'joelsimon.net',
    install_requires = ['numpy', 'cython'],
    license = 'MIT',
    cmdclass={'build_ext' : build_ext},
    include_dirs = [numpy.get_include()],
    ext_modules = cythonize(extensions,include_path = [numpy.get_include()])
)
