import queue
import numpy as np
class Cell:
    def __init__(self, x, y, h):
        self.x, self.y, self.h = x, y, h

    def __lt__(self, other):
        return self.h < other.h
    # def __cmp__(self, other):
    #     if self.h < other.h:
    #         return -1
    #     elif self.h > other.h:
    #         return 1
    #     else:
    #         return 0

class Solution:
    # @param heights: a matrix of integers
    # @return: an integer
    def __init__(self):
        self.dx = [1,-1,0,0]
        self.dy = [0,0,1,-1]

    def trapRainWater(self, heights):
        q = queue.PriorityQueue()
        n = heights.shape[0]
        m = heights.shape[1]
        visit = [[False for i in range(m)] for i in range(n)]

        for i in range(n):
            q.put(Cell(i, 0, heights[i][0]))
            q.put(Cell(i, m-1, heights[i][m-1]))
            visit[i][0] = True
            visit[i][m-1] = True

        for i in range(m):
            q.put(Cell(0, i, heights[0][i]))
            q.put(Cell(n-1, i, heights[n-1][i]))
            visit[0][i] = True
            visit[n-1][i] = True

        ans = 0
        while not q.empty():
            now = q.get()
            for i in range(4):
                nx = now.x + self.dx[i]
                ny = now.y + self.dy[i]
                if 0 <= nx and nx < n and 0 <= ny and ny < m and not visit[nx][ny]:
                    visit[nx][ny] = True
                    q.put(Cell(nx, ny, max(now.h,heights[nx][ny])))
                    ans += max(0, now.h - heights[nx][ny])

        return ans

def water_hold(mesh, grid_size):
    min_x, _, min_z = list(mesh.verts[0].p)
    max_x, _, max_z = list(mesh.verts[0].p)
    grid = dict()

    for vert in mesh.verts:
        x = int(vert.p[0] / grid_size )
        z = int(vert.p[2] / grid_size )

        min_x = min(min_x, x)
        min_z = min(min_z, z)
        max_x = max(max_x, x)
        max_z = max(max_z, z)

        grid[(x, z)] = max(grid.get((x, z), 0), vert.p[ 1 ])

    heights = np.zeros((max_x-min_x+1, max_z-min_z+1))

    for (x, z), y in grid.items():
        # print(x, z), y
        heights[x, z] = y

    sol = Solution()
    return sol.trapRainWater(heights)
