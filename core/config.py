import grp
import logging.config
import os
import pwd
import traceback

from celery.utils.log import get_task_logger

from core.env import OJ_ENV, OJ_DEBUG

UNLIMITED = -1


class Result:
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
        Result.RESULT_SUCCESS: ACCEPTED,
        Result.RESULT_WRONG_ANSWER: WRONG_ANSWER,
        Result.RESULT_CPU_TIME_LIMIT_EXCEEDED: TIME_LIMIT_EXCEEDED,
        Result.RESULT_REAL_TIME_LIMIT_EXCEEDED: TIME_LIMIT_EXCEEDED,
        Result.RESULT_MEMORY_LIMIT_EXCEEDED: MEMORY_LIMIT_EXCEEDED,
        Result.RESULT_RUNTIME_ERROR: RUNTIME_ERROR,
        Result.RESULT_SYSTEM_ERROR: SYSTEM_ERROR,
        Result.RESULT_PRESENTATION_ERROR: PRESENTATION_ERROR
    }


if OJ_ENV != 'container':
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
simple_format = '[%(levelname)s][%(asctime)s][%(filename)s:%(lineno)d]%(message)s'
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            # 'datefmt': '%m-%d-%Y %H:%M:%S'
            'format': simple_format
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'simple',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'
        },
    },
    'loggers': {
        'myapp': {
            'handlers': ['console'],
            'level': 'INFO' if not OJ_DEBUG else 'DEBUG',
            'propagate': True,
        }
    }
}

logging.config.dictConfig(LOG_CONFIG)
logger = get_task_logger('myapp')
