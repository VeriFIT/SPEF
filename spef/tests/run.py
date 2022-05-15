#!/usr/bin/env python3

import os
import shutil
import threading
import time
import traceback
import yaml

from subprocess import Popen, PIPE
from pathlib import Path

from key_values import kth


HOME = Path(os.path.join(os.getcwd(), Path(__file__))).parents[1]
SRC = os.path.join(HOME, 'src')
MAIN = os.path.join(SRC, 'main.py')
TYPICAL_NOTES_FILE = os.path.join(SRC, 'data', 'typical_notes.txt')
USER_LOGS_FILE = os.path.join(SRC, 'data', 'logs.csv')


class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout, data):
        def target():
            self.process = Popen(self.cmd, shell=True, stdin=PIPE, stdout=PIPE)
            self.process.communicate(input=data.encode('utf-8'))

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.process.kill()
            thread.join()
            print("process killed bcs of timeout")


"""
Vytvorenie a uprava suboru
* som v prazdnom adresari
1. vytvor novy subor "test"
2. otvor subor na upravu
3. zapis do suboru text: "This is\n...test"
4. uloz subor
5. skontroluj existenciu suboru "test" a jeho obsah
"""
def test1():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test1')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['3'] # select option "create new file"
        data += kth['t']+kth['e']+kth['s']+kth['t']
        data += kth['ENTER']
        data += kth['TAB'] # open file for edit
        data += kth['T']+kth['h']+kth['i']
        data += kth['e']
        data += kth['BACKSPACE']
        data += kth['s']
        data += kth['space']
        data += kth['i']+kth['s']
        data += kth['ENTER']
        data += kth['.']*3
        data += kth['t']+kth['e']+kth['s']+kth['t']
        data += kth['F2'] # save file
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        test_file = os.path.join(work_dir, 'test')
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                file_content = f.read()
                if file_content == "This is\n...test":
                    test_pass = True
        if len(os.listdir(work_dir)) != 1:
            test_pass = False

        time_passed = str(round(end-start,2))
        print("Test1........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test1 | {err} | "+str(traceback.format_exc()))


"""
Pridavanie poznamok
* som v adresari test2 v ktorom su subory: test1, test2, test3
1. otvor subor test2 na upravu
2. vloz poznamku na prvy riadok s obsahom "note"
3. otvor mgmt poznamok
4. uloz poznamku ako typicku
5. skontroluj obsah suboru s typickymi poznamkami
6. skontroluj existenciu suboru s poznamkami k suboru "test"
"""
def test2():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test2')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)
    with open(os.path.join(work_dir, 'test1'), 'w+') as f:
        f.write("This is test1\nfile...")
    with open(os.path.join(work_dir, 'test2'), 'w+') as f:
        f.write("This is test2\nfile...")
    with open(os.path.join(work_dir, 'test3'), 'w+') as f:
        f.write("This is test3\nfile...")
    with open(TYPICAL_NOTES_FILE, 'w+'): pass

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['DOWN'] # select file test2
        data += kth['TAB'] # open file for edit
        data += kth['ESC'] # set file management mode
        data += kth['0'] # add custom note
        data += kth['n']+kth['o']+kth['t']+kth['e']
        data += kth['ENTER']
        data += kth['F7'] # open note management
        data += kth['F6'] # save note "note" as typical
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        notes_file = os.path.join(work_dir, 'test2_report.yaml')
        if os.path.exists(notes_file):
            with open(notes_file, 'r') as f:
                data = yaml.safe_load(f)
                if data == {1: {0: ['note']}}:
                    test_pass = True
        with open(TYPICAL_NOTES_FILE, 'r') as f:
            new_typical_notes = f.read()
            if new_typical_notes != 'note':
                test_pass = False


        time_passed = str(round(end-start,2))
        print("Test2........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test2 | {err} | "+str(traceback.format_exc()))


