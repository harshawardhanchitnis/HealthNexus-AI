"""Predictable bounded LRU retention. Eviction never changes calculation inputs."""
from collections import OrderedDict


class BoundedCache(OrderedDict):
    def __init__(self, limit):
        super().__init__()
        self.limit = limit

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > self.limit:
            self.popitem(last=False)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            self[key] = value
