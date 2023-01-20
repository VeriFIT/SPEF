import curses
import re

from spef.utils.coloring import *
from spef.utils.logger import *
from spef.utils.match import get_tests_names


def parse_sum_equation(env, solution, sum_equation_str):
    equation = []
    ignored_tags = []
    first_term_is_none = False
    if sum_equation_str is not None:
        # sum_equation_str = ''.join(sum_equation_str)
        sum_equation_str = sum_equation_str.strip()
        if sum_equation_str.startswith("SUM="):
            sum_equation_str = sum_equation_str[4:]
            sum_equation_str = sum_equation_str.strip()
            if re.match(r"^\w+(\s*[\+\-\*]\s*\w+)*$", sum_equation_str):
                components = re.split(r"([\+\-\*])", sum_equation_str)

                if len(components) > 0:
                    term = components.pop(0)
                    term, ignored = parse_equation_term(env, solution, term)
                    ignored_tags.extend(ignored)
                    if term is not None:
                        equation.append(str(term))
                    else:
                        first_term_is_none = True
                else:
                    log("empty SUM equation")
                    return equation

                while len(components) >= 2:
                    op = components.pop(0)
                    term = components.pop(0)

                    op = parse_equation_operand(op)
                    term, ignored = parse_equation_term(env, solution, term)
                    ignored_tags.extend(ignored)
                    if op is not None and term is not None:
                        equation.append(op)
                        equation.append(str(term))
                    else:
                        equation.append("")
                        equation.append("")
            else:
                log("invalid SUM equation - doesnt match regex for equation")
        else:
            log("invalid SUM equation - doesnt start with 'SUM=' prefix ")
        if first_term_is_none and len(equation) > 0:
            equation = equation[1:]
    return equation, ignored_tags


def parse_equation_term(env, solution, term):
    term = str(term).strip()
    if term == "SUM_ALL_TESTS":
        # get all valid tests
        tests = get_tests_names(env)

        # for all test try to find its scoring tag in solution tags and tests tags
        result = 0
        skipped_tags = []
        for test in tests:
            tag_name = f"scoring_{test}"
            tag_args = find_tag_for_solution(solution, tag_name)
            if tag_args is not None and len(tag_args) > 0:
                # for valid tests with scoring tag add its scoring value to equation with '+'
                value = str(tag_args[0]).strip()
                try:
                    result = result + int(value)
                except ValueError:
                    log(f"firs param of tag '{tag_name}' is not a number")
                    skipped_tags.append(tag_name)
            else:
                log(f"tag '{tag_name}' not found in solution or tests tags")
                skipped_tags.append(tag_name)
        return result, skipped_tags
    else:
        tag_name = term
        if not term.startswith("scoring_"):
            # add default 'scoring_' prefix
            tag_name = f"scoring_{tag_name}"

        # try to find tag with scoring_ prefix in solution tags and tests tags
        tag_args = find_tag_for_solution(solution, tag_name)
        if tag_args is not None and len(tag_args) > 0:
            value = str(tag_args[0]).strip()
            try:
                result = int(value)
                return result, []
            except ValueError:
                log(f"firs param of tag '{tag_name}' is not a number")
                return None, [tag_name]
        else:
            return None, [tag_name]


def parse_equation_operand(op):
    op = str(op).strip()
    if op in "+-*":
        return op
    else:
        return None


# return parsing_ok, tag_name, tag_param, compare_to = (op, value)
def parse_tag(tag):
    parsing_ok = False
    tag_name, tag_param_num, compare_to = None, None, None
    tag = str(tag).strip()
    # matches: tag_name.1 > 5
    if re.match("^\w+.[0-9]+\s*[<>=]\s*\w+$", tag):
        components = re.split(r"([<>=])", tag)
        tag = str(components[0]).strip()

        # parse tag name and param
        tag_components = re.split(r"[.]", tag)
        if len(tag_components) == 2:
            tag_name, param_num = tag_components
            if int(param_num) > 0:
                tag_param_num = int(param_num)
                parsing_ok = True

        # parse tag comparison
        if len(components) == 3 and parsing_ok:
            op, value = str(components[1]).strip(), str(components[2]).strip()
            if op in ["<", ">"] and not re.match(r"[0-9]+", value):
                log(
                    "cannot compare string (must be number when using < > operand in predicate)"
                )
                parsing_ok = False
            elif op in ["<", ">", "="]:
                compare_to = (op, value)
            else:
                log("invalid operand in info predicate (in proj conf)")
                parsing_ok = False
    # matches: tag_name.1
    elif re.match("^\w+.[0-9]+$", tag):
        tag_components = re.split(r"[.]", tag)
        if len(tag_components) == 2:
            tag_name, param_num = tag_components
            if int(param_num) > 0:
                tag_param_num = int(param_num)
                parsing_ok = True
    # matches: tag_name
    else:
        tag_name = tag
        parsing_ok = True

    return parsing_ok, tag_name, tag_param_num, compare_to