"""
Zalozenie projektu a tvorba testov
* som v prazdnom adresari
1. vytvor novy adresar "proj"
2. vojdi do noveho adresara
3. zaloz novy projekt
4. vytvor novy test "testA"
5. skontroluj existenciu suboru "proj/tests/testA/dotest.sh"
6. skontroluj verziu testu
7. skontroluj existenciu adresarov "tests", "history" a "reports" v "proj"
"""
def test3():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test3')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['2'] # select option for create new dir
        data += kth['p']+kth['r']+kth['o']+kth['j']
        data += kth['ENTER']
        data += kth['RIGHT'] # go to new directory
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['F2'] # open menu
        data += kth['E'] # select option for create new test
        data += kth['t']+kth['e']+kth['s']+kth['t']+kth['A']
        data += kth['ENTER']
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        tests_dir = os.path.join(work_dir, 'proj', 'tests')
        history_dir = os.path.join(work_dir, 'proj', 'history')
        history_file = os.path.join(history_dir, 'testsuite_history.txt')
        reports_dir = os.path.join(work_dir, 'proj', 'reports')
        template_file = os.path.join(reports_dir, 'report_template.j2')
        tst_file = os.path.join(tests_dir, 'src', 'tst')
        testsuite_file = os.path.join(tests_dir, 'testsuite.sh')
        ts_file_tags = os.path.join(tests_dir, 'testsuite_tags.yaml')
        scoring_file = os.path.join(tests_dir, 'scoring')
        sum_file = os.path.join(tests_dir, 'sum')
        proj_conf = os.path.join(work_dir, 'proj', 'proj_conf.yaml')

        proj_dirs = [tests_dir, history_dir, reports_dir]
        proj_files = [history_file, template_file, tst_file, testsuite_file, scoring_file, sum_file, proj_conf, ts_file_tags]
        test_file = os.path.join(tests_dir, 'testA', 'dotest.sh')
        test_file_tags = os.path.join(tests_dir, 'testA', 'test_tags.yaml')
        if os.path.exists(test_file) and os.path.exists(test_file_tags):
            with open(test_file_tags, 'r') as f:
                data = yaml.safe_load(f)
                if data in [{'version': [1]}, {'version': ['1']}]:
                    test_pass = True

        for pdir in proj_dirs:
            if not (os.path.exists(pdir) and os.path.isdir(pdir)):
                test_pass = False
                break
        for pfile in proj_files:
            if not (os.path.exists(pfile) and os.path.isfile(pfile)):
                test_pass = False
                break
        if not os.access(testsuite_file, os.X_OK):
            test_pass = False


        time_passed = str(round(end-start,2))
        print("Test3........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test3 | {err} | "+str(traceback.format_exc()))


