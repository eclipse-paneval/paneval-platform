register_dataset = {"seed_bench_dataset.py": "SeedBenchDataset"}

dataset = dict(
    type="SeedBenchDataset",
    anno_file="SEED-Bench.json",
    data_root="/share/project/mmdataset/SEED-Bench",
    prompt_template=dict(type="PromptTemplate"),
    name="seed_bench",
)

evaluator = dict(type="BaseEvaluator")
