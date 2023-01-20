"""End-to-end tests running various scenarios with SPEF.

Contains high-level integration tests which execute a series of commands
(keystrokes) in SPEF and then check that the result (typically the created
files) are as expected.
"""

import os
import pathlib
import subprocess
import yaml

from spef.utils.logger import DATA_DIR, TYPICAL_NOTES_FILE, USER_LOGS_FILE
from key_values import kth

TYPICAL_NOTES = pathlib.Path(os.path.join(DATA_DIR, TYPICAL_NOTES_FILE))
USER_LOGS = pathlib.Path(os.path.join(DATA_DIR, USER_LOGS_FILE))


def run_scenario(path, keys):
    os.chdir(path)
    stdin = "".join([kth[k] for k in keys]).encode("utf-8")
    subprocess.run(["spef"], input=stdin, stdout=subprocess.PIPE)


def assert_version(tags_file, version):
    tags = yaml.safe_load(tags_file.read_text())
    assert tags["version"] == [version] or tags["version"] == [str(version)]


def test_create_file(tmp_path):
    """Test creation of a text file

    Scenario:
    1. Create a new file "test"
    2. Open the file for writing
    3. Insert the text "This is \n...test"
    4. Save the file

    Checks that the file has the expected content.
    """
    # fmt: off
    keys = [
        "F2",  # open menu
        "3",   # select option "create new file"
        "t", "e", "s", "t",
        "ENTER",
        "TAB",  # open file for edit
        "T", "h", "i", "e", "BACKSPACE",
        "s", "space", "i", "s", "ENTER", ".", ".", ".", "t", "e", "s", "t",
        "F2",  # save file
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    test = tmp_path / "test"
    assert test.read_text() == "This is\n...test"
    assert len(list(tmp_path.iterdir())) == 1


def test_add_notes(tmp_path):
    """Test adding notes

    Scenario:
    0. Starting in a folder with 3 files: test1, test2, test3
    1. Open test2 for writing
    2. Insert a new note to the first line with text "note"
    3. Open note management
    4. Save the note as typical

    Checks:
    - note file for test2 has the expected content
    - typical notes file has the expected content
    """
    test1 = tmp_path / "test1"
    test1.write_text("This is test1\nfile")
    test2 = tmp_path / "test2"
    test2.write_text("This is test2\nfile")
    TYPICAL_NOTES.touch()

    # fmt: off
    keys = [
        "DOWN",  # select file test2
        "TAB",  # open file for edit
        "ESC",  # set file management mode
        "0",    # add custom note
        "n", "o", "t", "e",
        "ENTER",
        "F7",  # open note management
        "F6",  # save note "note" as typical
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    notes = tmp_path / "test2_report.yaml"
    assert yaml.safe_load(notes.read_text()) == {1: {0: ["note"]}}
    assert TYPICAL_NOTES.read_text() == "note"


def test_create_project(tmp_path):
    """Test creating a project and tests inside it

    Scenario:
    1. Create a new directory "proj"
    2. Enter the directory
    3. Create a new project
    4. Create a new test "testA"

    Checks:
    - test has correct version (1)
    - project contains expected files and directories
    """
    # fmt: off
    keys = [
        "F2",  # open menu
        "2",   # select option for create new dir
        "p", "r", "o", "j",
        "ENTER",
        "RIGHT",  # go to new directory
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "F2",     # open menu
        "E",      # select option for create new test
        "t", "e", "s", "t", "A",
        "ENTER",
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    tests_dir = tmp_path / "proj" / "tests"

    test_file_tags = tests_dir / "testA" / "test_tags.yaml"
    assert_version(test_file_tags, 1)

    for d in ["proj/tests", "proj/history", "proj/reports"]:
        assert (tmp_path / d).is_dir()
    for f in [
        "proj/history/testsuite_history.txt",
        "proj/reports/report_template.j2",
        "proj/tests/src/tst",
        "proj/tests/testsuite.sh",
        "proj/tests/scoring",
        "proj/tests/sum",
        "proj/proj_conf.yaml",
        "proj/tests/testsuite_tags.yaml",
    ]:
        assert (tmp_path / f).is_file()
    assert os.access(tests_dir / "testsuite.sh", os.X_OK)


def test_modify_tests(tmp_path):
    """Test modification of tests (versioning and history)

    Scenario:
    1. Create a new project
    2. Create new tests test_1 and test_2
    3. Open menu and choose to edit test_1
    4. Write "echo test_1" to the test file
    5. Save the test including its history

    Checks:
    - version 1 is preserved in "history/testA/version1"
    - tests and testsuite have expected versions
    """
    # fmt: off
    keys = [
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "F2",     # open menu
        "E",      # select option for create new test (test_1)
        "ENTER",
        "TAB",    # go to browsing
        "TAB",
        "TAB",
        "F2",     # open menu
        "E",      # select option for create new test (test_2)
        "ENTER",
        "TAB",    # go to browsing
        "TAB",
        "TAB",
        "F2",     # open menu
        "I",      # select option for edit test_1
        "ENTER",
        "DOWN",   # go to second line in file dotest.sh
        "ENTER",
        "LEFT",
        "e", "c", "h", "o",
        "space",
        "t", "e", "s", "t",
        "F2",  # save file
        "F2",  # save test to history
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    test_1 = tmp_path / "tests" / "test_1" / "dotest.sh"
    test_2 = tmp_path / "tests" / "test_2" / "dotest.sh"
    assert test_1.read_text().splitlines()[1] == "echo test"
    assert test_2.is_file()

    test_1_tags = tmp_path / "tests" / "test_1" / "test_tags.yaml"
    test_2_tags = tmp_path / "tests" / "test_2" / "test_tags.yaml"
    testsuite_tags = tmp_path / "tests" / "testsuite_tags.yaml"
    assert_version(test_1_tags, 2)
    assert_version(test_2_tags, 1)
    assert_version(testsuite_tags, 4)

    test_1_hist = tmp_path / "history" / "test_1" / "version_1" / "dotest.sh"
    testsuite_hist = tmp_path / "history" / "testsuite_history.txt"
    assert (
        testsuite_hist.read_text()
        == """\
2:test_1:create new test
3:test_2:create new test
4:test_1:modify test (test version 1 -> 2)
"""
    )
    assert test_1_hist.is_file()


def test_create_dockerfile(tmp_path):
    """Test creating Dockerfile for testing environment

    Scenario:
    1. Create a new project
    2. Open menu and choose to create a Dockerfile
    3. Enter the "fedora:34" distribution
    4. Enter the user id 1000 and the group id 1000

    Check that the Dockerfile is correctly created.
    """
    # fmt: off
    keys = [
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "F2",     # open menu
        "3",      # select option for create Dockerfile
        "f", "e", "d", "o", "r", "a", ":", "3", "4",
        "ENTER",
        "1", "0", "0", "0",  # set uid
        "ENTER",
        "1", "0", "0", "0",  # set gid
        "ENTER",
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    dockerfile = tmp_path / "Dockerfile"
    assert (
        dockerfile.read_text()
        == """\
FROM fedora:34
RUN addgroup -g 1000 test 2>/dev/null || groupadd -g 1000 test
RUN adduser -D -u 1000 -G test test 2>/dev/null || useradd -u 1000 -g test test
USER test
"""
    )


def test_logging(tmp_path):
    """Test creating logs

    Scenario:
    1. Create a new project "test_logging0"
    2. Extract solution archives
    3. Create a new test
    4. Edit and save the test
    5. Create a new solution directory "xlogin00"
    6. Run the test on the solution
    7. Clear the test

    Check that the logs have expected content.
    """
    # fmt: off
    keys = [
        "TAB",    # go to logs
        "F9",     # clear logs
        "TAB",    # go to brows
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "F2",     # open menu
        "5",      # select option for extract all solutions
        "F2",     # open menu
        "E",      # select option for create new test (test_1)
        "ENTER",
        "DOWN",
        "ENTER",
        "F2",     # save file
        "F2",     # save test history
        "TAB",    # go to brows
        "TAB",
        "TAB",
        "LEFT",   # go to tests
        "LEFT",   # go to proj
        "F2",     # open menu
        "M",      # select option for create new directory
        "x", "l", "o", "g", "i", "n", "0", "0",
        "ENTER",
        "F2",     # open menu
        "7",      # run tests
        "F2",     # open menu
        "I",      # edit test
        "ENTER",  # first one
        "F3",     # hide tags
        "TAB",    # go to brows
        "TAB",
        "F2",     # open menu
        "J",      # remove test
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    logs = [
        "|INFO   |new project created (test_logging0)",
        "|INFO   |extracting all solution archives...",
        "|WARNING|no solution archives found in project directory",
        "|INFO   |creating new test...",
        "|INFO   |test 'test_1' created (scoring ok=1,fail=0)",
        "|INFO   |file 'dotest.sh' saved",
        "|INFO   |old version (1) of test 'test_1' is saved in history",
        "|INFO   |*** testing student 'xlogin00' ***",
        "|ERROR  |FUT 'sut' doesnt exists in solution directory",
        "|INFO   |testing done",
        "|INFO   |testing all students done !!",
        "|INFO   |removing test 'test_1'...",
        "|INFO   |test 'test_1' (version: 2) is archived in history",
    ]
    for i, line in enumerate(USER_LOGS.read_text().splitlines()):
        assert line.endswith(logs[i])


def test_batch_notes(tmp_path):
    """Test file filtering and adding notes in batch

    Scenario:
    0. Starting in a folder with 6 solutions, each having one file.
    1. Create a new project
    2. Filter by path "*e" (should not match tmp1 and tmp2)
    3. Filter by file content "test"
    4. Add batch note "ok" to all the filtered files

    Check (non)existence of notes for individual files.
    """
    solutions = [tmp_path / ("xlogin0" + str(i)) for i in range(7)]
    for s in solutions:
        s.mkdir()

    (solutions[0] / "file1").touch()
    (solutions[1] / "file2").write_text("This is test\n...")
    (solutions[2] / "file3").touch()
    (solutions[3] / "test1").touch()
    (solutions[4] / "test2").write_text("This is test\n...")
    (solutions[5] / "tmp1").touch()
    (solutions[6] / "tmp2").write_text("This is test\n...")

    # fmt: off
    keys = [
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "/",      # set filter by path
        "*", "e",
        "ENTER",
        "TAB",
        "ESC",
        "/",      # set filter by content
        "t", "e", "s", "t",
        "ENTER",
        "/",
        "F4",     # aggregate filter
        "F2",     # open menu
        "C",      # add custom user note
        "o", "k",
        "ENTER",
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    notes = [sol / "reports" / "user_notes" for sol in solutions]
    assert not notes[0].is_file()
    assert notes[1].read_text() == "ok"
    assert not notes[2].is_file()
    assert not notes[3].is_file()
    assert notes[4].read_text() == "ok"
    assert not notes[5].is_file()
    assert not notes[6].is_file()


def test_tags(tmp_path):
    """Test creating and deleting tags

    Scenario:
    0. Starting in a folder with two solutions xlogin00 and xlogin01
    1. Create a new project
    2. Add the tag "test" to the xlogin00 solution
    3. Add the tags "test1" and "test2" to the xlogin01 solution
    4. Set parameter the tag "test" for xlogin00 to the value 2
    5. Delete the "test2" tag from xlogin01

    Check that the final logins are correct.
    """
    solution0 = tmp_path / "xlogin00"
    solution1 = tmp_path / "xlogin01"
    solution0.mkdir()
    solution1.mkdir()

    # fmt: off
    keys = [
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "DOWN",   # skip "history"
        "DOWN",   # skip "reports"
        "DOWN",   # skip "test"
        "F5",     # go to xlogin00 tags
        "F3",     # add new tag
        "t", "e", "s", "t",
        "ENTER",
        "TAB",    # to go brows
        "TAB",
        "DOWN",   # go to xlogin01
        "F5",     # go to tags
        "F3",     # add new tag
        "t", "e", "s", "t", "1",
        "ENTER",
        "F3",     # add new tag
        "t", "e", "s", "t", "2",
        "ENTER",
        "TAB",    # to go brows
        "TAB",
        "UP",     # go to xlogin00
        "F5",     # edit tag
        "F2",
        "RIGHT",
        "RIGHT",
        "RIGHT",
        "RIGHT",
        "space",
        "2",
        "ENTER",
        "TAB",    # to go brows
        "TAB",
        "DOWN",   # go to xlogin01
        "F5",
        "DOWN",
        "F8",     # remove tag test2
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    tags0 = solution0 / "solution_tags.yaml"
    tags1 = solution1 / "solution_tags.yaml"
    assert yaml.safe_load(tags0.read_text()) == {"test": ["2"]}
    assert yaml.safe_load(tags1.read_text()) == {"test1": []}


def test_run_test(tmp_path):
    """Test running tests and creating a report

    Scenario:
    0. Starting in a directory with one solution "xlogin00" and file "sut"
    1. Create a new project
    2. Create a new test "test_1" (adds tags scoring_test_1(2) and test_1_ok())
    3. Create a test strategy that runs test_1
    4. Add a new note "ok" to the xlogin00 solution
    5. Create a new code review note "note" to the first line of sut
    6. Execute the testing strategy
    7. Generate a report for xlogin00

    Check that the report has expected content.
    """
    solution = tmp_path / "xlogin00"
    solution.mkdir()
    (solution / "sut").touch()

    # fmt: off
    keys = [
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "F2",     # open menu
        "E",      # select option for create new test
        "ENTER",
        "DOWN",
        "c", "d", "space", "$", "T",
        "ENTER",
        "a", "d", "d", "_", "t", "e", "s", "t", "_", "t", "a", "g",
        "space",
        "s", "c", "o", "r", "i", "n", "g", "_", "t", "e", "s", "t", "_", "1",
        "space",
        "2",
        "ENTER",
        "a", "d", "d", "_", "t", "e", "s", "t", "_", "t", "a", "g",
        "space",
        "t", "e", "s", "t", "_", "1", "_", "o", "k",
        "ENTER",
        "F2",   # save test_1
        "F2",
        "TAB",  # go to brows
        "TAB",
        "TAB",
        "F2",   # open menu
        "F",    # select option for edit testsuite
        "DOWN",
        "t", "s", "t", "space",
        "r", "u", "n", "space",
        "t", "e", "s", "t", "_", "1",
        "ENTER",
        "F2",     # save testsuite
        "TAB",    # go to brows
        "TAB",
        "TAB",
        "LEFT",   # go to tests
        "LEFT",   # go to proj dir
        "DOWN",   # go to xlogin00
        "F2",     # open menu
        "L",      # add user note
        "o", "k",
        "ENTER",
        "RIGHT",  # go to xlogin00 dir
        "DOWN",   # select sut
        "TAB",
        "ESC",
        "0",
        "n", "o", "t", "e",
        "ENTER",
        "TAB",    # to go brows
        "TAB",
        "TAB",
        "F2",     # open menu
        "F",      # run testsuite
        "F2",     # open menu
        "J",      # generate report
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    report = solution / "reports" / "total_report"
    assert (
        report.read_text()
        == """\
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
    )


def test_statictics(tmp_path):
    """Test running test on multiple solutions and creating statistics

    Scenario:
    0. Starting in a folder with six solutions, each with one file
    1. Create a new project
    2. Create a new test test_1 (adds tags scoring_test_1(0) and test_1_ok())
    3. Filter files by the content "a"
    4. Add tag scoring_bonus(3) to the solutions
    5. Filter files by the content "e"
    6. Add tag scoring_bonus(9) to the solutions
    7. Update the file "sum" to count with the bonus
    8. Execute test_1 on all solutions
    9. Recalculate score
    10. Generate statistics

    Check that the created statistics are correct.
    """
    solutions = [
        (0, "test"),
        (1, "txt"),
        (2, "abc"),
        (3, "def"),
        (4, "ahoj"),
        (5, "test"),
    ]
    for i, content in solutions:
        s = tmp_path / ("xlogin0" + str(i))
        s.mkdir()
        (s / "sut").write_text(content)

    # fmt: off
    keys = [
        "F2",     # open menu
        "ENTER",  # select first option (create proj)
        "F2",     # open menu
        "E",      # select option for create new test
        "ENTER",
        "DOWN",
        "c", "d", "space", "$", "T",
        "ENTER",
        "a", "d", "d", "_", "t", "e", "s", "t", "_", "t", "a", "g",
        "space",
        "s", "c", "o", "r", "i", "n", "g", "_", "t", "e", "s", "t", "_", "1",
        "space",
        "0",
        "ENTER",
        "a", "d", "d", "_", "t", "e", "s", "t", "_", "t", "a", "g",
        "space",
        "t", "e", "s", "t", "_", "1", "_", "o", "k",
        "ENTER",
        "F2",   # save test_1
        "F2",
        "TAB",  # go to brows
        "TAB",
        "TAB",
        "F2",   # open menu
        "F",    # select option for edit testsuite
        "DOWN",
        "t", "s", "t", "space",
        "r", "u", "n", "space",
        "t", "e", "s", "t", "_", "1",
        "ENTER",
        "F2",   # save testsuite
        "ESC",  # set filter by content "a"
        "/",
        "a",
        "ENTER",
        "/",
        "F4",   # aggregate filter
        "F2",   # add tag to filtered solutions
        "D",
        "s", "c", "o", "r", "i", "n", "g", "_", "b", "o", "n", "u", "s",
        "space",
        "3",
        "ENTER",
        "TAB",
        "ESC",  # set filter by content "e"
        "/",
        "DEL",
        "e",
        "ENTER",
        "F2",   # add tag to filtered solutions
        "D",
        "s", "c", "o", "r", "i", "n", "g", "_", "b", "o", "n", "u", "s",
        "space",
        "9",
        "ENTER",
        "/",    # remove filter
        "F8",
        "F2",   # change sum file
        "H",
        "ESC",
        "a",
        "DOWN",
        "DOWN",
        "DOWN",
        "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",
        "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",
        "RIGHT",
        "+", "b", "o", "n", "u", "s",
        "F2",
        "TAB",  # go to brows
        "TAB",
        "TAB",
        "F2",   # test all solutions
        "7",
        "F2",   # generate stats
        "K",
        "F10",
    ]
    # fmt: on
    run_scenario(tmp_path, keys)

    stats = tmp_path / "reports" / "scoring_stats"
    assert (
        stats.read_text()
        == """\
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

"""
    )