"""
Modifikacia testu (verzovanie a historia)
* som v prazdnom adresari
1. zaloz novy projekt
2. vytvor novy test test_1 a test_2
3. otvor menu a vyber moznost editovat test "vyber jediny test_1"
4. zapis do suboru "echo test_1"
5. uloz subor vratane historie
6. skontroluj existenciu adresara "history/testA/version1"
7. skontroluj v tomto adresari existenciu suboru "dotest.sh" a jeho obsah
8. skontroluj inkrementovanu verziu testu a inkrementovanu verziu testsuitu
"""
def test4():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test4')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['F2'] # open menu
        data += kth['E'] # select option for create new test (test_1)
        data += kth['ENTER']
        data += kth['TAB'] # go to browsing
        data += kth['TAB']
        data += kth['TAB']
        data += kth['F2'] # open menu
        data += kth['E'] # select option for create new test (test_2)
        data += kth['ENTER']
        data += kth['TAB'] # go to browsing
        data += kth['TAB']
        data += kth['TAB']
        data += kth['F2'] # open menu
        data += kth['I'] # select option for edit test_1
        data += kth['ENTER']
        data += kth['DOWN'] # go to second line in file dotest.sh
        data += kth['ENTER']
        data += kth['LEFT']
        data += kth['e']+kth['c']+kth['h']+kth['o']
        data += kth['space']
        data += kth['t']+kth['e']+kth['s']+kth['t']
        data += kth['F2'] # save file
        data += kth['F2'] # save test to history
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        content_ok = False
        test1_file = os.path.join(work_dir, 'tests', 'test_1', 'dotest.sh')
        test2_file = os.path.join(work_dir, 'tests', 'test_2', 'dotest.sh')
        if os.path.exists(test1_file) and os.path.exists(test2_file):
            with open(test1_file, 'r') as f:
                file_content = f.readlines()
                if file_content[1] == "echo test\n":
                    content_ok = True

        tags_ok = False
        test1_tag_ok, test2_tag_ok, ts_tag_ok = False, False, False
        test1_file_tags = os.path.join(work_dir, 'tests', 'test_1', 'test_tags.yaml')
        test2_file_tags = os.path.join(work_dir, 'tests', 'test_2', 'test_tags.yaml')
        ts_file_Tags = os.path.join(work_dir, 'tests', 'testsuite_tags.yaml')
        if os.path.exists(test1_file_tags):
            with open(test1_file_tags, 'r') as f:
                data = yaml.safe_load(f)
                if data in [{'version': [2]}, {'version': ['2']}]:
                    test1_tag_ok = True
        if os.path.exists(test2_file_tags):
            with open(test2_file_tags, 'r') as f:
                data = yaml.safe_load(f)
                if data in [{'version': [1]}, {'version': ['1']}]:
                    test2_tag_ok = True
        if os.path.exists(ts_file_Tags):
             with open(ts_file_Tags, 'r') as f:
                data = yaml.safe_load(f)
                if data in [{'version': [4]}, {'version': ['4']}]:
                    ts_tag_ok = True

        history_ok = False
        history_file = os.path.join(work_dir, 'history', 'testsuite_history.txt')
        history_test1_file = os.path.join(work_dir, 'history', 'test_1', 'version_1', 'dotest.sh')
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                history_data = f.read()
                requested_data = """\
2:test_1:create new test
3:test_2:create new test
4:test_1:modify test (test version 1 -> 2)\n"""
                if history_data == requested_data: 
                    history_ok = True

        if not os.path.exists(history_test1_file):
            history_ok = False

        tags_ok = test1_tag_ok and test2_tag_ok and ts_tag_ok
        test_pass = content_ok and tags_ok and history_ok

        time_passed = str(round(end-start,2))
        print("Test4........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test4 | {err} | "+str(traceback.format_exc()))



"""
Vytvorenie Dockerfilu
* som v prazdnom adresari
1. zaloz novy projekt
2. otvor menu a vyber moznost vytvorit Dockerfile
3. zadaj distribuciu "fedora:34"
4. zadaj user id 1000 a group id 1000
5. skontroluj vytvoreny adresar Dockerfile
"""
def test5():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test5')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['F2'] # open menu
        data += kth['3'] # select option for create dockerfile
        data += kth['f']+kth['e']+kth['d']+kth['o']+kth['r']+kth['a']
        data += kth[':']+kth['3']+kth['4']
        data += kth['ENTER']
        data += kth['1']+kth['0']+kth['0']+kth['0'] # set uid
        data += kth['ENTER']
        data += kth['1']+kth['0']+kth['0']+kth['0'] # set gid
        data += kth['ENTER']
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        docker_file = os.path.join(work_dir, 'Dockerfile')
        if os.path.exists(docker_file):
            with open(docker_file, 'r') as f:
                file_content = f.read()
                requested_content = """\
FROM fedora:34
RUN addgroup -g 1000 test 2>/dev/null || groupadd -g 1000 test
RUN adduser -D -u 1000 -G test test 2>/dev/null || useradd -u 1000 -g test test
USER test\n"""
                if file_content == requested_content:
                    test_pass = True

        time_passed = str(round(end-start,2))
        print("Test5........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test5 | {err} | "+str(traceback.format_exc()))


