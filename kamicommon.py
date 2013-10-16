class LinkedList(object):
    def __init__(self, head, tail):
        self.head, self.tail = head, tail

    def __iter__(self):
        n = self
        while n:
            yield n.head
            n = n.tail
