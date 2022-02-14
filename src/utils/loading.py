
import curses
import curses.ascii
import yaml
import os


from modules.buffer import Buffer, Report, Tags

# from utils.printing import *
from utils.logger import *


""" **************** REPORT **************** """
def get_report_file_name(path):
    file_name = os.path.splitext(path)[:-1]
    return str(os.path.join(*file_name))+"_report.yaml"

def load_report_from_file(path):
    report_file = get_report_file_name(path)
    report = None
    try:
        with open(report_file, 'r') as f:
            data = yaml.safe_load(f)
        report = Report(report_file, data)
    except yaml.YAMLError as err:
        report = Report(report_file, {})
    except FileNotFoundError:
        report = Report(report_file, {})
    except Exception as err:
        log("load report | "+str(err))

    return report



""" **************** TAGS **************** """
def get_tags_file_name(path):
    file_name = os.path.splitext(path)[:-1]
    return str(os.path.join(*file_name))+"_tags.yaml"

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
        log("load tags | "+str(err))

    return tags



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
        except Exception as err:
            log("load file content | "+str(err))
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



""" **************** SAVE BUFFER AND REPORT **************** """

def save_buffer(file_name, buffer, report=None):
    with open(file_name, 'w') as f:
        lines = '\n'.join(buffer.lines)
        f.write(lines)
    buffer.set_save_status(True)
    buffer.last_save = buffer.lines.copy()
    if report:
        save_report_to_file(report)
        report.last_save = report.code_review.copy()


def save_report_to_file(report):
    with open(report.path, 'w+', encoding='utf8') as f:
        yaml.dump(report.code_review, f, default_flow_style=False, allow_unicode=True)