"""
Vytaranie logov
* som v prazdnom adresari
1. premaz logy
2. zaloz novy projekt test6
3. rozbal archivy studentov
4. vytvor novy test
5. edituj a uloz test
6. vytvor adresar xlogin00
7. spusti test nad loginom
8. odstran test
9. skontroluj subor s logmi
"""
def test6():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test6')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['TAB'] # go to logs
        data += kth['F9'] # clear logs
        data += kth['TAB'] # go to brows
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['F2'] # open menu
        data += kth['5'] # select option for extract all solutions
        data += kth['F2'] # open menu
        data += kth['E'] # select option for create new test (test_1)
        data += kth['ENTER']
        data += kth['DOWN']
        data += kth['ENTER']
        data += kth['F2'] # save file
        data += kth['F2'] # save test history
        data += kth['TAB'] # go to brows
        data += kth['TAB']
        data += kth['TAB']
        data += kth['LEFT'] # go to tests
        data += kth['LEFT'] # go to proj
        data += kth['F2'] # open menu
        data += kth['M'] # select option for create new directory
        data += kth['x']+kth['l']+kth['o']+kth['g']+kth['i']+kth['n']+kth['0']+kth['0']
        data += kth['ENTER']
        data += kth['F2'] # open menu
        data += kth['7'] # run tests
        data += kth['F2'] # open menu
        data += kth['I'] # edit test
        data += kth['ENTER'] # first one
        data += kth['F3'] # hide tags
        data += kth['TAB'] # go to brows
        data += kth['TAB']
        data += kth['F2'] # open menu
        data += kth['J'] # remove test
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        if os.path.exists(USER_LOGS_FILE):
            with open(USER_LOGS_FILE, 'r') as f:
                file_content = f.readlines()
                req = [
"|INFO   |new project created (test6)\n",
"|INFO   |extracting all solution archives...\n",
"|WARNING|no solution archives found in project directory\n",
"|INFO   |creating new test...\n",
"|INFO   |test 'test_1' created (scoring ok=1,fail=0)\n",
"|INFO   |file 'dotest.sh' saved\n",
"|INFO   |old version (1) of test 'test_1' is saved in history\n",
"|INFO   |*** testing student 'xlogin00' ***\n",
"|ERROR  |FUT 'sut' doesnt exists in solution directory\n",
"|INFO   |testing done\n",
"|INFO   |testing all students done !!\n",
"|INFO   |removing test 'test_1'...\n",
"|INFO   |test 'test_1' (version: 2) is archived in history\n"]
                test_pass = True
                for idx, line in enumerate(file_content):
                    if not line.endswith(req[idx]):
                        test_pass = False

        time_passed = str(round(end-start,2))
        print("Test6........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test6 | {err} | "+str(traceback.format_exc()))


