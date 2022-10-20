"""
This Class is for building Hash_Table to store the data from XML file. The Hash-Table is a an array of LinekdList
so called 'chain structure'
"""
__author__ = "Adrian (Pouya) Firouzmakan"
__all__ = []

class HashTable():

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

    def print_hash_table(self):
        for i, val in enumerate(self.data_map):
            print(f"{i} : {val}")

    def set_item(self, key, value):
        index = self.__hash(key)
        if self.data_map[index] is None:
            self.data_map[index] = value
        else:

