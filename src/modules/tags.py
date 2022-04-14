import os
import json
import yaml
import re

from utils.logger import *


"""
data = {'documentation': ['ok'],
        'test0': [],
        'test1': ['5', '4', '8'],
        'test2': ['5']}
"""
class Tags:
    def __init__(self, path, data):
        self.path = path
        self.data = data # {"tag_name": [param1, param2], "tag_name": []}

    def __str__(self):
        return str(self.data)

    def __len__(self):
        return len(self.data)

    def remove_tag(self, tag_name):
        if tag_name in self.data:
            del self.data[tag_name]

    def remove_tag_by_idx(self, idx):
        for i, key in enumerate(self.data):
            if i == idx:
                del self.data[key]
                return

    def get_tag_by_idx(self, idx):
        for i, key in enumerate(self.data):
            if i == idx:
                # log(self.data[key])
                return key, self.data[key]
        return None, None

    def get_param_by_idx(self, tag_name, idx):
        if tag_name in self.data:
            tag_args = self.data[tag_name]
            if idx < len(tag_args):
                return tag_args[idx]
        return None

    def set_tag(self, tag_name, args):
        self.data[tag_name] = [*args]

    # return arguments for tag_name if exists (else returns None)
    def get_args_for_tag(self, tag_name):
        for key in self.data:
            if re.search(tag_name, key):
                return self.data[key]
        return None

    def find(self, tag_name, args=None):
        for key in self.data:
            if re.search(tag_name, key):
                if args is not None:
                    return self.compare_args(self.data[key], args)
                else:
                    return True
        return False

    def compare_args(self, tag_args, compare_args):
        if len(compare_args) != len(tag_args):
            return False
        for i in range(len(compare_args)):
            if not re.search(str(compare_args[i]), str(tag_args[i])):
                return False
        return True
