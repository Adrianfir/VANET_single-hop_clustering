"""
This Class is for building Hash_Table to store the data from XML file obtained from SUMO.
The Hash-Table is an array of 'LinekdList' so called 'chain structure'
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

import LinkedList


class HashTable:

    # size is the size of the Hash_Table and it should be a prime number
    # to increase the randomness
    def __init__(self, size):
        self.data_map = [None] * size

    def hash_index(self, key):
        """
        :param key: is the index that we want to refer to it in order to generate index in Hash_Table
        :return: my_hash which is the generated key related to the Hash_Table
        """
        my_hash = 0
        for letter in key:
            my_hash = (my_hash + ord(letter) * 31) % len(self.data_map)
        return my_hash

    def set_item(self, key, value):
        """

        :param key: is the car_id
        :param value: details about the relevant car
        :return: True if it is correct
        """
        index = self.hash_index(key)
        if self.data_map[index] is None:
            self.data_map[index] = LinkedList.LinkedList(key, value)
            return True
        self.data_map[index].append(key, value)
        return True

    def car_values(self, key):
        """

        :param key: for example 'bus0' or 'vehicle36'
        :return: the values related to each car
        """
        # Here, the values are trying to get retrieved from linkedlist inside the Hash_Table
        index = self.hash_index(key)
        if self.data_map[index]:
            temp = self.data_map[index].head
            while temp:
                if temp.key is key:
                    return temp.value
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
                    all_keys.append(temp.key)
                    temp = temp.next
        return all_keys

    def print_hash_table(self):
        for index in range(self.data_map.__len__()):
            if self.data_map[index]:
                print(f"{index}:")
                print(f"{self.data_map[index].print_list()}")


# table = HashTable(10)
# table.set_item('bus0', {'x': 12, 'y': 13})
# table.set_item('bus0', {'x': 15, 'y': 14})
# table.set_item('bus1', {'x': -1, 'y': 1})
# print(table.car_values('bus1'))

