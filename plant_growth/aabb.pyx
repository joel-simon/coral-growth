# distutils: language = c++
# distutils: sources = AABB.cpp

from libcpp.vector cimport vector

cdef extern from "AABB.h" namespace "aabb":
    cdef cppclass AABB:
        AABB() except +
        AABB(unsigned int) except +
        AABB(const vector[double]&, const std::vector[double]&) except +
        double computeSurfaceArea() const
        double getSurfaceArea() const
        void merge(const AABB&, const AABB&)
        bool contains(const AABB&) const
        bool overlaps(const AABB&) const
        vector[double] computeCentre()
        void setDimension(unsigned int)
        std::vector[double] lowerBound
        std::vector[double] upperBound
        std::vector[double] centre
        double surfaceArea

cdef class AABB:
    cdef AABB c_aabb      # hold a C++ instance which we're wrapping
    def __cinit__(self, int x0, int y0, int x1, int y1):
        self.c_aabb = AABB(x0, y0, x1, y1)
    def get_area(self):
        return self.c_aabb.getArea()
    def get_size(self):
        cdef int width, height
        self.c_aabb.getSize(&width, &height)
        return width, height
    def move(self, dx, dy):
        self.c_aabb.move(dx, dy)
