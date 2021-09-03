


class Content:
    def __init__(self, path, dirs, files):
        self.path = path
        self.dirs = dirs
        self.files = files
        self.item_count = len(self.dirs) + len(self.files)
        self.position = 1
        self.shift = 0

    def go_up(self):
        if self.position > 1: # current position is not on first item
            self.position -= 1
        # else:
            # self.position = self.item_count

    def go_down(self):
        if self.position < self.item_count: # current position is not on last item
            self.position += 1
        # else:
            # self.position = 1

    def up_shift(self):
        self.shift += 1

    def down_shift(self):
        if self.shift >= 1:
            self.shift -= 1

    def is_empty(self):
        return not (self.dirs or self.files)
 
    def get_all_items(self):
        items = self.dirs
        items.extend(self.files)
        return items

    def get_shifted_items(self):
        items = self.get_all_items()
        return items[self.shift:]

    def get_shifted_dirs_and_files(self):
        dirs_count = len(self.dirs)
        if self.shift == dirs_count:
            dirs = []
            files = self.files
        elif self.shift > dirs_count:
            dirs = []
            files = self.files[(self.shift-dirs_count):]
        else:
            dirs = self.dirs[self.shift:]
            files = self.files
        return dirs, files

