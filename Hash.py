"""
This Class is for building Hash_Table to store the data from XML file. The Hash-Table is a an array of LinekdList
so called 'chain structure'
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import LinkedList


class HashTable:

    # size is the size of the Hash_Table and it should be a prime number
    # to increase the randomness
    def __init__(self, size):
        self.data_map = [None] * size

    def __hash(self, key):
        """
        :param key: is the index that we want to refer to it in order to generate index in Hash_Table
        :return: my_hash which is the generated key related to the Hash_Table
        """
        my_hash = 0
        for letter in key:
            my_hash = (my_hash + ord(letter) * 31) % len(self.data_map)
        return my_hash

    def set_item(self, key, value):
        index = self.__hash(key)
        if self.data_map[index] is None:
            self.data_map[index] = LinkedList.LinkedList(None)
        self.data_map[index].append(key, value)

    def car_values(self, key):
        """

        :param key: for example 'bus0' or 'vehicle36'
        :return: the values related to each car
        """
        # Here, the values are trying to get retrieved from linkedlist inside the Hash_Table
        index = self.__hash(key)
        if self.data_map[index]:
            temp = self.data_map[index].head
            while temp:
                if temp[0] is key:
                    return temp[1]
                temp = temp.next
            return None

    def cars_id(self):
        """

        :return: this method will return all the cars id
        """
        all_keys = []
        for i in range(len(self.data_map)):
            if self.data_map[i]:
                temp = self.data_map[i].head
                while temp:
                    all_keys.append(temp[0])
                    temp = temp.next
        return all_keys

    def print_hash_table(self):
        for i, val in enumerate(self.data_map):
            print(f"{i} : {self.data_map.print_list}")
