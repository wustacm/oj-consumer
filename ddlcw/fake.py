import json
import subprocess

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
    out = {'cpu_time': 0, 'signal': 0, 'memory': 4554752, 'exit_code': 0, 'result': 0, 'error': 0, 'real_time': 2}
    return out
