from ddlcw import Runner
from ddlcw.languages import c_lang_config


def main(test_case_dir, manifest, code):
    runner = Runner(test_case_dir, manifest, 1, 32, code, c_lang_config)
    print(runner.compile())
    print(runner.run())


if __name__ == '__main__':
    manifest = {
        "hash": "1892378192372127389137",
        'test_cases': [{'in': '1.in', 'out': '1.out'}, {'in': '2.in', 'out': '2.out'}],
        'spj': False,
        'spj_code': ''
    }
    with open('./1/test.c', 'r') as f:
        code = f.read()
    main('./1', manifest, code)