def parse_solution_info_predicate(
    predicate, solution, info_for_tests=False, test_name=None
):
    # defined colors
    red = curses.color_pair(COL_RED)
    green = curses.color_pair(COL_GREEN)
    blue = curses.color_pair(COL_BLUE)
    normal = curses.A_NORMAL
    cyan = curses.color_pair(COL_CYAN)
    yellow = curses.color_pair(COL_YELLOW)
    orange = curses.color_pair(COL_ORANGE)
    pink = curses.color_pair(COL_PINK)

    color = normal
    match = False
    try:
        if "predicate" in predicate:
            conditions = predicate["predicate"]
            if len(conditions) > 0:
                for cond in conditions:
                    cond = str(cond).strip()
                    match = False
                    # check if predicate condition refers to param from tag
                    # matches: tag_name.1 > 5
                    if re.match("^\w+.[0-9]+\s*[<>=]\s*\w+$", cond):
                        components = re.split(r"([<>=])", cond)
                        tag = str(components[0]).strip()
                        param = get_param_from_tag(
                            tag,
                            solution,
                            info_for_tests=info_for_tests,
                            test_name=test_name,
                        )
                        if param is not None:
                            if len(components) == 1:
                                # there is no comparison so predicate refers to existance of tag parameter
                                match = True
                            elif len(components) == 3:
                                # compare given parameter from tag
                                op, value = (
                                    str(components[1]).strip(),
                                    str(components[2]).strip(),
                                )
                                if op in ["<", ">"] and (
                                    not re.match(r"[0-9]+", value)
                                    or not re.match(r"[0-9]+", param)
                                ):
                                    log(
                                        "cannot compare string (must be number when using < > operand in predicate)"
                                    )
                                else:
                                    if op == "<":
                                        match = int(param) < int(value)
                                    elif op == ">":
                                        match = int(param) > int(value)
                                    elif op == "=":
                                        match = str(param) == str(value)
                                    else:
                                        log(
                                            "invalid operand in info predicate (in proj conf)"
                                        )
                        # else:
                        # log(f"tag in predicate doesnt exist or has no param with given idx")
                    elif cond == "":
                        # condition is empty
                        match = True
                    else:
                        # predicate condition refers to existance of tag
                        # try to find given tag in solution tags
                        if not info_for_tests:
                            solution_tags = solution.tags
                            if solution_tags is not None and len(solution_tags) > 0:
                                match = solution_tags.find(cond)

                        # try to find given tag in tests tags
                        if not match:
                            tests_tags = solution.test_tags
                            if tests_tags is not None and len(tests_tags) > 0:
                                if info_for_tests and test_name is not None:
                                    cond = cond.replace("XTEST", test_name)
                                match = tests_tags.find(cond)
                    if not match:
                        break

        if "color" in predicate:
            col = str(predicate["color"]).lower()
            if col == "":
                color = normal
            elif col == "red":
                color = red
            elif col == "green":
                color = green
            elif col == "blue":
                color = blue
            elif col == "cyan":
                color = cyan
            elif col == "yellow":
                color = yellow
            elif col == "orange":
                color = orange
            elif col == "pink":
                color = pink
    except Exception as err:
        log("parse solution info predicate | " + str(err))

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


def parse_solution_info_visualization(
    info, solution, info_for_tests=False, test_name=None
):
    visualization = str(info["visualization"]).strip()
    visual, length = None, None

    # check if visualization refers to param from tag
    # matches: tag_name.1
    if re.match("^\w+.[0-9]+$", visualization):
        visual = get_param_from_tag(
            visualization, solution, info_for_tests=info_for_tests, test_name=test_name
        )
        length = info["length"] if "length" in info else 1
    else:
        visual = str(visualization)
        length = info["length"] if "length" in info else len(visual)

    # alignment
    if visual is not None:
        if len(visual) != length:
            visual += " " * (length - len(visual))

    # log("visual: "+str(visual))
    # log("length: "+str(length))
    return visual, length


def get_param_from_tag(txt, solution, info_for_tests=False, test_name=None):
    try:
        result = None
        txt = str(txt).strip()
        # matches: tag_name.1
        if re.match("^\w+.[0-9]+$", txt):
            components = re.split(r"[.]", txt)
            if len(components) == 2:
                tag_name, param_num = components
                if info_for_tests and test_name is not None:
                    tag_name = tag_name.replace("XTEST", test_name)
                if int(param_num) < 1:
                    log(
                        "get param from tag | param idx cant be less then 1 (parameter counting starts from 1)"
                    )
                    return None
                # check if tag has required param
                tag_param = find_tag_param_for_solution(
                    solution,
                    tag_name,
                    int(param_num) - 1,
                    info_for_tests=info_for_tests,
                )
                if tag_param is None:
                    # log("get param from tag | tag not exist or has no param in required idx")
                    return None
                result = str(tag_param)
        return result
    except Exception as err:
        log("get param from tag | " + str(err))
        return None


def find_tag_param_for_solution(solution, tag_name, param_idx, info_for_tests=False):
    param = None
    if not info_for_tests:
        # try to find required tag in solution tags
        solution_tags = solution.tags
        if solution_tags is not None and len(solution_tags) > 0:
            param = solution_tags.get_param_by_idx(tag_name, param_idx)
            if param is not None:
                return param

    # try to find required tag in tests tags
    tests_tags = solution.test_tags
    if tests_tags is not None and len(tests_tags) > 0:
        param = tests_tags.get_param_by_idx(tag_name, param_idx)
        if param is not None:
            return param
    return None


def find_tag_for_solution(solution, tag_name):
    args = None
    # try to find required tag in solution tags
    solution_tags = solution.tags
    if solution_tags is not None and len(solution_tags) > 0:
        args = solution_tags.get_args_for_tag(tag_name)
        if args is not None:
            return list(args)

    # try to find required tag in tests tags
    tests_tags = solution.test_tags
    if tests_tags is not None and len(tests_tags) > 0:
        args = tests_tags.get_args_for_tag(tag_name)
        if args is not None:
            return list(args)
    return args
