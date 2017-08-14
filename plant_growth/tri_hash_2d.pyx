# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from cymem.cymem cimport Pool

cdef class TriHash2D:
    def __init__(self, cell_size, world_size):
        self.mem = Pool()
        self.cell_size = cell_size
        self.world_size = world_size

        self.dim_size = int(world_size / cell_size)
        self.size = self.dim_size**2
        self.bins = <Entry **>self.mem.alloc(self.size, sizeof(Entry *))
        # print('n bins', self.size)

    cdef void initialize(self):
        cdef size_t i
        for i in range(self.size):
            self.bins[i] = NULL

    cdef uint tri_bucket(self, double a[2], double b[2], double c[2]):
        # Find cell coords off center of tri.
        cdef double ws2 = self.world_size / 2
        cdef int x = <int>((((a[0] + b[0] + c[0])/3) + ws2) / self.cell_size)
        cdef int y = <int>((((a[1] + b[1] + c[1])/3) + ws2) / self.cell_size)

        cdef uint bi = x + y*self.dim_size
        bi = max(0, min(bi, self.size-1))

        return bi

    cdef void add_tri(self, void *key, double a[2], double b[2], double c[2]) except *:
        cdef uint bi = self.tri_bucket(a, b, c)
        cdef Entry *entry = <Entry *>self.mem.alloc(1, sizeof(Entry))

        entry.key = key
        entry.next = self.bins[bi]
        self.bins[bi] = entry

    def py_add_tr(self, object key, list la, list lb, list lc):
        cdef double a[2], b[2], c[2]
        a[:] = la
        b[:] = lb
        c[:] = lc
        self.add_tri(<void *>key, a, b, c)

    cdef uint neighbors(self, double a[2], uint n, void **results) except *:
        cdef int h, x, y, z
        cdef uint i = 0
        cdef Entry* entry

        cdef double ws2 = self.world_size / 2
        cdef int cx = <int>((a[0] + ws2) / self.cell_size)
        cdef int cy = <int>((a[1] + ws2) / self.cell_size)

        for x in range(max(0, cx-1), min(cx+2, self.dim_size-1)):
            for y in range(max(0, cy-1), min(cy+2, self.dim_size-1)):
                h = x + y*self.dim_size
                entry = self.bins[h]

                while entry != NULL:
                    results[i] = entry.key

                    if i == n - 1:
                        return i
                    else:
                        i += 1
                        entry = entry.next
        return i

    def py_neighbors(self, a):
        cdef int h, x, y, z
        cdef Entry* entry

        cdef double ws2 = self.world_size / 2
        cdef int cx = <int>((a[0] + ws2) / self.cell_size)
        cdef int cy = <int>((a[1] + ws2) / self.cell_size)

        cdef list results = []

        for x in range(max(0, cx-1), min(cx+2, self.dim_size-1)):
            for y in range(max(0, cy-1), min(cy+2, self.dim_size-1)):
                h = x + y*self.dim_size
                entry = self.bins[h]

                while entry != NULL:
                    results.append(<object>entry.key)
                    entry = entry.next
        return results
