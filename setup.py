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

# _macros = [('CYTHON_TRACE', '1')]
_macros = None

compiler_directives = {'linetrace': True, 'profile': True}

extensions = [
    Extension(
        'plant_growth/geometry',
        sources = ['./plant_growth/geometry.pyx'],
        extra_compile_args = _extra,
        define_macros=_macros
    ),
    Extension(
        'plant_growth/plant',
        sources = ['./plant_growth/plant.pyx'],
        extra_compile_args = _extra,
        define_macros=_macros
    ),
    Extension(
        'plant_growth/world',
        sources = ['./plant_growth/world.pyx'],
        extra_compile_args = _extra,
        define_macros=_macros
    ),
    Extension(
        'plant_growth/spatial_hash',
        sources = ['./plant_growth/spatial_hash.pyx'],
        extra_compile_args = _extra,
        define_macros=_macros
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
    ext_modules = cythonize(
        extensions,
        include_path = [numpy.get_include()],
        compiler_directives=compiler_directives
    )
)
