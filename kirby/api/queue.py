class Queue:
    def __init__(self, name, testing=False):
        self.name = name
        self.testing = testing
        if testing:
            self.__messages = []
        else:
            raise NotImplementedError("queue is only for testing for now")

    def append(self, message):
        if self.testing:
            self.__messages.append(message)

    def last(self):
        if self.testing:
            return self.__messages[-1]
