import grp
import os
import pwd
import traceback

if os.getenv('ddlcw_env', 'production') == 'development':
    DDLCW_DEBUG = True
else:
    DDLCW_DEBUG = False
UNLIMITED = -1

ACCEPT_SUBMISSION_LANGUAGES = ['c', 'cpp', 'java', 'go', 'python', 'kotlin']
ACCEPT_SPJ_LANGUAGES = ['c']

RESULT_SUCCESS = 0
RESULT_WRONG_ANSWER = -1
RESULT_CPU_TIME_LIMIT_EXCEEDED = 1
RESULT_REAL_TIME_LIMIT_EXCEEDED = 2
RESULT_MEMORY_LIMIT_EXCEEDED = 3
RESULT_RUNTIME_ERROR = 4
RESULT_SYSTEM_ERROR = 5
RESULT_PRESENTATION_ERROR = 6

ERROR_INVALID_CONFIG = -1
ERROR_FORK_FAILED = -2
ERROR_PTHREAD_FAILED = -3
ERROR_WAIT_FAILED = -4
ERROR_ROOT_REQUIRED = -5
ERROR_LOAD_SECCOMP_FAILED = -6
ERROR_SETRLIMIT_FAILED = -7
ERROR_DUP2_FAILED = -8
ERROR_SETUID_FAILED = -9
ERROR_EXECVE_FAILED = -10
ERROR_SPJ_ERROR = -11


class Verdict:
    PENDING = 'P'
    RUNNING = 'R'
    ACCEPTED = 'AC'
    SYNC_TEST_CASES = 'SYNC'
    PRESENTATION_ERROR = 'PE'
    TIME_LIMIT_EXCEEDED = 'TLE'
    MEMORY_LIMIT_EXCEEDED = 'MLE'
    WRONG_ANSWER = 'WA'
    RUNTIME_ERROR = 'RE'
    OUTPUT_LIMIT_EXCEEDED = 'OLE'
    COMPILE_ERROR = 'CE'
    SYSTEM_ERROR = 'SE'
    VERDICT_MAPPING = {
        RESULT_SUCCESS: ACCEPTED,
        RESULT_WRONG_ANSWER: WRONG_ANSWER,
        RESULT_CPU_TIME_LIMIT_EXCEEDED: TIME_LIMIT_EXCEEDED,
        RESULT_REAL_TIME_LIMIT_EXCEEDED: TIME_LIMIT_EXCEEDED,
        RESULT_MEMORY_LIMIT_EXCEEDED: MEMORY_LIMIT_EXCEEDED,
        RESULT_RUNTIME_ERROR: RUNTIME_ERROR,
        RESULT_SYSTEM_ERROR: SYSTEM_ERROR,
        RESULT_PRESENTATION_ERROR: PRESENTATION_ERROR
    }


if DDLCW_DEBUG:
    BASE_DIR = os.path.abspath('./judge')
    TMP_DIR = os.path.join(BASE_DIR, 'tmp')
else:
    BASE_DIR = '/judge'
    TMP_DIR = '/tmp'

RUNNER_DIR = os.path.join(BASE_DIR, 'runner')
UPLOAD_DIR = os.path.join(BASE_DIR, 'upload')

PROBLEM_TEST_CASES_DIR = os.path.join(BASE_DIR, 'test_cases')

try:
    os.makedirs(RUNNER_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
except Exception:
    traceback.print_exc()

RUN_USER_UID = pwd.getpwnam("code").pw_uid
RUN_GROUP_GID = grp.getgrnam("code").gr_gid
# tasks producer queue
BROKER_URL = f"amqp://{os.getenv('RABBITMQ_USER', 'guest')}:{os.getenv('RABBITMQ_PASS', 'guest')}" \
             f"@{os.getenv('RABBITMQ_HOST', '127.0.0.1')}:{os.getenv('RABBITMQ_PORT', 5672)}/"
BACKEND_BASE_URL = f"{os.getenv('BACKEND_PROTOCOL', 'http')}://" \
                   f"{os.getenv('BACKEND_HOST', '127.0.0.1')}:{os.getenv('BACKEND_PORT', 8000)}"
BACKEND_SYNC_TEST_CASES_URL = BACKEND_BASE_URL + '/api/problem/{problem_id}/sync_test_cases/'
JUDGE_TOKEN = os.getenv('JUDGE_TOKEN', 'JUDGE_TOKEN')