"""
Filtrovanie suborov a hromadne pridanie poznamky
* som adresari so subormi:
xlogin00/file1, 
xlogin01/file2, 
xlogin02/file3, 
xlogin03/test1, 
xlogin04/test2, 
xlogin05/tmp1, 
xlogin06/tmp2
* subory xlogin01/file2, xlogin05/test2 a xlogin07/tmp2 obsahuju retazec "test"
1. zaloz projekt
2. zadaj filter podla cesty "*e"
3. zadaj filter podla obsahu "test"
4. pridaj filtrovanym suborom poznamku "ok"
5. skontroluj pridanie poznamky suborom file2 a test2
"""
def test7():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test7')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)
    os.mkdir(os.path.join(work_dir, 'xlogin00'))
    os.mkdir(os.path.join(work_dir, 'xlogin01'))
    os.mkdir(os.path.join(work_dir, 'xlogin02'))
    os.mkdir(os.path.join(work_dir, 'xlogin03'))
    os.mkdir(os.path.join(work_dir, 'xlogin04'))
    os.mkdir(os.path.join(work_dir, 'xlogin05'))
    os.mkdir(os.path.join(work_dir, 'xlogin06'))
    with open(os.path.join(work_dir, 'xlogin00', 'file1'), 'w+'): pass
    with open(os.path.join(work_dir, 'xlogin01', 'file2'), 'w+') as f:
        f.write("This is test\n...")
    with open(os.path.join(work_dir, 'xlogin02', 'file3'), 'w+'): pass
    with open(os.path.join(work_dir, 'xlogin03', 'test1'), 'w+'): pass
    with open(os.path.join(work_dir, 'xlogin04', 'test2'), 'w+') as f:
        f.write("This is test\n...")
    with open(os.path.join(work_dir, 'xlogin05', 'tmp1'), 'w+'): pass
    with open(os.path.join(work_dir, 'xlogin06', 'tmp2'), 'w+') as f:
        f.write("This is test\n...")

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['/'] # set filter by path
        data += kth['*']+kth['e']
        data += kth['ENTER']
        data += kth['TAB']
        data += kth['ESC']
        data += kth['/'] # set filter by content
        data += kth['t']+kth['e']+kth['s']+kth['t']
        data += kth['ENTER']
        data += kth['/']
        data += kth['F4'] # aggregate filter
        data += kth['F2'] # open menu
        data += kth['C'] # add custom user note
        data += kth['o']+kth['k']
        data += kth['ENTER']
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        note1_ok, note4_ok = False, False
        notes_file = os.path.join(work_dir, 'xlogin01', 'reports', 'user_notes')
        if os.path.exists(notes_file):
            with open(notes_file, 'r') as f:
                data = f.read()
                if data == "ok":
                    note1_ok = True
        notes_file = os.path.join(work_dir, 'xlogin04', 'reports', 'user_notes')
        if os.path.exists(notes_file):
            with open(notes_file, 'r') as f:
                data = f.read()
                if data == "ok":
                    note4_ok = True
        test_pass = note1_ok and note4_ok
        notes00_file = os.path.join(work_dir, 'xlogin00', 'reports', 'user_notes')
        notes02_file = os.path.join(work_dir, 'xlogin02', 'reports', 'user_notes')
        notes03_file = os.path.join(work_dir, 'xlogin03', 'reports', 'user_notes')
        if os.path.exists(notes00_file) or os.path.exists(notes02_file) or os.path.exists(notes03_file):
            test_pass = False

        time_passed = str(round(end-start,2))
        print("Test7........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test7 | {err} | "+str(traceback.format_exc()))


"""
Vytvaranie a mazanie tagov
* som v adresari s podadresarmi xlogin00 a xlogin01
1. vytvor novy projekt
2. pridaj tag rieseniu xlogin00 "test"
3. pridaj tagy rieseniu xlogin01 "test1" a "test2"
4. pre xlogin00 zmen parameter tagu "test" na hodnotu 2
5. pre xlogin01 zmaz tag test2
6. skontroluj tagy oboch rieseni
"""
def test8():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test8')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)
    os.mkdir(os.path.join(work_dir, 'xlogin00'))
    os.mkdir(os.path.join(work_dir, 'xlogin01'))

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['DOWN'] # skip "history"
        data += kth['DOWN'] # skip "reports"
        data += kth['DOWN'] # skip "test"
        data += kth['F5'] # go to xlogin00 tags
        data += kth['F3'] # add new tag
        data += kth['t']+kth['e']+kth['s']+kth['t']
        data += kth['ENTER']
        data += kth['TAB'] # to go brows
        data += kth['TAB']
        data += kth['DOWN'] # go to xlogin01
        data += kth['F5'] # go to tags
        data += kth['F3'] # add new tag
        data += kth['t']+kth['e']+kth['s']+kth['t']+kth['1']
        data += kth['ENTER']
        data += kth['F3'] # add new tag
        data += kth['t']+kth['e']+kth['s']+kth['t']+kth['2']
        data += kth['ENTER']
        data += kth['TAB'] # to go brows
        data += kth['TAB']
        data += kth['UP'] # go to xlogin00
        data += kth['F5'] # edit tag
        data += kth['F2']
        data += kth['RIGHT']
        data += kth['RIGHT']
        data += kth['RIGHT']
        data += kth['RIGHT']
        data += kth['space']
        data += kth['2']
        data += kth['ENTER']
        data += kth['TAB'] # to go brows
        data += kth['TAB']
        data += kth['DOWN'] # go to xlogin01
        data += kth['F5']
        data += kth['DOWN']
        data += kth['F8'] # remove tag test2
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        log00_ok, log01_ok = False, False
        login00_tags = os.path.join(work_dir, 'xlogin00', 'solution_tags.yaml')
        login01_tags = os.path.join(work_dir, 'xlogin01', 'solution_tags.yaml')
        if os.path.exists(login00_tags):
            with open(login00_tags, 'r') as f:
                data = yaml.safe_load(f)
                if data == {'test': ['2']}:
                    log00_ok = True
        if os.path.exists(login01_tags):
            with open(login01_tags, 'r') as f:
                data = yaml.safe_load(f)
                if data == {'test1': []}:
                    log01_ok = True
        test_pass = log00_ok and log01_ok

        time_passed = str(round(end-start,2))
        print("Test8........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test8 | {err} | "+str(traceback.format_exc()))



