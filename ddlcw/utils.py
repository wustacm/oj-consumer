import json
import os
from json import JSONDecodeError

import yaml
from yaml import YAMLError
import requests
from ddlcw.config import PROBLEM_TEST_CASES_DIR, BACKEND_SYNC_TEST_CASES_URL, JUDGE_TOKEN, TMP_DIR
import traceback
import zipfile


class ManifestError(Exception):
    pass


class TestCaseError(ManifestError):
    pass


def validate_test_case(dir_name, filename):
    if not os.path.exists(PROBLEM_TEST_CASES_DIR) or not os.path.isdir(PROBLEM_TEST_CASES_DIR):
        raise TestCaseError('problem test cases dir not exist')
    problem_test_case_dir = os.path.join(PROBLEM_TEST_CASES_DIR, dir_name)
    if not os.path.exists(problem_test_case_dir) or not os.path.isdir(problem_test_case_dir):
        raise TestCaseError('this problem test case dir not exist')
    file_path = os.path.join(problem_test_case_dir, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise TestCaseError('this problem test case dir not exist')
    if not os.access(file_path, os.R_OK):
        raise TestCaseError(f'file "{file_path}" not readable.')


def validate_manifest(manifest):
    # check manifest type
    if isinstance(manifest, str):
        try:
            manifest = json.loads(manifest)
        except JSONDecodeError:
            raise ManifestError('decode manifest error')
    if not isinstance(manifest, dict):
        raise ManifestError(
            f'manifest type error, type(manifest)={type(manifest)}')
    # check manifest keys
    keys = ['hash', 'test_cases', 'spj']
    for key in keys:
        if key not in manifest.keys():
            raise ManifestError(f'key {key} not in manifest')
    # check manifest key-values type
    if not isinstance(manifest.get('hash'), str):
        raise ManifestError('hash value not str')
    if len(manifest.get('hash')) == 0:
        raise ManifestError('hash value length 0')
    if not isinstance(manifest.get('test_cases'), list):
        raise ManifestError('test_cases value not list')
    if not isinstance(manifest.get('spj'), bool):
        raise ManifestError('spj value not bool')
    if manifest.get('spj'):
        if 'spj_code' not in manifest.keys() or not isinstance(manifest.get('spj_code'), str):
            raise ManifestError('spj_code value not str')
    # check test_cases
    for item in manifest.get('test_cases'):
        if not isinstance(item, dict):
            raise TestCaseError(f'test_cases item {item} not dict')
        if 'in' not in item.keys():
            raise TestCaseError('test_cases item needs key(in)')
        if not isinstance(item.get('in'), str):
            raise TestCaseError('test_cases item key(in) type error')
        if len(item.get('in')) == 0:
            raise TestCaseError('test_cases item key(in) length 0')
        validate_test_case(manifest.get('hash'), item.get('in'))
        if not manifest.get('spj'):
            if 'out' not in item.keys():
                raise TestCaseError('test_cases item needs key(out)')
            if not isinstance(item.get('out'), str):
                raise TestCaseError('test_cases item key(out) type error')
            if len(item.get('out')) == 0:
                raise TestCaseError('test_cases item key(out) length 0')
            validate_test_case(manifest.get('hash'), item.get('out'))
    return manifest


def load_submission_config(lang):
    with open(f"ddlcw/languages/{lang}.yml", 'r') as f:
        result = f.read()
    try:
        return yaml.load(result, yaml.SafeLoader)
    except YAMLError:
        traceback.print_exc()
        return {}


def load_spj_config(lang):
    with open(f"ddlcw/spj/{lang}.yml", 'r') as f:
        result = f.read()
    try:
        return yaml.load(result, yaml.SafeLoader)
    except YAMLError:
        traceback.print_exc()
        return {}


def sync_test_cases(valid_hash, problem_id):
    os.makedirs(TMP_DIR, exist_ok=True)
    tmp_file_name = f'{valid_hash}.zip'
    tmp_file_path = os.path.join(TMP_DIR, tmp_file_name)
    problem_test_cases_url = BACKEND_SYNC_TEST_CASES_URL.format(problem_id=problem_id)
    res = requests.get(problem_test_cases_url, headers={'JudgeToken': JUDGE_TOKEN})
    if res.status_code != 200:
        return
    with open(tmp_file_path, 'wb') as fd:
        for chunk in res.iter_content(chunk_size=128):
            fd.write(chunk)
    test_cases_dir = os.path.join(PROBLEM_TEST_CASES_DIR, valid_hash)
    os.makedirs(test_cases_dir, exist_ok=True)
    tmp_zip_file = zipfile.ZipFile(tmp_file_path, 'r')
    for item in tmp_zip_file.namelist():
        with open(os.path.join(test_cases_dir, item), 'wb') as f:
            f.write(tmp_zip_file.read(item))
    tmp_zip_file.close()
    os.remove(tmp_file_path)