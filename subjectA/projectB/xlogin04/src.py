#rename solution

# solution is dir
if env.cwd.proj.solution_type_dir:
    pass
# solution is file
else:
    solutions = get_solution_files(env)
    for solution in solutions:
        try:
            # check if solution is named correctly
            if fnmatch.fnmatch(solution, env.cwd.proj.sut_required):
                ok.append(solution)
            else:
                for ext in env.cwd.proj.sut_ext_variants:
                    extention = os.path.join(os.path.dirname(solution), ext)
                    if fnmatch.fnmatch(solution, extention):
                        old_file = solution
                        new_file = os.path.join(os.path.dirname(old_file), env.cwd.proj.sut_required)
                        shutil.copy(old_file, new_file)
                        renamed.append(solution)
                        add_tag_to_file(old_file, "renamed", ["-1b"])
        except:
            fail.append(solution)

