import traceback

from celery import Celery

from ddlcw import Runner as JudgeRunner
from ddlcw.config import Verdict, ACCEPT_SUBMISSION_LANGUAGES, PROBLEM_TEST_CASES_DIR, BROKER_URL, DDLCW_DEBUG
from ddlcw.utils import load_spj_config, load_submission_config, validate_manifest, ManifestError, TestCaseError, \
    sync_test_cases

app = Celery('tasks')
app.conf.update(
    broker_url=BROKER_URL,
    enable_utc=True,
    task_serializer='json',
    timezone='UTC'
)


@app.task(name='result_submission_task')
def result_submission_task(submission_id, verdict, time_spend, memory_spend, additional_info):
    print(submission_id, verdict, time_spend, memory_spend, additional_info)


@app.task(name='run_submission_task')
def run_submission_task(submission_id, problem_id, manifest, code, language, time_limit, memory_limit):
    result_submission_task.apply_async(args=[submission_id, Verdict.RUNNING, None, None, {}], queue='result')
    if language not in ACCEPT_SUBMISSION_LANGUAGES:
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': f'language {language} not support'}],
            queue='result')
    # initialize runner
    try:
        validate_manifest(manifest)
    except TestCaseError:
        if DDLCW_DEBUG:
            print('--------------------------------------- validate manifest error -----------------------------------')
            traceback.print_exc()
        result_submission_task.apply_async(args=[submission_id, Verdict.SYNC_TEST_CASES, None, None, {}],
                                           queue='result')
        try:
            sync_test_cases(manifest['hash'], problem_id)
            validate_manifest(manifest)
        except ManifestError as e:
            traceback.print_exc()
            result_submission_task.apply_async(
                args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(e)}], queue='result')
            return
    except ManifestError as e:
        traceback.print_exc()
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': repr(e)}], queue='result')
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
