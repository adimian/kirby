from abc import ABC


class External(ABC):
    def __init__(self, name):
        self.name = name
