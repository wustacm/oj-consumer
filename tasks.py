import traceback

from celery import Celery

from ddlcw import Runner as JudgeRunner
from ddlcw.config import Verdict, ACCEPT_SUBMISSION_LANGUAGES
from distribute.config import PROBLEM_TEST_CASES_DIR
from distribute.utils import validate_manifest, ManifestError, load_submission_config, load_spj_config
import os

app = Celery('tasks', broker_url=f'amqp://guest:guest@{os.getenv("RABBITMQ_HOST", "127.0.0.1")}:5672/')
app.conf.update(
    enable_utc=True,
    task_serializer='json',
    timezone='UTC'
)


@app.task(name='result_submission_task')
def result_submission_task(submission_id, verdict, time_spend, memory_spend, additional_info):
    print(submission_id, verdict, time_spend, memory_spend, additional_info)


@app.task(name='run_submission_task')
def run_submission_task(submission_id, manifest, code, language, time_limit, memory_limit):
    result_submission_task.apply_async(args=[submission_id, Verdict.RUNNING, None, None, {}], queue='result')
    if language not in ACCEPT_SUBMISSION_LANGUAGES:
        result_submission_task.apply_async(
            args=[submission_id, Verdict.SYSTEM_ERROR, None, None, {'error': f'language {language} not support'}],
            queue='result')
    # initialize runner
    try:
        validate_manifest(manifest)
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
