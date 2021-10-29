

""" represents content of current working directory """

class Directory:
    def __init__(self, path, dirs, files):
        self.path = path
        self.dirs = dirs
        self.files = files


    def __len__(self):
        return len(self.dirs) + len(self.files)


    def is_empty(self):
        return not (self.dirs or self.files)
 
    def get_shifted_dirs_and_files(self, shift):
        dirs_count = len(self.dirs)
        if shift == dirs_count:
            dirs = []
            files = self.files
        elif shift > dirs_count:
            dirs = []
            files = self.files[(shift-dirs_count):]
        else:
            dirs = self.dirs[shift:]
            files = self.files
        return dirs, files

    def get_all_items(self):
        items = self.dirs.copy()
        items.extend(self.files)
        return items

    # unused
    def get_shifted_items(self):
        items = self.get_all_items()
        return items[self.shift:]

