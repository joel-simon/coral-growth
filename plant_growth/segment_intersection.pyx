# http://www.geeksforgeeks.org/given-a-set-of-line-segments-find-if-any-two-segments-intersect/
import numpy as np
from sortedcontainers import SortedDict

from plant_growth.geometry import intersect
# from bintrees import FastRBTree

intersect(float p0_x, float p0_y, float p1_x, float p1_y,
                    float p2_x, float p2_y, float p3_x, float p3_y)

def segment_intersections(x, y):
	"""
	Return a list of tuples of segment pairs that intersect.
	There are n segments where segment i has point indexes s1[i], s2[i]

	Args:
		x: array of x positions
		y: array of y positions
		# s1: array of starting points of segments
		# s2: array of ending points of segments

	Returns:
		A list of two tuples of integers. [(i:int, j:int), ... ]

	Raises:
		None
	"""

	n_points = x.shape[0]
	# n_segments = s1.shape[0]

	# Sort points from left to right.
	ordered_points = np.argsort(x)

	# Create self balancing binary search tree.
	# It will contain all active line segments ordered by y coordinate.
	# T = FastRBTree()
	T = SortedDict() # map y-position to cell_index

	# # Map point to segments they start and end. 
	# starts_segment = np.zeros(n_points, dtype='i') - 1
	# ends_segments = np.zeros(n_points, dtype='i') - 1

	# i_to_j = np.zeros(n_points, dtype='i')
	# for k in range(0, n_points, 2):
	# 	i = 

	# for i in range(s1.shape[0])
	# 	starts_segments[s1[i]] = i
	# 	ends_segments[s2[i]] = i

	# Iterate across the points from left to right.
	for i in ordered_points:
		if (i % 2) == 0:
			j = i + 1
		else:
			j = i - 1

		x1 = x[i]
		y1 = y[i]

		x2 = x[j]
		y2 = y[j]

		y_index = T.index(y1)
		i_next = T[y_index + 1]
		i_prev = T[y_index - 1]

		# If this point is left end of its line
		if x1 < x2:
			T[x1] = i

		else:
			T.remove()