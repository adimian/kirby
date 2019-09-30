from .external import External


class Files (External):
    def __init__(self, name, folder):
        super().__init__(name)
        self.folder = folder
