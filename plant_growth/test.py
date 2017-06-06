import numpy as np
import heapq

def light(self, plant):
    minheap = []

    # TODO: compare with merge sort and insertion sort for speed.
    cells_indexes_ordered = np.asarray(plant.cell_x[:plant.max_i]).argsort()

    for i in range(plant.max_i):
        plant.cell_light[i] = 0

    for i in range(plant.max_i):
        cid = cells_indexes_ordered[i]
        
        # Neither dead nor underground cells collect light.
        if not plant.cell_alive[cid]:
            continue

        is_lit = False
        x0 = plant.cell_x[cid]
        y0 = plant.cell_y[cid]

        cid_prev = plant.cell_prev[cid]
        cid_next = plant.cell_next[cid]

        if plant.cell_x[cid_prev] < x0:
            minheap.remove((-plant.cell_y[cid_prev], (cid_prev, cid)))

        if plant.cell_x[cid_next] < x0:
            minheap.remove((-plant.cell_y[cid_next], (cid_next, cid)))

        if len(minheap) == 0:
            is_lit = True

        else:
            y1, (cid_left, cid_right) = minheap[0]
            y1 *= -1
            x1 = plant.cell_x[cid_left]
            x2 = plant.cell_x[cid_right]
            y2 = plant.cell_y[cid_right]

            # See if cell is to the right or above the currect active segment.
            slope = (y2 - y1) / (x2 - x1)
            is_lit = (y0 >= slope * (x0 - x1) + y1)

        if plant.cell_x[cid_prev] > x0:
            heapq.heappush(minheap, (-y0 , (cid, cid_prev)))

        if plant.cell_x[cid_next] > x0:
            heapq.heappush(minheap, (-y0 , (cid, cid_next)))

        if is_lit and y0 >= self.soil_height:
            plant.cell_light[cid] = 1

    assert len(minheap) == 0