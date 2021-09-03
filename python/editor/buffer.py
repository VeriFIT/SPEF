


class Buffer:
    def __init__(self,lines):
        self.lines = lines

    def __len__(self):
        return len(self.lines)

    def __getitem__(self,index):
        return self.lines[index]

    @property
    def bottom(self):
        return len(self) - 1