import json
import os
import subprocess
import uuid
from multiprocessing import Pool

import psutil

from ddlcw import config
from ddlcw import runner
from ddlcw.exceptions import CompileError, JudgeError
from ddlcw import languages


def _run(instance, test_case):
    return instance._judge_single(test_case)


class Runner:
    def __init__(self, manifest, time_limit, memory_limit, code, language_config):
        # test cases file list
        # {'hash':'','test_cases':[{'in': '1.in', 'out': '1.out'},{'in': '2.in', 'out': '2.out'}], 'spj': true, 'spj_code': '#include<stdio.h>\nint main(){\n   return 0;\n}\n'}
        self._manifest = manifest
        self._test_cases_dir = os.path.join(config.TEST_CASES_DIR, self._manifest['hash'])
        # int, unit is ms
        self._time_limit = time_limit
        # int, unit is MB
        self._memory_limit = memory_limit
        self._compile_config = language_config['compile']
        self._language_config = language_config
        self._runner_path = os.path.join(config.RUNNER_DIR, str(uuid.uuid4()))
        if not os.path.exists(self._runner_path):
            os.makedirs(self._runner_path)
        os.chown(self._runner_path, config.RUN_USER_UID, config.RUN_GROUP_GID)
        self._src_path = os.path.join(self._runner_path, self._compile_config['src_name'])
        with open(self._src_path, 'w') as f:
            f.write(code)

        self._exe_path = os.path.join(self._runner_path, self._compile_config["exe_name"])
        if not os.path.exists(self._runner_path):
            os.makedirs(self._runner_path)
            os.chown(self._runner_path, config.RUN_USER_UID, config.RUN_GROUP_GID)
        self._compiler_out = os.path.join(self._runner_path, "compiler.out")
        self._compiler_log = os.path.join(self._runner_path, "compiler.log")
        self._spj = False
        self._spj_code = ''
        self._spj_src_path = ''
        self._spj_exe_path = ''
        self._spj_version = 'ver1'
        self._run_config = language_config['run']
        self._run_log = os.path.join(self._runner_path, "run.log")
        self._pool = Pool(processes=psutil.cpu_count())
        if self._manifest['spj'] is True:
            self._spj = True
            self._spj_code = self._manifest['spj_code']
            self._spj_src_path = os.path.join(self._runner_path,
                                              languages.c_lang_spj_compile['src_path']).format(
                spj_version=self._spj_version)
            self._spj_exe_path = os.path.join(self._runner_path,
                                              languages.c_lang_spj_compile['exe_path']).format(
                spj_version=self._spj_version)
            with open(self._spj_src_path, 'w') as f:
                f.write(self._spj_code)

    def _compile_spj(self):
        compile_config = languages.c_lang_spj_compile
        command = compile_config['compile_command']
        command = command.format(src_path=self._spj_src_path, exe_path=self._spj_exe_path)
        _command = command.split(' ')
        os.chdir(self._runner_path)
        env = 'PATH=' + os.getenv('PATH')
        spj_compile_result = runner.run(max_cpu_time=compile_config['max_cpu_time'],
                                        max_real_time=compile_config['max_real_time'],
                                        max_memory=compile_config['max_memory'],
                                        max_stack=128 * 1024 * 1024,
                                        max_output_size=20 * 1024 * 1024,
                                        max_process_number=config.UNLIMITED,
                                        exe_path=_command[0],
                                        input_path=self._spj_src_path,
                                        output_path=self._compiler_out,
                                        error_path=self._compiler_out,
                                        args=_command[1::],
                                        env=env,
                                        log_path=self._compiler_log,
                                        seccomp_rule_name=None,
                                        uid=config.RUN_USER_UID,
                                        gid=config.RUN_GROUP_GID)
        if spj_compile_result["result"] != config.RESULT_SUCCESS:
            if os.path.exists(self._compiler_out):
                with open(self._compiler_out, encoding="utf-8") as f:
                    error = f.read().strip()
                    os.remove(self._compiler_out)
                    if error:
                        raise CompileError(error)
            raise CompileError("Compiler runtime error, info: %s" % json.dumps(spj_compile_result))
        else:
            if os.path.exists(self._compiler_out):
                os.remove(self._compiler_out)
            return self._spj_exe_path

    def compile(self):
        compile_config = self._language_config['compile']
        command = compile_config["compile_command"]
        command = command.format(src_path=self._src_path, exe_dir=self._runner_path, exe_path=self._exe_path)
        _command = command.split(" ")
        os.chdir(self._runner_path)
        env = compile_config.get("env", [])
        env.append("PATH=" + os.getenv("PATH"))
        result = runner.run(max_cpu_time=compile_config["max_cpu_time"],
                            max_real_time=compile_config["max_real_time"],
                            max_memory=compile_config["max_memory"],
                            max_stack=128 * 1024 * 1024,
                            max_output_size=20 * 1024 * 1024,
                            max_process_number=config.UNLIMITED,
                            exe_path=_command[0],
                            input_path=self._src_path,
                            output_path=self._compiler_out,
                            error_path=self._compiler_out,
                            args=_command[1::],
                            env=env,
                            log_path=self._compiler_log,
                            seccomp_rule_name=None,
                            uid=config.RUN_USER_UID,
                            gid=config.RUN_GROUP_GID)
        if result["result"] != config.RESULT_SUCCESS:
            if os.path.exists(self._compiler_out):
                with open(self._compiler_out, encoding="utf-8") as f:
                    error = f.read().strip()
                    os.remove(self._compiler_out)
                    if error:
                        raise CompileError(error)
            raise CompileError("Compiler runtime error, info: %s" % json.dumps(result))
        else:
            if os.path.exists(self._compiler_out):
                os.remove(self._compiler_out)
            return self._exe_path

    def _judge_single(self, test_case):
        # test case input and output path
        in_file_path = os.path.join(self._test_cases_dir, test_case['in'])
        out_file_path = os.path.join(self._test_cases_dir, test_case['out'])

        # run test case output path & run test case error path
        run_out_file_path = os.path.join(self._runner_path, test_case['out'])
        run_out_err_path = os.path.join(self._runner_path, test_case['in'] + '.err')

        command = self._run_config["command"].format(exe_path=self._exe_path, exe_dir=self._runner_path,
                                                     max_memory=int(self._memory_limit * 1024)).split(" ")
        env = ["PATH=" + os.environ.get("PATH", "")] + self._run_config.get("env", [])
        seccomp_rule = self._run_config["seccomp_rule"]

        run_result = runner.run(max_cpu_time=self._time_limit * 3,
                                max_real_time=self._time_limit * 9,
                                max_memory=self._memory_limit * 1024 * 1024,
                                max_stack=128 * 1024 * 1024,
                                max_output_size=1024 * 1024 * 16,
                                max_process_number=config.UNLIMITED,
                                exe_path=command[0],
                                args=command[1::],
                                env=env,
                                input_path=in_file_path,
                                output_path=run_out_file_path,
                                error_path=run_out_err_path,
                                log_path=self._run_log,
                                seccomp_rule_name=seccomp_rule,
                                uid=config.RUN_USER_UID,
                                gid=config.RUN_GROUP_GID,
                                memory_limit_check_only=self._run_config.get("memory_limit_check_only", 0))
        run_result['memory'] = run_result['memory'] // 1024 // 1024

        if run_result["result"] == config.RESULT_SUCCESS:
            if not os.path.exists(run_out_file_path):
                run_result["result"] = config.RESULT_WRONG_ANSWER
            else:
                run_result["result"] = Runner.diff(standard_path=out_file_path, output_path=run_out_file_path)
        return run_result

    # if output is PE or AC or WA ?
    # reference to: https://github.com/4ddl/docs/blob/master/err.md
    @staticmethod
    def diff(standard_path, output_path):
        args1 = ['diff', '-Z', standard_path, output_path]
        args2 = ['diff', '-a', '-w', '-B', standard_path, output_path]
        proc = subprocess.Popen(args1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if err:
            return config.RESULT_SYSTEM_ERROR
        if not out:
            return config.RESULT_SUCCESS
        proc = subprocess.Popen(args2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if err:
            return config.RESULT_SYSTEM_ERROR
        if not out:
            return config.RESULT_PRESENTATION_ERROR
        return config.RESULT_WRONG_ANSWER

    def run(self):
        tmp_result = []
        result = []
        for item in self._manifest['test_cases']:
            tmp_result.append(self._pool.apply_async(_run, (self, item)))
        self._pool.close()
        self._pool.join()
        for item in tmp_result:
            result.append(item.get())
        return result

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        del self_dict["_pool"]
        return self_dict
