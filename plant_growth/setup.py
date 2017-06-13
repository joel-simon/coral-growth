from distutils.core import setup
from Cython.Build import cythonize

setup(ext_modules = cythonize(
           "aabb.pyx",            # our Cython source
           sources=["AABB.cpp"],  # additional source file(s)
           language="c++",        # generate C++ code
      ))
