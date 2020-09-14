import json
import os
from json import JSONDecodeError

import yaml
from yaml import YAMLError

from .config import PROBLEM_TEST_CASES_DIR
import traceback

class ManifestError(Exception):
    pass


def validate_test_case(dir_name, filename):
    if not os.path.exists(PROBLEM_TEST_CASES_DIR) or not os.path.isdir(PROBLEM_TEST_CASES_DIR):
        raise ManifestError('problem test cases dir not exist')
    problem_test_case_dir = os.path.join(PROBLEM_TEST_CASES_DIR, dir_name)
    if not os.path.exists(problem_test_case_dir) or not os.path.isdir(problem_test_case_dir):
        raise ManifestError('this problem test case dir not exist')
    file_path = os.path.join(problem_test_case_dir, filename)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise ManifestError('this problem test case dir not exist')
    if not os.access(file_path, os.R_OK):
        raise ManifestError(f'file "{file_path}" not readable.')


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
            raise ManifestError(f'test_cases item {item} not dict')
        if 'in' not in item.keys():
            raise ManifestError('test_cases item needs key(in)')
        if not isinstance(item.get('in'), str):
            raise ManifestError('test_cases item key(in) type error')
        if len(item.get('in')) == 0:
            raise ManifestError('test_cases item key(in) length 0')
        validate_test_case(manifest.get('hash'), item.get('in'))
        if not manifest.get('spj'):
            if 'out' not in item.keys():
                raise ManifestError('test_cases item needs key(out)')
            if not isinstance(item.get('out'), str):
                raise ManifestError('test_cases item key(out) type error')
            if len(item.get('out')) == 0:
                raise ManifestError('test_cases item key(out) length 0')
            validate_test_case(manifest.get('hash'), item.get('out'))
    return manifest


def load_submission_config(lang):
    print(os.path.abspath('.'))
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
