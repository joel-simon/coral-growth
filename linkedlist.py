
class DoubleList(object):
    def __init__(self):
        self.head = None
        self.tail = None
        self._n = 0

    def insert_before(self, node, new_node):
        prev = node.prev
        prev.next = new_node
        new_node.prev = prev
        new_node.next = node
        node.prev = new_node

        if node == self.head:
            self.head = new_node

        self._n += 1

    def insert_after(self, node, new_node):
        next = node.next
        next.prev = new_node
        new_node.prev = node
        new_node.next = next
        node.next = new_node

        if node == self.tail:
            self.tail = new_node

        self._n -= 1

    def append(self, new_node):
        if self.head is None:
            self.head = self.tail = new_node
        else:
            new_node.prev = self.tail
            new_node.next = self.head
            self.tail.next = new_node
            self.tail = new_node

            self.head.prev = self.tail

        self._n += 1

    # def remove(self, node):
        # node.prev.next = node.next
        # node.next.prev = node.prev
        # node.next = None
        # node.prev = None
        # self._n -= 1

    def __len__(self):
        return self._n

    def __iter__(self):
        if self.head == None:
            yield
        elif self.head == self.tail:
            yield self.head
        else:
            current_node = self.head
            while current_node != self.tail:
                yield current_node
                current_node = current_node.next
            yield self.tail


if __name__ == '__main__':
    ll = DoubleList()
    print(list(map(str, ll)))
    for i in range(10):
        if i == 1:
            print(list(map(str, ll)))
        c = Cell(i)
        ll.append(c)

    print(list(map(str, ll)))
