import os
import re
import curses


from utils.coloring import *
from utils.logger import *
from utils.loading import load_solution_tags, load_tests_tags



def parse_tag(tag):
    """ parse tag """
    tag_parsing_ok = False
    tag_name = None
    compare_args = None
    tag = str(tag).strip()
    if re.match('[\w\(\)]+', tag):
        components = re.split('[()]', tag)
        # log(components)
        if len(components)>0:
            # search only for tag name
            tag_name = components[0]
            tag_parsing_ok = True
            if len(components)>1 and components[1]!="":
                compare_args = list(map(str, components[1].split(',')))
    return tag_parsing_ok, tag_name, compare_args


"""
c) for predicate in predicates -- resp while predicate not matches
        1. spracuj predicate
        2. vyhodnot predicate
        3. ak matchol, konci a vrat farbu ak je definovana, inak vrat Normal farbu
        4. ak nematchol pokracuj v cykle
        5. ak uz nie su dalsie predicates --> nezobrazuj info a chod dalej
    d) ak mas co zobrazit, pridaj zlava hodnotu v danej farbe + 1 medzeru
    e) ak nemas co zobrazit, pridaj zlava medzeru*length + 1 medzeru
"""
def parse_solution_info_predicate(predicate, solution_dir):

    red = curses.color_pair(HL_RED)
    green = curses.color_pair(HL_GREEN)
    blue = curses.color_pair(HL_BLUE)
    normal = curses.A_NORMAL

    total_match = True
    color = normal

    if 'predicate' in predicate:
        conditions = predicate['predicate']
        if len(conditions) > 0:
            for cond in conditions:
                cond = str(cond).strip()
                match = False
                # check if predicate condition refers to param from tag
                # matches: param2 FROM #tag_name(param1, param2, param3) > compare_with
                # if re.match("^\w+ FROM #\w+\(\w+(,\s*\w+)*\)", cond):
                # matches: tag_name.1 > 5
                if re.match("^\w+.[0-9]+\s*[<>=]\s*\w+$", cond):
                    components = re.split(r'([<>=])', cond)
                    tag = components[0].strip()
                    param = get_param_from_tag(tag, solution_dir)
                    if param is not None:
                        if len(components)==1:
                            # there is no comparison so predicate refers to existance of tag parameter
                            match = True
                        elif len(components)==3:
                            # compare given parameter from tag
                            op, value = components[1].strip(), components[2].strip()
                            if op in ['<','>'] and (not re.match(r'[0-9]+',value) or not re.match(r'[0-9]+',param)):
                                log("cannot compare string (must be number when using < > operand in predicate)")
                            else:
                                if op == '<': match = int(param) < int(value)
                                elif op == '>': match = int(param) > int(value)
                                elif op == '=': match = str(param) == str(value)
                                else:
                                    log("invalid operand in info predicate (in proj conf)")
                    else:
                        log("invalid info predicate (in proj conf)")
                elif cond == '':
                    # condition is empty
                    match = True
                else:
                    # predicate condition refers to existance of tag
                    # try to find given tag in solution tags
                    solution_tags = load_solution_tags(solution_dir)
                    if solution_tags is not None and len(solution_tags)>0:
                        match = solution_tags.find(cond)

                    # try to find given tag in tests tags
                    if not match:
                        solution_tests_dir = os.path.join(solution_dir, TESTS_DIR)
                        tests_tags = load_tests_tags(solution_tests_dir)
                        if tests_tags is not None and len(tests_tags)>0:
                            match = tests_tags.find(cond)
                if not match:
                    total_match = False
                    break

    if 'color' in predicate:
        col = str(predicate['color']).lower()
        if col == '': color = normal
        elif col == 'red': color = red
        elif col == 'green': color = green
        elif col == 'blue': color = blue

    return match, color



"""
returns visual + length
visual:
    * param (if visualization refers to param from tag)
    * None (if visualization refers to param from tag that doesnt exist or has no param) --> skip this info
    * string (if visualization is just string)
length:
    * length (if 'length' is defined)
    * 1 (if visualization refers to param from tag and 'length' is not defined)
    * len(string) (if visualization is just string and 'length' is not defined)
"""
def parse_solution_info_visualization(info, solution_dir):
    visualization = info['visualization'].strip()
    visual, length = None, None

    # check if visualization refers to param from tag
    # if re.match("^\w+ FROM #\w+\(\w+(,\s*\w+)*\)$", visualization):
    if re.match("^\w+.[0-9]+$", visualization):
        visual = get_param_from_tag(visualization, solution_dir)
        length = info['length'] if 'length' in info else 1
    else:
        visual = str(visualization)
        length = info['length'] if 'length' in info else len(visual)

    # alignment
    if visual is not None:
        if len(visual) != length: visual += ' '*(length-len(visual))

    # log("visual: "+str(visual))
    # log("length: "+str(length))
    return visual, length


def get_param_from_tag(txt, solution_dir):
    try:
        result = None
        txt.strip()
        # matches: param2 FROM #tag_name(param1, param2, param3)
        # if re.match("^\w+ FROM #\w+\(\w+(,\s*\w+)*\)$", txt):
        if re.match("^\w+.[0-9]+$", txt):
            components = re.split(r'[.]', txt)
            if len(components) == 2:
                tag_name, param_num = components
                if int(param_num) < 1:
                    log("get param from tag | param idx cant be less then 1 (parameter counting starts from 1)")
                    return None
                # check if tag has required param
                tag_param = find_tag_param_for_solution(solution_dir, tag_name, int(param_num)-1)
                log(tag_name)
                log(int(param_num)-1)
                log(tag_param)
                if tag_param is None:
                    log("get param from tag | tag not exist or has no param in required idx")
                    return None
                result = str(tag_param)
        return result
    except Exception as err:
        log("get param from tag | "+str(err))
        return None


def find_tag_param_for_solution(solution_dir, tag_name, param_idx):
    param = None
    # try to find required tag in solution tags
    solution_tags = load_solution_tags(solution_dir)
    if solution_tags is not None and len(solution_tags)>0:
        param = solution_tags.get_param_by_idx(tag_name, param_idx)
        if param is not None:
            return param

    # try to find required tag in tests tags
    solution_tests_dir = os.path.join(solution_dir, TESTS_DIR)
    tests_tags = load_tests_tags(solution_tests_dir)
    log(f"tags: {tests_tags}")
    if tests_tags is not None and len(tests_tags)>0:
        param = tests_tags.get_param_by_idx(tag_name, param_idx)
        log(f"param: {param}")
        if param is not None:
            return param
    return None


def find_tag_for_solution(solution_dir, tag_name):
    args = None
    # try to find required tag in solution tags
    solution_tags = load_solution_tags(solution_dir)
    if solution_tags is not None and len(solution_tags)>0:
        args = solution_tags.get_args_for_tag(tag_name)
        if args is not None:
            return list(args)

    # try to find required tag in tests tags
    solution_tests_dir = os.path.join(solution_dir, TESTS_DIR)
    tests_tags = load_tests_tags(solution_tests_dir)
    if tests_tags is not None and len(tests_tags)>0:
        args = tests_tags.get_args_for_tag(tag_name)
        if args is not None:
            return list(args)
    return args
