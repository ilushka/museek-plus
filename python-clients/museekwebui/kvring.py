""" A dictionary that stores only last N values. """

import logging

logging.basicConfig(level=logging.INFO)

class KeyValueRing(object):
    """ A dictionary that stores only last N values. """

    def __init__(self, max_count):
        self.dict = {}
        self.queue = []
        self.max_count = max_count

    def set(self, key, value):
        """ Set new value for specified key. If key already exists it is
            overwritten and value is marked as the newest value """

        logging.debug("set: %s => %s", key, value)

        # do we need to remove existing key from queue?
        oldval = self.dict.get(key, None)
        if oldval is not None:
            del self.queue[oldval["qindex"]]

        if len(self.queue) >= self.max_count:
            del self.dict[self.queue.pop(0)]

        # at this point only <= max_count of elements should be stored in ring
        # and we know that new key will be at len(self.queue) position

        # insert key/value
        self.dict[key] = {"qindex": len(self.queue), "value": value}
        self.queue.append(key)

        if len(self.dict) != len(self.queue):
            logging.critical("Size of dictionary should always equal size of queue.")

    def get(self, key):
        """ Get value for specified key. """

        value = self.dict.get(key, None)
        logging.debug("get: %s => %s", key, value)
        if value is not None:
            value = value["value"]
        return value

    def get_all(self):
        """ Retrieve complete dictionary. """

        logging.debug("get_all")
        return self.dict

    def __len__(self):
        return len(self.queue)

    def __str__(self):
        string = ""
        for key in self.queue:
            string += (key + ": " + self.dict[key] + ", ")
        return string
