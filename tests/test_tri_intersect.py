from plant_growth.tri_intersection import py_tri_tri_intersection

connected_tri_a = [[-3.109626, 0.913894, -1.093081],
                    [0.000000, -0.000000, 1.432313],
                    [0.000000, 0.000000, -1.093081]]

connected_tri_b = [[ 0.000000, -0.000000, 1.432313],
                   [ 1.888641, -0.284436, 1.432313],
                   [ 0.000000, 0.000000, -1.093081]]

print(py_tri_tri_intersection(*(connected_tri_a + connected_tri_b)))

inter_tri_a =  [[-2.086964, 1.219437, -0.480749],
                [0.105598, -1.323423, 0.293974],
                [0.105598, 1.219437, -0.480749]]

inter_tri_b = [[-3.696262, 0.634013, -1.157567],
                [0.716440, -0.634013, 1.178764],
                [-1.503700, 0.634013, -1.157567]]

print(py_tri_tri_intersection(*(inter_tri_a + inter_tri_b)))

non_inter_tri_a = [[-1.152708, 0.000000, -1.318530],
                [1.039854, -0.000000, 1.339728],
                [1.039854, 0.000000, -1.318530]]

non_inter_tri_b = [[-3.696262, 0.000000, -1.318530],
                    [0.716440, -0.000000, 1.339728],
                    [-1.503700, 0.000000, -1.318530]]

print(py_tri_tri_intersection(*(non_inter_tri_a + non_inter_tri_b)))

print('tests passed.')
