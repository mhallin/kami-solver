class LinkedList(object):
    def __init__(self, head, tail):
        self.head, self.tail = head, tail
        self.length = self.tail.length + 1 if self.tail else 1

    def __iter__(self):
        n = self
        while n:
            yield n.head
            n = n.tail

    def __len__(self):
        return self.length
