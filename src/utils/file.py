import os
import re
import glob
import shutil
import traceback
import tarfile
import zipfile

from utils.loading import *
from utils.printing import *
from utils.logger import *
from utils.match import *
from utils.reporting import *

# input: list of archive files
# output: set of problematic archives
def extract_archives(archives):
    problem_archives = set()
    for arch in archives:
        opener, mode = None, None
        if arch.endswith('.zip'):
            dest_dir = arch.removesuffix('.zip')
            opener, mode = zipfile.ZipFile, 'r'
        elif arch.endswith('.tar'):
            dest_dir = arch.removesuffix('.tar')
            opener, mode = tarfile.open, 'r'
        elif arch.endswith('.tar.gz') or arch.endswith('.tgz'):
            dest_dir = arch.removesuffix('.tar.gz').removesuffix('.tgz')
            opener, mode = tarfile.open, 'r:gz'
        elif arch.endswith('.tar.bz2') or arch.endswith('.tbz'):
            dest_dir = arch.removesuffix('.tar.bz2').removesuffix('.tbz')
            opener, mode = tarfile.open, 'r:bz2'
        elif arch.endswith('.tar.xz') or arch.endswith('.txz'):
            dest_dir = arch.removesuffix('.tar.xz').removesuffix('.txz')
            opener, mode = tarfile.open, 'r:xz'
        else:
            problem_archives.add(os.path.basename(arch))

        try:
            if opener and mode:
                with opener(arch, mode) as arch_file:
                    if not os.path.exists(dest_dir):
                        os.mkdir(dest_dir)
                    arch_file.extractall(dest_dir)
        except Exception as err:
            log("extract all from archive | "+str(err)+" | "+str(traceback.format_exc()))

    return problem_archives


def rename_solutions(src_dirs, required_name, extended_variants):
    ok, renamed, fail = [], [], []
    for solution in src_dirs:
        try:
            # find sut in solution dir
            file_list = glob.glob(os.path.join(solution, '**', required_name))
            if len(file_list) == 1: # only one file matches the sut required
                ok.append(solution)
            else:
                files = []
                for ext in extended_variants: # find extended version of sut in solution dir
                    files.extend(glob.glob(os.path.join(solution, '**', ext)))
                if len(files) == 1: # only one file matches some sut extened variant
                    old_file = files[0]
                    new_file = os.path.join(os.path.dirname(old_file), required_name)
                    shutil.copy(old_file, new_file)
                    renamed.append(solution)
                    add_tag_to_file(old_file, "renamed", ["-1b"])
                else:
                    fail.append(solution)
        except:
            fail.append(solution)
    return ok, renamed, fail