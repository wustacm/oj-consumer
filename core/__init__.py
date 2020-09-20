import json
import os
import shutil
import subprocess
import uuid

from core import runner
from core.config import Result, RUN_USER_UID, RUN_GROUP_GID, RUNNER_DIR, UNLIMITED, logger
from core.exceptions import CompileError


class Runner:
    # 初始化一个运行的Runner
    def __init__(self, test_case_dir, manifest, time_limit, memory_limit, code, language_config, spj_config):
        self._original_dir = os.path.abspath('.')
        self._manifest = manifest
        self._test_cases_dir = os.path.abspath(
            os.path.join(test_case_dir, self._manifest['hash']))
        # int, unit is ms
        self._time_limit = time_limit
        # int, unit is MB
        self._memory_limit = memory_limit
        self._compile_config = language_config['compile']
        self._language_config = language_config
        self._runner_path = os.path.join(RUNNER_DIR, str(uuid.uuid4()))
        if not os.path.exists(self._runner_path):
            os.makedirs(self._runner_path)
        os.chown(self._runner_path, RUN_USER_UID, RUN_GROUP_GID)
        self._src_path = os.path.join(
            self._runner_path, self._compile_config['src_name'])
        with open(self._src_path, 'w') as f:
            f.write(code)

        self._exe_path = os.path.join(
            self._runner_path, self._compile_config["exe_name"])
        if not os.path.exists(self._runner_path):
            os.makedirs(self._runner_path)
            os.chown(self._runner_path, RUN_USER_UID,
                     RUN_GROUP_GID)
        self._compiler_out = os.path.join(self._runner_path, 'compile.out')
        self._compiler_spj_out = os.path.join(self._runner_path, 'compile_spj.out')
        self._compiler_log = os.path.join(self._runner_path, 'compile.log')
        self._compiler_spj_log = os.path.join(self._runner_path, 'compile_spj.log')
        self._spj = False
        self._spj_lang = 'c'
        self._spj_code = ''
        self._spj_src_path = ''
        self._spj_exe_path = ''
        self._spj_config = spj_config
        self._run_config = language_config['run']
        self._run_log = os.path.join(self._runner_path, "run.log")
        if self._manifest['spj'] is True:
            self._spj = True
            self._spj_code = self._manifest['spj_code']
            self._spj_src_path = os.path.join(self._runner_path,
                                              self._spj_config['compile']['src_name'])
            self._spj_exe_path = os.path.join(self._runner_path,
                                              self._spj_config['compile']['exe_name'])
            with open(self._spj_src_path, 'w') as f:
                f.write(self._spj_code)

    # 编译SPJ代码

    def _compile_spj(self):
        compile_config = self._spj_config['compile']
        command = compile_config['compile_command']
        command = command.format(
            src_path=self._spj_src_path, exe_path=self._spj_exe_path)
        _command = command.split(' ')
        os.chdir(self._runner_path)
        runner_env = compile_config.get("env", [])
        runner_env.append("PATH=" + os.getenv("PATH"))
        if os.getenv("JAVA_OPTS"):
            runner_env.append("JAVA_OPTS=" + os.getenv("JAVA_OPTS"))
        spj_compile_result = runner.run(max_cpu_time=compile_config['max_cpu_time'],
                                        max_real_time=compile_config['max_real_time'],
                                        max_memory=compile_config['max_memory'],
                                        max_stack=128 * 1024 * 1024,
                                        max_output_size=20 * 1024 * 1024,
                                        max_process_number=UNLIMITED,
                                        exe_path=_command[0],
                                        input_path=self._spj_src_path,
                                        output_path=self._compiler_spj_out,
                                        error_path=self._compiler_spj_out,
                                        args=_command[1::],
                                        env=runner_env,
                                        log_path=self._compiler_log,
                                        seccomp_rule_name=None,
                                        uid=RUN_USER_UID,
                                        gid=RUN_GROUP_GID)
        logger.debug(spj_compile_result)
        if spj_compile_result["result"] != Result.RESULT_SUCCESS:
            if os.path.exists(self._compiler_out):
                with open(self._compiler_out, encoding="utf-8") as f:
                    error = f.read().strip()
                    if error:
                        raise CompileError('Compile spj error.\n' + error)
            raise CompileError("Compile spj runtime error, info:\n%s" %
                               json.dumps(spj_compile_result))

    # 编译用户代码

    def compile(self):
        if self._spj:
            self._compile_spj()
        compile_config = self._language_config['compile']
        command = compile_config["compile_command"]
        command = command.format(
            src_path=self._src_path, exe_dir=self._runner_path, exe_path=self._exe_path)
        _command = command.split(" ")
        os.chdir(self._runner_path)
        runner_env = ["PATH=" + os.environ.get("PATH", "")] + self._compile_config.get("env", [])
        if os.getenv("JAVA_OPTS"):
            runner_env.append(f'JAVA_OPTS={os.getenv("JAVA_OPTS")}')
        result = runner.run(max_cpu_time=compile_config["max_cpu_time"],
                            max_real_time=compile_config["max_real_time"],
                            max_memory=compile_config["max_memory"],
                            max_stack=128 * 1024 * 1024,
                            max_output_size=20 * 1024 * 1024,
                            max_process_number=UNLIMITED,
                            exe_path=_command[0],
                            input_path=self._src_path,
                            output_path=self._compiler_out,
                            error_path=self._compiler_out,
                            args=_command[1::],
                            env=runner_env,
                            log_path=self._compiler_log,
                            seccomp_rule_name=None,
                            uid=RUN_USER_UID,
                            gid=RUN_GROUP_GID)
        logger.debug('compile result:' + str(result))
        os.chdir(self._original_dir)
        if result["result"] != Result.RESULT_SUCCESS:
            if os.path.exists(self._compiler_out):
                with open(self._compiler_out, encoding="utf-8") as f:
                    error = f.read().strip()
                    logger.debug(error)
                    if error:
                        raise CompileError(error)
            raise CompileError(
                "Compiler runtime error, info: \n%s\n" % json.dumps(result))
        else:
            return result

    # 运行单个测试样例的SPJ代码

    def _judge_single_spj(self, input_path, output_path, user_output_path, test_case):
        # 将test case拷贝到运行目录下面，并且分配权限
        spj_in_file_path = os.path.join(self._runner_path, test_case['in'])
        spj_out_file_path = os.path.join(self._runner_path, test_case['out'])
        shutil.copyfile(input_path, spj_in_file_path)
        shutil.copyfile(output_path, spj_out_file_path)
        os.chown(spj_in_file_path, RUN_USER_UID, RUN_GROUP_GID)
        os.chown(spj_out_file_path, RUN_USER_UID, RUN_GROUP_GID)

        command = self._spj_config['run']['command'].format(exe_path=self._spj_exe_path,
                                                            in_file_path=spj_in_file_path,
                                                            out_file_path=spj_out_file_path,
                                                            user_out_file_path=user_output_path).split(" ")
        runner_env = ["PATH=" + os.environ.get("PATH", "")]
        if os.getenv("JAVA_OPTS"):
            runner_env.append(f'JAVA_OPTS={os.getenv("JAVA_OPTS")}')
        seccomp_rule = self._spj_config['run']["seccomp_rule"]
        in_file_path = os.path.join(self._test_cases_dir, test_case['in'])
        # run test case output path & run test case error path
        run_out_file_path = os.path.join(self._runner_path, test_case['out'] + '.spj.out')
        run_out_err_path = os.path.join(self._runner_path, test_case['out'] + '.spj.err')
        run_result = runner.run(max_cpu_time=self._time_limit * 3,
                                max_real_time=self._time_limit * 3,
                                max_memory=self._memory_limit * 1024 * 1024,
                                max_stack=128 * 1024 * 1024,
                                max_output_size=1024 * 1024 * 16,
                                max_process_number=UNLIMITED,
                                exe_path=command[0],
                                args=command[1::],
                                env=runner_env,
                                input_path=in_file_path,
                                output_path=run_out_file_path,
                                error_path=run_out_err_path,
                                log_path=self._run_log,
                                seccomp_rule_name=seccomp_rule,
                                uid=RUN_USER_UID,
                                gid=RUN_GROUP_GID,
                                memory_limit_check_only=self._run_config.get("memory_limit_check_only", 0))
        logger.debug(run_result)
        return run_result

    # 运行单个测试样例

    def _judge_single(self, test_case):
        # test case input and output path
        in_file_path = os.path.join(self._test_cases_dir, test_case['in'])
        out_file_path = os.path.join(self._test_cases_dir, test_case['out'])
        # run test case output path & run test case error path
        run_out_file_path = os.path.join(self._runner_path, test_case['out'])
        run_out_err_path = os.path.join(
            self._runner_path, test_case['in'] + '.err')

        command = self._run_config["command"].format(exe_path=self._exe_path, exe_dir=self._runner_path,
                                                     max_memory=int(self._memory_limit * 1024)).split(" ")
        runner_env = ["PATH=" + os.environ.get("PATH", "")] + self._run_config.get("env", [])
        seccomp_rule = self._run_config.get("seccomp_rule")

        run_result = runner.run(max_cpu_time=self._time_limit * 3,
                                max_real_time=self._time_limit * 3,
                                max_memory=self._memory_limit * 1024 * 1024,
                                max_stack=128 * 1024 * 1024,
                                max_output_size=1024 * 1024 * 16,
                                max_process_number=UNLIMITED,
                                exe_path=command[0],
                                args=command[1::],
                                env=runner_env,
                                input_path=in_file_path,
                                output_path=run_out_file_path,
                                error_path=run_out_err_path,
                                log_path=self._run_log,
                                seccomp_rule_name=seccomp_rule,
                                uid=RUN_USER_UID,
                                gid=RUN_GROUP_GID,
                                memory_limit_check_only=self._run_config.get("memory_limit_check_only", 0))
        run_result['memory'] = run_result['memory'] // 1024 // 1024
        logger.debug(run_result)
        if run_result["result"] != Result.RESULT_SUCCESS:
            return run_result
        if self._spj:
            spj_run_result = self._judge_single_spj(
                in_file_path, out_file_path, run_out_file_path, test_case)
            if spj_run_result['exit_code'] == 0:
                run_result['result'] = spj_run_result['result']
            elif spj_run_result['exit_code'] == 1:
                run_result['result'] = Result.RESULT_WRONG_ANSWER
            else:
                run_result['result'] = Result.RESULT_SYSTEM_ERROR
        else:
            if not os.path.exists(run_out_file_path):
                run_result["result"] = Result.RESULT_WRONG_ANSWER
            else:
                run_result["result"] = Runner.diff(
                    standard_path=out_file_path, output_path=run_out_file_path)
        return run_result

    # if output is PE or AC or WA ?
    # reference to: https://github.com/4ddl/docs/blob/master/err.md
    # 比较用户的输出结果是否正确，可以判断PE，WA或者AC。
    @staticmethod
    def diff(standard_path, output_path):
        args1 = ['diff', '-Z', standard_path, output_path]
        args2 = ['diff', '-a', '-w', '-B', standard_path, output_path]
        proc = subprocess.Popen(
            args1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if err:
            return Result.RESULT_SYSTEM_ERROR
        if not out:
            return Result.RESULT_SUCCESS
        proc = subprocess.Popen(
            args2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if err:
            return Result.RESULT_SYSTEM_ERROR
        if not out:
            return Result.RESULT_PRESENTATION_ERROR
        return Result.RESULT_WRONG_ANSWER

    # 运行所有数据

    def run(self):
        result = []
        for item in self._manifest['test_cases']:
            result.append(self._judge_single(item))
        return result

    def clean(self):
        shutil.rmtree(self._runner_path, ignore_errors=True)
