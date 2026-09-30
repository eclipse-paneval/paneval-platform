
config = dict(
    dataset_path="nyu-visionx/CV-Bench",
    split="test",
    processed_dataset_path="CV-Bench",
    processor="process.py",
)

dataset = dict(
    type="VqaBaseDataset",
    prompt_template=dict(type="PromptTemplate"),
    config=config,
    data_root="/share/projset/mmdataset/robust/uap/CV-Bench/test",
    name="cv_bench_test_uap",
)

evaluator = dict(type="BaseEvaluator", eval_func="evaluate.py")
