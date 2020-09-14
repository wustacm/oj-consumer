from ddlcw import Runner
import json
import os
from ddlcw.config import DEBUG
from ddlcw.utils import load_spj_config, load_submission_config


def main(test_case_dir, manifest_param, code_param, lang):
    runner = Runner(test_case_dir, manifest_param,
                    1000, 96, code_param, load_submission_config(lang), load_spj_config('c'))
    print(runner.compile())
    print(runner.run())


if __name__ == '__main__':
    manifest = {
        "hash": "1892378192372127389137",
        'test_cases': [{'in': '1.in', 'out': '1.out'}, {'in': '2.in', 'out': '2.out'}],
        'spj': True,
        'spj_code': ''
    }
    with open('test/1/spj.c', 'r') as f:
        manifest['spj_code'] = f.read()
    print('-------------------------test c----------------------')
    with open('test/1/main.c', 'r') as f:
        code = f.read()
    main('/test_cases', manifest, code, 'c')
    print('-------------------------test cpp----------------------')
    with open('test/1/main.cpp', 'r') as f:
        code = f.read()
    main('/test_cases', manifest, code, 'cpp')
    print('-------------------------test java----------------------')
    with open('test/1/Main.java', 'r') as f:
        code = f.read()
    main('/test_cases', manifest, code, 'java')
    print('-------------------------test kotlin----------------------')
    with open('test/1/main.kt', 'r') as f:
        code = f.read()
    main('/test_cases', manifest, code, 'kotlin')
    print('-------------------------test go----------------------')
    with open('test/1/main.go', 'r') as f:
        code = f.read()
    main('/test_cases', manifest, code, 'go')
