"""
This cass is for define a LinkedList to be sed in Hash_Table
"""


class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


class LinkedList:
    def __init__(self, key, value):
        new_node = Node(key, value)
        self.head = new_node
        self.tail = new_node
        self.length = 1

    def print_list(self):
        temp = self.head
        while temp:
            print(f"{temp.key}: {temp.value}")
            temp = temp.next
            if temp is None:
                return {'length': self.length}

    def append(self, key, value):
        new_node = Node(key, value)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node
        self.length += 1
        return True

    def pop(self):
        if self.length == 0:
            return None
        temp = self.head
        pre = self.head
        while temp.next:
            pre = temp
            temp = temp.next
        self.tail = pre
        self.tail.next = None
        self.length -= 1
        if self.length == 0:
            self.head = None
            self.tail = None
        return temp

    def prepend(self, key, value):
        new_node = Node(key, value)
        if self.length == 0:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head = new_node
        self.length += 1
        return True

    def pop_first(self):
        if self.length == 0:
            return None
        temp = self.head
        self.head = self.head.next
        temp.next = None
        self.length -= 1
        if self.length == 0:
            self.tail = None
        return temp

    def get(self, index):
        if index < 0 or index >= self.length:
            return None
        temp = self.head
        for _ in range(index):
            temp = temp.next
        return temp

    def set_value(self, index, value):
        temp = self.get(index)
        if temp:
            temp.value = value
            return True
        return False

    def insert(self, index, key, value):
        if index < 0 or index > self.length:
            return False
        if index == 0:
            return self.prepend(key, value)
        if index == self.length:
            return self.append(key, value)
        new_node = Node(key, value)
        temp = self.get(index - 1)
        new_node.next = temp.next
        temp.next = new_node
        self.length += 1
        return True

    def remove(self, key):
        index = 0
        if self.get(0).key == key:
            return self.pop_first()
        elif self.get(self.length-1).key == key:
            return self.pop()

        for index in range(1, self.length-1):
            if self.get(index).key == key:
                pre = self.get(index - 1)
                temp = pre.next
                pre.next = temp.next
                temp.next = None
                self.length -= 1

    def reverse(self):
        temp = self.head
        self.head = self.tail
        self.tail = temp
        after = temp.next
        before = None
        for _ in range(self.length):
            after = temp.next
            temp.next = before
            before = temp
            temp = after

# my_list = LinkedList('bus0', {'x': 12, 'y': 13})
# my_list.append('bus1', {'x': 1, 'y': 134})
# my_list.append('bus2', {'x': 1, 'y': 134})
# my_list.print_list()
#
# print(my_list.length)
