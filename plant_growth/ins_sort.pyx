cdef void ins_sort(double[:] k):
    cdef n = len(k)
    for i in range(1, n):    #since we want to swap an item with previous one, we start from 1
        j = i                    #bcoz reducing i directly will mess our for loop, so we reduce its copy j instead
        while j > 0 and k[j] < k[j-1]: #j>0 bcoz no point going till k[0] since there is no value to its left to be swapped
            k[j], k[j-1] = k[j-1], k[j] #syntactic sugar: swap the items, if right one is smaller.
            j = j - 1 #take k[j] all the way left to the place where it has a smaller/no value to its left.
    # return k
