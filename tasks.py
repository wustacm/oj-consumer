import traceback

import sentry_sdk
from celery import Celery
from celery.signals import setup_logging
from sentry_sdk.integrations.celery import CeleryIntegration
from celery.utils.nodenames import default_nodename

from core import Runner as JudgeRunner
from core.config import Verdict, PROBLEM_TEST_CASES_DIR
from core.config import logger
from core.env import OJ_ENABLE_SYNC, BROKER_URL
from core.languages import ACCEPT_SUBMISSION_LANGUAGES
from core.utils import load_spj_config, load_submission_config, validate_manifest, ManifestError, TestCaseError, \
    sync_test_cases

sentry_sdk.init(dsn='https://5e1c2c755d414a0b87c2d9e8d763c1b3@o428533.ingest.sentry.io/5432217',
                integrations=[CeleryIntegration()])

app = Celery('tasks')
app.conf.update(
    broker_url=BROKER_URL,
    enable_utc=True,
    task_serializer='json',
)


@setup_logging.connect
def setup_celery_logger(*args, **kwargs):
    pass


@app.task(name='result_submission_task')
def result_submission_task(submission_id, verdict, time_spend, memory_spend, additional_info):
    print(submission_id, verdict, time_spend, memory_spend, additional_info)


@app.task(name='run_submission_task')
def run_submission_task(submission_id, problem_id, manifest, code, language, time_limit, memory_limit):
    logger.debug(submission_id, problem_id, manifest, code, language, time_limit, memory_limit)
    result_submission_task.apply_async(
        args=[submission_id, Verdict.RUNNING, None, None, {'node': default_nodename(None)}], queue='result')
    if language not in ACCEPT_SUBMISSION_LANGUAGES:
        logger.warning('request language not valid')
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None,
                  {'error': f'language {language} not support', 'node': default_nodename(None)}],
            queue='result')
    # initialize runner
    try:
        validate_manifest(manifest)
    except TestCaseError as test_case_error:
        logger.debug(test_case_error)
        if OJ_ENABLE_SYNC:
            # sync test cases
            result_submission_task.apply_async(
                args=[submission_id, Verdict.SYNC_TEST_CASES, None, None, {'node': default_nodename(None)}],
                queue='result')
            logger.debug("sync test cases")
            try:
                sync_test_cases(manifest['hash'], problem_id)
                validate_manifest(manifest)
            except ManifestError as e:
                traceback.print_exc()
                result_submission_task.apply_async(
                    args=[submission_id, Verdict.SYSTEM_ERROR, None, None,
                          {'error': str(e), 'node': default_nodename(None)}], queue='result')
                return
        else:
            # sync test cases disabled, return system error
            result_submission_task.apply_async(
                args=[submission_id, Verdict.SYSTEM_ERROR, None, None,
                      {'error': str(test_case_error), 'node': default_nodename(None)}],
                queue='result')
    except ManifestError as e:
        logger.debug(e)
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': str(e), 'node': default_nodename(None)}],
            queue='result')
        return
    try:
        runner = JudgeRunner(PROBLEM_TEST_CASES_DIR,
                             manifest,
                             time_limit,
                             memory_limit,
                             code,
                             load_submission_config(language), load_spj_config('c'))
    except Exception as e:
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': str(e), 'node': default_nodename(None)}],
            queue='result')
        return
    # compile code
    try:
        res_compile = runner.compile()
        logger.debug('compile result:' + str(res_compile))
    except Exception as e:
        logger.debug('compile error:' + str(e))
        result_submission_task.apply_async(
            args=[submission_id, Verdict.COMPILE_ERROR, None, None, {'error': str(e), 'node': default_nodename(None)}],
            queue='result')
        return
    # run code
    try:
        result = runner.run()
        verdict = Verdict.ACCEPTED
        # attention: time spend and memory spend indicated maximum case time spend and maximum case memory spend
        time_cost = 0
        memory_cost = 0
        for item in result:
            # calculate max time spend and memory spend
            time_cost = max(time_cost, item['cpu_time'])
            memory_cost = max(memory_cost, item['memory'])
            if item['result'] != 0:
                verdict = Verdict.VERDICT_MAPPING[item['result']]
                break
        result_submission_task.apply_async(
            args=[submission_id, verdict, time_cost, memory_cost, {'result': result, 'node': default_nodename(None)}],
            queue='result')
    except Exception as e:
        traceback.print_exc()
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': str(e), 'node': default_nodename(None)}],
            queue='result')
        return
    try:
        # clean running directory
        runner.clean()
    except OSError:
        pass
