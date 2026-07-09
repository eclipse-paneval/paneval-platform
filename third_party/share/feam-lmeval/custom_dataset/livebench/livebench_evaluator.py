from concurrent.futures import ThreadPoolExecutor
import nltk

# todo: find a better solution than all these imports.
from lm_eval.tasks.livebench.process_results.data_analysis.tablereformat.utils import table_process_results
from lm_eval.tasks.livebench.process_results.data_analysis.cta.utils import cta_process_results
from lm_eval.tasks.livebench.process_results.data_analysis.tablejoin.utils import joinmap_process_results
from lm_eval.tasks.livebench.process_results.reasoning.web_of_lies_v2.utils import web_of_lies_process_results
from lm_eval.tasks.livebench.process_results.reasoning.house_traversal.utils import house_traversal_process_results
from lm_eval.tasks.livebench.process_results.reasoning.zebra_puzzle.utils import zebra_puzzle_process_results
from lm_eval.tasks.livebench.process_results.reasoning.spatial.utils import spatial_process_results
from lm_eval.tasks.livebench.process_results.math.math_competitions.utils import mathcontest_process_results,aime_process_results 
from lm_eval.tasks.livebench.process_results.math.olympiad.utils import proof_rearrangement_process_results
from lm_eval.tasks.livebench.process_results.math.AMPS_Hard.utils import amps_hard_process_results 
from lm_eval.tasks.livebench.process_results.writing.plot_unscrambling.utils import plot_unscrambling_process_results
from lm_eval.tasks.livebench.process_results.writing.typos.utils import typos_process_results
from lm_eval.tasks.livebench.process_results.writing.connections.utils import connections_process_results
from lm_eval.tasks.livebench.process_results.coding.utils import LCB_generation_process_results
from lm_eval.tasks.livebench.process_results.instruction_following.utils import instruction_following_process_results

import pdb


def play_a_match_gt(question, answer):
    # pdb.set_trace()
    coding_test_case_tasks = ["coding_completion","LCB_generation"]
    if "ground_truth" not in question and "reference" not in question and question["task"] not in coding_test_case_tasks and question["category"] != "instruction_following":
        raise ValueError("Questions must have ground_truth to run gen_ground_truth_judgment.")

    task = question["task"]
    task_or_subtask = question["subtask"] if "subtask" in question.keys() else question["task"]
    question_text = question['turns'][0]
    ground_truth = question.get("ground_truth", None)
    llm_answer = answer['choices'][0]['turns'][0]
    score = 0
    category = None

    # todo: find a better solution than a long if statement.
    splits = task_or_subtask.split('_')
    if splits[0] in ["amc", "smc"] or (len(splits) > 1 and splits[1] == "amc"):
        score = mathcontest_process_results(ground_truth, llm_answer, question_text)
        category = "math"
    elif splits[0] == "aime":
        score = aime_process_results(ground_truth, llm_answer)
        category = "math"
    elif splits[0] in ["imo", "usamo"]:
        score = proof_rearrangement_process_results(ground_truth, llm_answer, edit_distance=True)
        category = "math"
    elif task_or_subtask == "cta":
        score = cta_process_results(ground_truth, llm_answer)
        category = "data_analysis"
    elif task_or_subtask == "tablereformat":
        score = table_process_results(question_text, ground_truth, llm_answer)
        category = "data_analysis"
    elif task_or_subtask == "tablejoin":
        score = joinmap_process_results(question_text, ground_truth, llm_answer)
        category = "data_analysis"
    elif "amps_hard" in task_or_subtask:
        score = amps_hard_process_results(ground_truth, llm_answer)
        category = "math"
    elif task_or_subtask == "web_of_lies_v2":
        score = web_of_lies_process_results(ground_truth, llm_answer)
        category = "reasoning"
    elif task_or_subtask == "house_traversal":
        score = house_traversal_process_results(ground_truth, llm_answer)
        category = "reasoning"
    elif task_or_subtask == "zebra_puzzle":
        score = zebra_puzzle_process_results(ground_truth, llm_answer)
        category = "reasoning"
    elif task_or_subtask == "spatial":
        score = spatial_process_results(ground_truth, llm_answer)
        category = "reasoning"
    elif task_or_subtask == 'typos':
        score = typos_process_results(ground_truth, llm_answer)
        category = "language"
    elif task_or_subtask == "connections":
        score = connections_process_results(ground_truth, llm_answer)
        category = "language"
    elif task_or_subtask == "plot_unscrambling":
        score = plot_unscrambling_process_results(ground_truth, llm_answer)
        category = "language"
    elif task_or_subtask in coding_test_case_tasks:
        # use entire question object, because there are test cases inside.
        score = LCB_generation_process_results(question, llm_answer)
        category = "coding"
    else:
        raise NotImplementedError(f"This task ({task_or_subtask}) has not been implemented yet.")

    if not category:
        raise NotImplementedError(f"A category must be assigned to each task")
    
    result = {
        "task": task,
        "score": score,
        "category": category,
    }
    if "subtask" in question.keys():
        result["subtask"] = question["subtask"]

    return score




def gen_judgment(question, model_answer, subset_name, task, model_id):

    if "instruction_following" in subset_name:
        # nltk.download('punkt')

        if isinstance(question, dict):
            questions = [question]
        if isinstance(model_answer, dict):
            model_answers = [model_answer]

        scores = instruction_following_process_results(questions, model_answers, task, model_id)
        
        if len(scores) != 1:
            raise ValueError("return more than 1 item !!!")
        
        return scores[0]['score']
       
    else:
        return play_a_match_gt(question, model_answer)