"""
Spustenie testu a vytvorenie reportu
* som v adresari so suborom xlogin00/sut
1. vytvor novy projekt
2. vytvor test test_1, ktory prida tag scoring_test_1(2) a test_1_ok()
3. vytvor testovaciu strategiu, ktora spusti test_1
4. pridaj poznamku "ok" k rieseniu xlogin00
5. vytvor poznamku "note" vramci code review na riadku 1
6. spusti testovaciu strategiu nad xlogin00
7. vygeneruj report pre riezenie xlogin00
8. skontroluj vygenerovany report
"""
def test9():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test9')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)
    os.mkdir(os.path.join(work_dir, 'xlogin00'))
    with open(os.path.join(work_dir, 'xlogin00', 'sut'), 'w+'): pass

    try:
        start = time.time()
        ######## E X E R C I S E ######## 
        data = ""
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['F2'] # open menu
        data += kth['E'] # select option for create new test
        data += kth['ENTER']
        data += kth['DOWN']
        data += kth['c']+kth['d']+kth['space']+kth['$']+kth['T']
        data += kth['ENTER']
        for i in "add_test_tag":
            data += kth[i]
        data += kth['space']
        for i in "scoring_test_1":
            data += kth[i]
        data += kth['space']
        data += kth['2']
        data += kth['ENTER']
        for i in "add_test_tag":
            data += kth[i]
        data += kth['space']
        for i in "test_1_ok":
            data += kth[i]
        data += kth['ENTER']
        data += kth['F2'] # save test_1
        data += kth['F2']
        data += kth['TAB'] # go to brows
        data += kth['TAB']
        data += kth['TAB']
        data += kth['F2'] # open menu
        data += kth['F'] # select option for edit testsuite
        data += kth['DOWN']
        data += kth['t']+kth['s']+kth['t']+kth['space']
        data += kth['r']+kth['u']+kth['n']+kth['space']
        for i in "test_1":
            data += kth[i]
        data += kth['ENTER']
        data += kth['F2'] # save testsuite
        data += kth['TAB'] # go to brows
        data += kth['TAB']
        data += kth['TAB']
        data += kth['LEFT'] # go to tests
        data += kth['LEFT'] # go to proj dir
        data += kth['DOWN'] # go to xlogin00
        data += kth['F2'] # open menu
        data += kth['L'] # add user note
        data += kth['o']+kth['k']
        data += kth['ENTER']
        data += kth['RIGHT'] # go to xlogin00 dir
        data += kth['DOWN'] # select sut
        data += kth['TAB']
        data += kth['ESC']
        data += kth['0']
        data += kth['n']+kth['o']+kth['t']+kth['e']
        data += kth['ENTER']
        data += kth['TAB'] # to go brows
        data += kth['TAB']
        data += kth['TAB']
        data += kth['F2'] # open menu
        data += kth['F'] # run testsuite
        data += kth['F2'] # open menu
        data += kth['J'] # generate report
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        report_file = os.path.join(work_dir, 'xlogin00', 'reports', 'total_report')
        req_report = """\
Scoring for project: project
Total score: 2 / 10
Bonus score: -
==================================
2:ok:test_1:-
==================================


Code review
==================================
xlogin00/sut:1:0:note
==================================


Additional notes
==================================
ok
=================================="""
        if os.path.exists(report_file):
            with open(report_file, 'r') as f:
                data = f.read()
                if data == req_report:
                    test_pass = True

        time_passed = str(round(end-start,2))
        print("Test9........"+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test9 | {err} | "+str(traceback.format_exc()))


"""
Tvorba statistik
* som v adresari so subormi
xlogin00/sut s obsahom "test"
xlogin01/sut s obsahom "txt"
xlogin02/sut s obsahom "abc"
xlogin03/sut s obsahom "def"
xlogin04/sut s obsahom "ahoj"
xlogin05/sut s obsahom "test"
1. vytvor novy projekt
2. vytvor test test_1, ktory prida tag scoring_test_1(0) a test_1_ok()
3. filtruj subory s obsahom "a"
4. pridaj rieseniam tag scoring_bonus(3)
5. filtruj subory s obsahom "e"
6. pridaj rieseniam tag scoring_bonus(9)
7. uprav subor sum aby pocital aj + bonus
8. spusti test_1 nad vsetkymi rieseniami
9. prepocitaj skore
10. generuj statistiky
11. skontroluj vytvorene statistiky (1x 1b, 2x 4b, 3x 10b)
"""
def test10():
    ########## S E T U P ########## 
    work_dir = os.path.join(HOME, 'test10')
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.mkdir(work_dir)
    os.chdir(work_dir)
    os.mkdir(os.path.join(work_dir, 'xlogin00'))
    os.mkdir(os.path.join(work_dir, 'xlogin01'))
    os.mkdir(os.path.join(work_dir, 'xlogin02'))
    os.mkdir(os.path.join(work_dir, 'xlogin03'))
    os.mkdir(os.path.join(work_dir, 'xlogin04'))
    os.mkdir(os.path.join(work_dir, 'xlogin05'))
    with open(os.path.join(work_dir, 'xlogin00', 'sut'), 'w+') as f: f.write("test")
    with open(os.path.join(work_dir, 'xlogin01', 'sut'), 'w+') as f: f.write("txt")
    with open(os.path.join(work_dir, 'xlogin02', 'sut'), 'w+') as f: f.write("abc")
    with open(os.path.join(work_dir, 'xlogin03', 'sut'), 'w+') as f: f.write("def")
    with open(os.path.join(work_dir, 'xlogin04', 'sut'), 'w+') as f: f.write("ahoj")
    with open(os.path.join(work_dir, 'xlogin05', 'sut'), 'w+') as f: f.write("test")

    try:
        start = time.time()
        ######## E X E R C I S E ########
        data = ""
        data += kth['F2'] # open menu
        data += kth['ENTER'] # select first option (create proj)
        data += kth['F2'] # open menu
        data += kth['E'] # select option for create new test
        data += kth['ENTER']
        data += kth['DOWN']
        data += kth['c']+kth['d']+kth['space']+kth['$']+kth['T']
        data += kth['ENTER']
        for i in "add_test_tag":
            data += kth[i]
        data += kth['space']
        for i in "scoring_test_1":
            data += kth[i]
        data += kth['space']
        data += kth['0']
        data += kth['ENTER']
        for i in "add_test_tag":
            data += kth[i]
        data += kth['space']
        for i in "test_1_ok":
            data += kth[i]
        data += kth['ENTER']
        data += kth['F2'] # save test_1
        data += kth['F2']
        data += kth['TAB'] # go to brows
        data += kth['TAB']
        data += kth['TAB']
        data += kth['F2'] # open menu
        data += kth['F'] # select option for edit testsuite
        data += kth['DOWN']
        data += kth['t']+kth['s']+kth['t']+kth['space']
        data += kth['r']+kth['u']+kth['n']+kth['space']
        for i in "test_1":
            data += kth[i]
        data += kth['ENTER']
        data += kth['F2'] # save testsuite
        data += kth['ESC'] # set filter by content "a"
        data += kth['/']
        data += kth['a']
        data += kth['ENTER']
        data += kth['/']
        data += kth['F4'] # aggregate filter
        data += kth['F2'] # add tag to filtered solutions
        data += kth['D']
        for i in "scoring_bonus":
            data += kth[i]
        data += kth['space']
        data += kth['3']
        data += kth['ENTER']
        data += kth['TAB']
        data += kth['ESC'] # set filter by content "e"
        data += kth['/']
        data += kth['DEL']
        data += kth['e']
        data += kth['ENTER']
        data += kth['F2'] # add tag to filtered solutions
        data += kth['D']
        for i in "scoring_bonus":
            data += kth[i]
        data += kth['space']
        data += kth['9']
        data += kth['ENTER']
        data += kth['/'] # remove filter
        data += kth['F8']
        data += kth['F2'] # change sum file
        data += kth['H']
        data += kth['ESC']
        data += kth['a']
        data += kth['DOWN']
        data += kth['DOWN']
        data += kth['DOWN']
        data += kth['RIGHT']*17
        for i in "+bonus":
            data += kth[i]
        data += kth['F2']
        data += kth['TAB'] # go to brows
        data += kth['TAB']
        data += kth['TAB']
        data += kth['F2'] # test all solutions
        data += kth['7']
        data += kth['F2'] # generate stats
        data += kth['K']
        data += kth['F10']
        command = Command(f"{MAIN}")
        command.run(timeout=200, data=data)
        end = time.time()

        ########## V E R I F Y ########## 
        test_pass = False
        stats_file = os.path.join(work_dir, 'reports', 'scoring_stats')
        req_content = """\
Maximum score: 10
------------------------------------
Average: 5.5
Average (without zero): 6.6
Modus: 9
------------------------------------
Scoring severity:
0:  * 1
1:   0
2:   0
3:  ** 2
4:   0
5:   0
6:   0
7:   0
8:   0
9:  *** 3
10:  0
\n"""
        if os.path.exists(stats_file):
            with open(stats_file, 'r') as f:
                data = f.read()
                if data == req_content:
                    test_pass = True

        time_passed = str(round(end-start,2))
        print("Test10......."+("ok  " if test_pass else "fail")+" ("+time_passed+"s)")

        ######### T E A R D O W N ######### 
        shutil.rmtree(work_dir)
    except Exception as err:
        print(f"test10 | {err} | "+str(traceback.format_exc()))




if __name__ == "__main__":

    old_user_logs =""
    with open(USER_LOGS_FILE, 'r+') as f:
        old_user_logs = f.read()

    start = time.time()
    test1() # vytvorenie a uprava suboru
    test2() # pridavanie poznamok
    test3() # zalozenie projektu a tvorba testov
    with open(USER_LOGS_FILE, 'w+'): pass
    test4() # verzovanie a historia testov
    test5() # vytvorenie dockerfilu
    test6() # vytvaranie logov
    test7() # filtrovanie a hromadne pridanie poznamky
    with open(USER_LOGS_FILE, 'w+'): pass
    test8() # vtrvaranie a mazanie tagov
    test9() # spustenie testu a vytvorenie reportu
    test10() # bash a mazanie suboru
    end = time.time()

    process_time = str(round(end-start,2))
    print("*** total: "+process_time+"s ***")

    with open(USER_LOGS_FILE, 'w+') as f:
        f.write(old_user_logs)
