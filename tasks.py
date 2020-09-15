import traceback

from celery import Celery

from ddlcw import Runner as JudgeRunner
from ddlcw.config import Verdict, PROBLEM_TEST_CASES_DIR, BROKER_URL
from ddlcw.config import logger
from ddlcw.env import DDLCW_ENABLE_SYNC
from ddlcw.languages import ACCEPT_SUBMISSION_LANGUAGES
from ddlcw.utils import load_spj_config, load_submission_config, validate_manifest, ManifestError, TestCaseError, \
    sync_test_cases

app = Celery('tasks')
app.conf.update(
    broker_url=BROKER_URL,
    enable_utc=True,
    task_serializer='json',
)


@app.task(name='result_submission_task')
def result_submission_task(submission_id, verdict, time_spend, memory_spend, additional_info):
    print(submission_id, verdict, time_spend, memory_spend, additional_info)


@app.task(name='run_submission_task')
def run_submission_task(submission_id, problem_id, manifest, code, language, time_limit, memory_limit):
    logger.debug(submission_id, problem_id, manifest, code, language, time_limit, memory_limit)
    result_submission_task.apply_async(args=[submission_id, Verdict.RUNNING, None, None, {}], queue='result')
    if language not in ACCEPT_SUBMISSION_LANGUAGES:
        logger.warning('request language not valid')
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': f'language {language} not support'}],
            queue='result')
    # initialize runner
    try:
        validate_manifest(manifest)
    except TestCaseError as test_case_error:
        logger.debug(test_case_error)
        if DDLCW_ENABLE_SYNC:
            # sync test cases
            result_submission_task.apply_async(args=[submission_id, Verdict.SYNC_TEST_CASES, None, None, {}],
                                               queue='result')
            logger.debug("sync test cases")
            try:
                sync_test_cases(manifest['hash'], problem_id)
                validate_manifest(manifest)
            except ManifestError as e:
                traceback.print_exc()
                result_submission_task.apply_async(
                    args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(e)}], queue='result')
                return
        else:
            # sync test cases disabled, return system error
            result_submission_task.apply_async(
                args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(test_case_error)}],
                queue='result')
    except ManifestError as e:
        logger.debug(e)
        result_submission_task.apply_async(args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(e)}],
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
        result_submission_task.apply_async(args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(e)}],
                                           queue='result')
        return
    # compile code
    try:
        runner.compile()
    except Exception as e:
        traceback.print_exc()
        result_submission_task.apply_async(args=[submission_id, Verdict.COMPILE_ERROR, None, None, {'error': repr(e)}],
                                           queue='result')
        return
    # run code
    try:
        result = runner.run()
        verdict = Verdict.ACCEPTED
        # attention: time spend and memory spend indicated maximum case time spend and maximum case memory spend
        time_spend = 0
        memory_spend = 0
        for item in result:
            # calculate max time spend and memory spend
            time_spend = max(time_spend, item['real_time'])
            memory_spend = max(memory_spend, item['memory'])
            if item['result'] != 0:
                verdict = Verdict.VERDICT_MAPPING[item['result']]
                break
        result_submission_task.apply_async(args=[submission_id, verdict, time_spend, memory_spend, {'result': result}],
                                           queue='result')
    except Exception as e:
        traceback.print_exc()
        result_submission_task.apply_async(args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(e)}],
                                           queue='result')
        return
    try:
        # clean running directory
        runner.clean()
    except OSError:
        pass
