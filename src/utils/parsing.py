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
                if re.match("^\w+ FROM #\w+\(\w+(,\s*\w+)*\)", cond):
                    components = re.split('\)', cond)

                    # log(str(components))
                    if len(components)==2:
                        param, comparison = components
                        param = get_param_from_tag(str(param)+')', solution_dir)
                        if param is not None:
                            comparison = str(comparison).strip()
                            if comparison == "":
                                # there is no comparison so predicate refers to existance of tag parameter
                                match = True
                            else:
                                # compare given parameter from tag
                                if re.match("[<>=]\s*\w+$", comparison):
                                    op, value = comparison[0], str(comparison[1:]).strip()
                                    if op == '<': match = param < value
                                    elif op == '>': match = param > value
                                    elif op == '=': match = param == value
                                else:
                                    log("invalid comparison part in info predicate (in proj conf)")
                    else:
                        log("invalid info predicate (in proj conf)")
                elif cond == '':
                    # condition is empty
                    match = True
                else:
                    # predicate condition refers to existance of tag
                    succ, tag_name, tag_args = parse_tag(cond)
                    if succ and tag_name is not None:
                        # try to find given tag in solution tags (like in tag filter)
                        solution_tags = load_solution_tags(solution_dir)
                        if solution_tags is not None and len(solution_tags)>0:
                            match = solution_tags.find(tag_name, tag_args)

                        # try to find given tag in tests tags (like in tag filter)
                        if not match:
                            solution_tests_dir = os.path.join(solution_dir, TESTS_DIR)
                            tests_tags = load_tests_tags(solution_tests_dir)
                            if tests_tags is not None and len(tests_tags)>0:
                                match = tests_tags.find(tag_name, tag_args)
                    else:
                        log("invalid info predicate (in proj conf)")
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
    visualization = info['visualization']
    visual, length = None, None

    # check if visualization refers to param from tag
    if re.match("^\w+ FROM #\w+\(\w+(,\s*\w+)*\)$", visualization):
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

        # matches: param2 FROM #tag_name(param1, param2, param3)
        if re.match("^\w+ FROM #\w+\(\w+(,\s*\w+)*\)$", txt):
            req_param, tag  = re.split(' FROM #', txt)
            components = re.split('[()]', tag)
            if len(components) == 3:
                tag_name, tag_params, _ = components
                tag_params = [tag.strip() for tag in tag_params.split(',')]

                # check if tag exists
                matched_tag_params = find_tag_for_solution(solution_dir, tag_name)
                if matched_tag_params is not None:
                    # check if tag has required param
                    param_idx = 0
                    for idx, tag_param in enumerate(tag_params):
                        if tag_param == req_param:
                            param_idx = idx
                    
                    # log("tag_params: "+str(tag_params))
                    # log("req_param: "+str(req_param))
                    # log("param_idx: "+str(param_idx))
                    # log("matched_tag_params: "+str(matched_tag_params))
                    # log("len matched_tag_params: "+str(len(matched_tag_params)))

                    if len(matched_tag_params) > param_idx:
                        result = str(matched_tag_params[param_idx])
        return result
    except Exception as err:
        log("gat param from tag | "+str(err))
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
