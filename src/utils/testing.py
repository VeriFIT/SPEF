



""" /bin/t --> spusti /tests/testsuite.sh --- ten spusta /bin/tst run param """
# def run_testsuite(stdscr, env, solution_dir):
def tmp_fce(stdscr, env, solution_dir):
    if not env.cwd.proj or not solution_dir:
        log("run testsuite | run from solution dir in some project dir")
        return

    ############### 1. nastavenie premennych ###############
    command = ""
    proj_dir = env.cwd.proj.path
    tests_dir = os.path.join(proj_dir, TESTS_DIR)
    scoring_file = os.path.join(tests_dir, SCORING_FILE)
    testsuite_file = os.path.join(tests_dir, TESTSUITE_FILE)
    if not os.path.exists(tests_dir) or not os.path.isdir(tests_dir):
        log(f"run testsuite | tests_dir '{tests_dir}' doesnt exists or its not a directory")
        return env
    if not os.path.exists(scoring_file):
        log(f"run testsuite | scoring file '{scoring_file}' doesnt exist")
        return env
    if not os.path.exists(testsuite_file):
        log(f"run testsuite | testsuite '{testsuite_file}' doesnt exist")
        return env
    if not os.access(testsuite_file, os.X_OK):
        log(f"run testsuite | testsuite '{testsuite_file}' is not executable (try: chmod +x testsuite.sh)")
        return env


    """
    # if [ -f $PROJDIR/sandbox.config ]; then
        # . $PROJDIR/sandbox.config
    # fi
    # export SANDBOXUSER
    # export SANDBOXDIR
    # export SANDBOXLOCK
    """
    ############### 2. nastavenie izolovaneho prostredia ###############
    # TODO !!!!!!!
    pass


    ############### 3. kontrola bash funkcii v tests_dir ###############
    # ci su nakopirovane bash funkcie v tests_dir (ak nie, nakopiruj ich do tests_dir/DST_BASH_FILE)
    bash_tests_ok = check_bash_functions_for_testing(env.cwd.proj.path)
    if not bash_tests_ok:
        log("run testsuite | problem with bash functions for tests")
        return env


    ############### 4. spristupni tst funkcie ###############
    # spristupnit bin/tst (run_test), bin/n (add_note) pre testsuite.sh
    # TODO !!!!!!!
    # SRC_BASH_DIR = '/testing/tst.py'  --> SRC_BASH_DIR/tst.py run test_name
    # SRC_BASH_DIR = '/testing/tst'     --> SRC_BASH_DIR/tst run test_name
    # command += f"export PATH={SRC_BASH_DIR}:$PATH\n"  
    tmp_dir = os.path.join(tests_dir, DST_BASH_DIR)
    command += f"export PATH={tmp_dir}:$PATH\n"  
    command += f"export TESTSDIR={tests_dir}\n"


    ############### 5. spusti testsuite ###############
    # (execute sh script)
    command += f"cd {solution_dir}\n"
    command += f"{testsuite_file}\n"

    # command += f"{print_score}\n"

    env.bash_active = True
    env.bash_action = Bash_action()
    env.bash_action.dont_jump_to_cwd()
    env.bash_action.add_command(command)
    return env

    # PRINT SCORE
    # echo ====================================
    # grep -m1 "^[0-9].*:celkem" hodnoceni-auto
    # echo Stiskni enter...; read
