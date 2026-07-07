import os

def test_qwen2_7b_weight():
    os.environ['EVALUATION_MODEL_NAME'] = 'Qwen2-7B'
    os.environ['REMOTE_API'] = 'hf://Qwen/Qwen2-7B'
    _run()

def test_qwen2_7b_api():
    os.environ['EVALUATION_MODEL_NAME'] = 'Qwen2-7B'
    os.environ['REMOTE_API'] = 'http://127.0.0.1:8000/v1/'
    _run()


def _run():
    from feam.models import Options
    from feam.runner import run
    from feam_opencompass.code import CodeScenario

    opts = Options(
        model=os.environ['EVALUATION_MODEL_NAME'],
        server_url=os.environ['REMOTE_API'],
        extras={}
    )
    s = CodeScenario(opts=opts)
    run(s, threads_num=1)
