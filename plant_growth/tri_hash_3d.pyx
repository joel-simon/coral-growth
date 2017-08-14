# cython: boundscheck=True
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

from cymem.cymem cimport Pool
from plant_growth.vector3D cimport vset

cdef class TriHash3D:
    def __init__(self, cell_size, world_size):
        self.mem = Pool()
        self.cell_size = cell_size
        self.world_size = world_size

        self.dim_size = int(world_size / cell_size)
        self.dim_size2 = self.dim_size**2
        self.size = self.dim_size**3
        self.bins = <Entry **>self.mem.alloc(self.size, sizeof(Entry *))
        # print('n bins', self.size)

    cdef void initialize(self):
        cdef size_t i
        for i in range(self.size):
            self.bins[i] = NULL

    cdef uint tri_bucket(self, double a[3], double b[3], double c[3]):
        # Find cell coords off center of tri.
        cdef double ws2 = self.world_size / 2
        cdef int x = <int>((((a[0] + b[0] + c[0])/3) + ws2) / self.cell_size)
        cdef int y = <int>((((a[1] + b[1] + c[1])/3) + ws2) / self.cell_size)
        cdef int z = <int>((((a[2] + b[2] + c[2])/3) + ws2) / self.cell_size)

        cdef uint bi = x + y*self.dim_size + z*self.dim_size2
        bi = max(0, min(bi, self.size-1))
        return bi

    cdef void add_tri(self, void *key, double a[3], double b[3], double c[3]) except *:
        cdef uint bi = self.tri_bucket(a, b, c)
        cdef Entry *entry = <Entry *>self.mem.alloc(1, sizeof(Entry))

        entry.key = key
        entry.next = self.bins[bi]
        self.bins[bi] = entry

    cdef void remove_tri(self, void *key, double a[3], double b[3], double c[3]) except *:
        cdef uint bi = self.tri_bucket(a, b, c)
        cdef Entry *entry = self.bins[bi]

        if entry == NULL:
            raise ValueError('key not found')

        # If it's the head of the list.
        if entry.key == key:
            self.bins[bi] = self.bins[bi].next
            return

        while entry.next != NULL:

            if entry.next.key == key:
                entry.next = entry.next.next
                return

            else:
                entry = entry.next

        raise ValueError('key not found')

    cdef void move_tri(self, void *key, double a[3], double b[3], double c[3],
                                      double d[3], double e[3], double f[3]) except *:
        cdef uint bfrom = self.tri_bucket(a, b, c)
        cdef uint bto = self.tri_bucket(d, e, f)

        if bfrom == bto:
            return

        else:
            self.remove_tri(key, a, b, c)
            self.add_tri(key, d, e, f)

    cdef uint neighbors(self, double a[3], double b[3], double c[3], uint n, void **results) except *:
        cdef int h, x, y, z
        cdef uint i = 0
        cdef Entry* entry

        cdef double ws2 = self.world_size / 2
        cdef int cx = <int>((((a[0] + b[0] + c[0])/3) + ws2) / self.cell_size)
        cdef int cy = <int>((((a[1] + b[1] + c[1])/3) + ws2) / self.cell_size)
        cdef int cz = <int>((((a[2] + b[2] + c[2])/3) + ws2) / self.cell_size)

        for x in range(max(0, cx-1), min(cx+2, self.dim_size-1)):
            for y in range(max(0, cy-1), min(cy+2, self.dim_size-1)):
                for z in range(max(0, cz-1), min(cz+2, self.dim_size-1)):
                    h = x + y*self.dim_size + z*self.dim_size2
                    entry = self.bins[h]

                    while entry != NULL:
                        results[i] = entry.key

                        if i == n - 1:
                            return i
                        else:
                            i += 1
                            entry = entry.next

        return i





