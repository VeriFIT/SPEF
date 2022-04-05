
import curses
import curses.ascii
import yaml
import os
import traceback

from modules.buffer import Buffer, Report, Tags, Note

# from utils.printing import *
from utils.logger import *


REPORT_SUFFIX = "_report.yaml"
TAGS_SUFFIX = "_tags.yaml"
CONFIG_FILE = "config.yaml"
CONTROL_FILE = "control.yaml"
TYPICAL_NOTES_FILE = "typical_notes.txt"
PROJECT_FILE = "proj_conf.yaml"

REPORT_DIR = "reports"
TESTS_DIR = "tests"

SCORING_FILE = "scoring"
TEST_FILE = "dotest.sh"
TESTSUITE_FILE = "testsuite.sh"


""" **************** CONFIG **************** """
def load_config_from_file():
    utils_dir = os.path.dirname(__file__)
    src_dir = os.path.abspath(os.path.join(utils_dir, os.pardir))
    conf_file = os.path.join(src_dir, CONFIG_FILE)
    try:
        with open(conf_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as err:
        log("cannot load config file | "+str(err)+" | "+str(traceback.format_exc()))
        return None

def load_control_from_file():
    utils_dir = os.path.dirname(__file__)
    src_dir = os.path.abspath(os.path.join(utils_dir, os.pardir))
    control_file = os.path.join(src_dir, CONTROL_FILE)
    try:
        with open(control_file, 'r') as f:
            control = yaml.safe_load(f)
        return control
    except Exception as err:
        log("cannot load control file | "+str(err)+" | "+str(traceback.format_exc()))
        return None


""" **************** PROJECT **************** """
def load_proj_from_conf_file(path):
    # load data from yaml file
    project_file = os.path.join(path, PROJECT_FILE)
    try:
        with open(project_file, 'r') as f:
            data = yaml.safe_load(f)
        return data
    except Exception as err:
        log("cannot load project file | "+str(err)+" | "+str(traceback.format_exc()))
        return None

def save_proj_to_conf_file(path, data):
    project_file = os.path.join(path, PROJECT_FILE)
    try:
        with open(project_file, 'w+', encoding='utf8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except Exception as err:
        log("cannot save project conf to file | "+str(err)+" | "+str(traceback.format_exc()))



""" ************* TYPICAL NOTES ************* """
def get_typical_notes_file_name():
    utils_dir = os.path.dirname(__file__)
    src_dir = os.path.abspath(os.path.join(utils_dir, os.pardir))
    notes_file = os.path.join(src_dir, TYPICAL_NOTES_FILE)
    return notes_file

def load_typical_notes_from_file():
    notes_file = get_typical_notes_file_name()
    notes = []
    try:
        with open(notes_file, 'r') as f:
            lines = f.read().splitlines()

        """ parse notes to list of Note objects """
        for line in lines:
            notes.append(Note(line))
    except FileNotFoundError:
        return []
    except Exception as err:
        log("cannot load file with typical notes | "+str(err)+" | "+str(traceback.format_exc()))

    return notes


def save_typical_notes_to_file(notes):
    """ save list of Note objects to file """
    if notes:
        lines = []
        for note in notes:
            lines.append(note.text)

        notes_file = get_typical_notes_file_name()
        with open(notes_file, 'w+') as f:
            lines = '\n'.join(lines)
            f.write(lines)




""" **************** REPORT **************** """
def get_report_file_name(path):
    file_name = os.path.splitext(path)[:-1]
    return str(os.path.join(*file_name))+REPORT_SUFFIX

def load_report_from_file(path, add_suffix=True, orig_file_name=None):
    report_file = get_report_file_name(path) if add_suffix else path
    report = Report(report_file, [])
    try:
        with open(report_file, 'r') as f: # first line is comment with file name
            first_line = f.readline()
            if first_line.startswith('#'):
                orig_file_name = first_line[1:]
        with open(report_file, 'r') as f:
            data = yaml.safe_load(f)
        notes = []
        """ parse notes from directory to list of Note objects """
        for row in data:
            for col in data[row]:
                for text in data[row][col]:
                    note = Note(text, row=row, col=col)
                    notes.append(note)
        report = Report(report_file, notes)
    except yaml.YAMLError as err:
        pass
    except FileNotFoundError:
        pass
    except Exception as err:
        log("load report | "+str(err)+" | "+str(traceback.format_exc()))
    finally:
        report.orig_file_name = orig_file_name
        return report


def save_report_to_file(report):
    """ parse notes list of Note objects to directory """
    notes = {}
    for note in report.data:
        if note.row is not None and note.col is not None:
            if note.row in notes:
                if note.col in notes[note.row]:
                    notes[note.row][note.col].append(note.text)
                else:
                    notes[note.row][note.col] = [note.text]
            else:
                notes[note.row] = {note.col: [note.text]}
        else:
            notes[0][0].append(note.text)

    """ save data to file """
    try:
        with open(report.path, 'w+', encoding='utf8') as f:
            if report.orig_file_name is not None:
                f.write(f"#{report.orig_file_name}\n")
        with open(report.path, 'a', encoding='utf8') as f:
            yaml.dump(notes, f, default_flow_style=False, allow_unicode=True)
        report.last_save = report.data.copy()
    except Exception as err:
        log("save report to file | "+str(err)+" | "+str(traceback.format_exc()))


""" **************** TAGS **************** """
def get_tags_file_name(path):
    file_name = os.path.splitext(path)[:-1]
    return str(os.path.join(*file_name))+TAGS_SUFFIX

def load_tags_from_file(path):
    tags_file = get_tags_file_name(path)
    tags = None
    try:
        with open(tags_file, 'r') as f:
            data = yaml.safe_load(f)
        tags = Tags(tags_file, data)
    except yaml.YAMLError as err:
        tags = Tags(tags_file, {})
    except FileNotFoundError:
        tags = Tags(tags_file, {})
    except Exception as err:
        log("load tags | "+str(err)+" | "+str(traceback.format_exc()))

    return tags


def save_tags_to_file(tags):
    with open(tags.path, 'w+', encoding='utf8') as f:
        yaml.dump(tags.data, f, default_flow_style=False, allow_unicode=True)



""" **************** BUFFER AND TAGS **************** """
def load_buffer_and_tags(env):
    """ try load file content to buffer """
    file_already_loaded = False
    if env.buffer and env.buffer.path == env.file_to_open:
        file_already_loaded = True
        buffer = env.buffer
    else:
        try:
            with open(env.file_to_open, 'r') as f:
                lines = f.read().splitlines()
            buffer = Buffer(env.file_to_open, lines)
            env.buffer = buffer
        except UnicodeDecodeError as err:
            log("load file content ("+str(env.file_to_open)+") | "+str(err))
            return env, None, False
        except Exception as err:
            log("load file content ("+str(env.file_to_open)+") | "+str(err)+" | "+str(traceback.format_exc()))
            env.set_exit_mode()
            return env, None, False

    """ try load file tags to env - only for view, tags will not change """
    if (not env.tags or not file_already_loaded): # tag file wasnt loaded yet
        tags = load_tags_from_file(env.file_to_open)
        if tags is None:
            env.set_exit_mode()
            return env, None, False
        else:
            env.tags = tags

    return env, buffer, True
    # return env, buffer, succes



""" **************** SAVE BUFFER **************** """
def save_buffer(file_name, buffer, report=None):
    with open(file_name, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)
    buffer.last_save = buffer.lines.copy()
    if report:
        save_report_to_file(report)

