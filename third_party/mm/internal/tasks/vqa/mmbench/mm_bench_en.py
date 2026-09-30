register_evaluator = {"mmbench_evaluator.py": "MmbenchEvaluator"}

dataset = dict(
    type="VqaBaseDataset",
    anno_file="problems/problems.json",
    data_root="/share/project/mmdataset/mm_bench_parsed/en",
    prompt_template=dict(type="PromptTemplate"),
    name="mm_bench_en",
)

evaluator = dict(type="MmbenchEvaluator")
