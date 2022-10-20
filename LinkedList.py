"""
This cass is for define a LinkedList to be sed in Hash_Table
"""
class Node:
    def __init__(self,value):
        self.value = value
        self.next = None


class LinkedList:
    def __init__(self, value):
        new_node = Node(value)
        self.head = new_node
        self.tail = new_node
        self.length = 1

    def append(self, value):
        new_node = Node(value)
        if self.length is 0:
            self.head = new_node
            self.tail = new_node
        self.tail.next = new_node
        self.tail = new_node
        self.length += 1

    def isnert(selfself, index , value):


    def print_list(self):
        temp = self.head
        while temp:
            print(f"{i} : {temp.value}")
            temp = temp.next


