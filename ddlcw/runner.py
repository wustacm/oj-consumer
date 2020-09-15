import json
import subprocess

from ddlcw.config import UNLIMITED
from ddlcw.env import DDLCW_DEBUG


def run(max_cpu_time,
        max_real_time,
        max_memory,
        max_stack,
        max_output_size,
        max_process_number,
        exe_path,
        input_path,
        output_path,
        error_path,
        args,
        env,
        log_path,
        seccomp_rule_name,
        uid,
        gid,
        memory_limit_check_only=0):
    str_list_vars = ["args", "env"]
    int_vars = ["max_cpu_time", "max_real_time",
                "max_memory", "max_stack", "max_output_size",
                "max_process_number", "uid", "gid", "memory_limit_check_only"]
    str_vars = ["exe_path", "input_path",
                "output_path", "error_path", "log_path"]

    proc_args = ["ddlc"]

    for var in str_list_vars:
        value = vars()[var]
        if not isinstance(value, list):
            raise ValueError("{} must be a list".format(var))
        for item in value:
            if not isinstance(item, str):
                raise ValueError("{} item must be a string".format(var))
            proc_args.append("--{}={}".format(var, item))

    for var in int_vars:
        value = vars()[var]
        if not isinstance(value, int):
            raise ValueError("{} must be a int".format(var))
        if value != UNLIMITED:
            proc_args.append("--{}={}".format(var, value))

    for var in str_vars:
        value = vars()[var]
        if not isinstance(value, str):
            raise ValueError("{} must be a string".format(var))
        proc_args.append("--{}={}".format(var, value))

    if not isinstance(seccomp_rule_name, str) and seccomp_rule_name is not None:
        raise ValueError("seccomp_rule_name must be a string or None")
    if seccomp_rule_name:
        proc_args.append("--seccomp_rule={}".format(seccomp_rule_name))
    if DDLCW_DEBUG:
        print('--------------- ddlc command ---------------')
        print(' '.join(proc_args))
    proc = subprocess.Popen(
        proc_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    out, err = proc.communicate()
    if err:
        raise ValueError("Error occurred while calling ddlc: {}".format(err))
    if DDLCW_DEBUG:
        print('--------------- ddlc run out ---------------')
        print(out)
    return json.loads(out.decode("utf-8"))
