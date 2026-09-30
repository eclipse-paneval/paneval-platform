register_dataset = {"science_qa_dataset.py": "ScienceQaDataset"}

dataset = dict(
    type="ScienceQaDataset",
    ques_file="problems.json",
    data_root="/share/project/mmdataset/ScienceQA_DATA",
    prompt_template=dict(type="PromptTemplate"),
    name="science_qa",
)

evaluator = dict(type="BaseEvaluator")
