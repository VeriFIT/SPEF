import glob
import os
import re
import traceback

from spef.utils.loading import get_tags_file, load_tags_from_file
from spef.utils.logger import log
from spef.utils.match import (
    filter_intern_files,
    get_root_tests_dir,
    get_root_solution_dir,
)
from spef.utils.parsing import parse_tag


""" class for currently set filters (by path, file content or tag) """


class Filter:
    def __init__(self, root):
        self.root = root  # root path

        self.path = None
        self.content = None
        self.tag = None

        self.aggregate = False
        self.aggregate_dirs = []
        self.aggregate_files = []
        self.files = []

    def is_empty(self):
        return not (self.path or self.content or self.tag)

    """ add filter by path """

    def add_path(self, path):
        self.path = path

    """ add filter by file content """

    def add_content(self, content):
        self.content = content

    """ add filter by tag """

    def add_tag(self, tag):
        tag_parsing_ok, _, _, _ = parse_tag(tag)
        if not tag_parsing_ok:
            log("invalid input for tag filter")
        else:
            self.tag = tag

    """ search for files with match of all set filters in root directory """

    def find_files(self, env):
        matches = []

        if self.path:
            matches = self.get_files_by_path(self.root, self.path)

        if self.content:
            # if some filtering has already been done, search for files only in its matches
            # else search all files in root directory
            files = matches if self.path else self.get_files_in_dir_recursive(self.root)
            matches = self.get_files_by_content(files)

        if self.tag:
            files = (
                matches
                if (self.path or self.content)
                else self.get_files_in_dir_recursive(self.root)
            )
            matches = self.get_files_by_tag(env, files)

        filtered_files = []
        for file_path in matches:
            file_name = os.path.relpath(file_path, self.root)
            filtered_files.append(file_name)

        filtered_files = filter_intern_files(
            filtered_files, keep_reports_and_tests=True
        )
        filtered_files.sort()

        # aggr_files, aggr_dirs = self.group_by_prefix(filtered_files)
        aggr_files, aggr_dirs = self.aggregate_by_same_tags_file(env, filtered_files)

        self.aggregate_files = aggr_files
        self.aggregate_dirs = aggr_dirs
        self.files = filtered_files

    def aggregate_by_same_tags_file(self, env, src_files):
        files = set()
        dirs = set()
        if len(src_files) > 0 and env.cwd.proj is not None:
            for i in src_files:
                match = False
                i_path = os.path.join(self.root, i)
                i_tag_file = get_tags_file(i_path, env.cwd.proj)
                for j in src_files:
                    if i != j:
                        j_path = os.path.join(self.root, i)
                        j_tag_file = get_tags_file(j_path, env.cwd.proj)
                        if j_tag_file == i_tag_file and i_tag_file is not None:
                            rel_path = os.path.relpath(i_tag_file, self.root)
                            dirs.add(os.path.dirname(rel_path))
                            match = True
                            break

                if not match:
                    if os.path.isdir(i_path):
                        dirs.add(i)
                    else:
                        files.add(i)
        else:
            return src_files, []

        files, dirs = list(files), list(dirs)
        files.sort()
        dirs.sort()
        return files, dirs

    def group_by_prefix(self, files):
        res = set()
        if len(files) > 0:
            for i in files:
                match = False
                for j in files:
                    if i != j:
                        pref = os.path.commonpath([i, j])
                        if pref:
                            match = True
                            break
                if match:
                    res.add(pref)
                else:
                    res.add(i)
        else:
            return files, []

        files = []
        dirs = []
        for item in res:
            path = os.path.join(self.root, item)
            if os.path.isdir(path):
                dirs.append(item)
            else:
                files.append(item)
        files.sort()
        dirs.sort()
        return files, dirs

    """ remove all filteres """

    def reset_all(self):
        self.path = None
        self.content = None
        self.tag = None

    """ remove filter according to current mode (ex: if broswing, remove filter by path) """

    def reset_by_current_mode(self, env):
        if env.is_brows_mode():
            self.path = None
        if env.is_view_mode():
            self.content = None
        if env.is_tag_mode():
            self.tag = None

    """ set filter according to current mode """

    def add_by_current_mode(self, env, text):
        if env.is_brows_mode():
            self.path = text
        if env.is_view_mode():
            self.content = text
        if env.is_tag_mode():
            self.tag = text

    """ returns list of all files in directory (recursive) """

    def get_files_in_dir_recursive(self, dir_path):
        files = []
        for root, dirnames, filenames in os.walk(dir_path):
            files.extend(os.path.join(root, filename) for filename in filenames)
        return files

    """
    src: source directory path
    dest: destination path to match
    """

    def get_files_by_path(self, src, dest):
        try:
            path_matches = []
            dest_path = os.path.join(src, "**", dest + "*")
            for file_path in glob.glob(dest_path, recursive=True):
                if os.path.isfile(file_path):
                    path_matches.append(file_path)
            return path_matches
        except Exception as err:
            log("Filter by path | " + str(err) + " | " + str(traceback.format_exc()))
            return []

    """
    files: files to filter
    content: content to match
    """

    def get_files_by_content(self, files):
        content_matches = []
        exception_catched = []
        problematic_files = []
        for file_path in files:
            try:
                with open(file_path, "r") as f:
                    if self.content in f.read():
                        content_matches.append(file_path)
            except Exception as err:
                # if there is some exception, skip this file
                exception_catched.append((str(err), str(traceback.format_exc())))
                problematic_files.append(file_path)
                pass

        if exception_catched:
            pass
            log(
                "Filter by content | some exception catched (probably bcs of some files that couldnt be opened)..."
            )
            # log(problematic_files)
            # log(exception_catched)
        return content_matches

    """
    files: files to filter
    tag: tag to match, ex: "test1(0,.*,2,[0-5],5)"
    """

    def get_files_by_tag(self, env, files):
        try:
            succ, tag_name, tag_param_num, compare_to = parse_tag(self.tag)
            if not succ or tag_name is None:
                return set()

            tag_matches = set()
            for file_path in files:
                tags = None
                if env.cwd.proj is not None:
                    # if file_path is in solution dir, tags are saved in proj.solutions (no need to load tags from file)
                    solution_root_dir = get_root_solution_dir(
                        env.cwd.proj.solution_id, file_path
                    )
                    tests_root_dir = get_root_tests_dir(file_path)
                    if solution_root_dir is not None:
                        solution_name = os.path.basename(solution_root_dir)
                        if solution_name in env.cwd.proj.solutions:
                            if tests_root_dir is not None:
                                tags = env.cwd.proj.solutions[solution_name].test_tags
                            else:
                                tags = env.cwd.proj.solutions[solution_name].tags
                if tags is None:
                    tags = load_tags_from_file(file_path)

                if tags and len(tags) > 0:
                    # find tag_name
                    if tags.find(tag_name):
                        if tag_param_num is None:
                            tag_matches.add(file_path)
                        else:
                            # find tag param
                            param = tags.get_param_by_idx(tag_name, tag_param_num - 1)
                            if param is not None:
                                match = True
                                if compare_to is not None:
                                    # compare tag param
                                    op, value = compare_to
                                    match = False
                                    if op in ["<", ">"] and not re.match(
                                        r"[0-9]+", str(param)
                                    ):
                                        continue
                                    if op == "<":
                                        match = int(param) < int(value)
                                    elif op == ">":
                                        match = int(param) > int(value)
                                    elif op == "=":
                                        match = str(param) == str(value)
                                if match:
                                    tag_matches.add(file_path)
            res = list(tag_matches)
            res.sort()
            return res
        except Exception as err:
            log("Filter by tag | " + str(err) + " | " + str(traceback.format_exc()))
            return files
