import re
from typing import Dict, List, Optional
import math
import datasets

from math import sqrt, sin, cos, log, pi, factorial, exp, e
from latex2sympy2 import latex2sympy

E = 2.718

# taken from
# https://github.com/wellecks/lm-evaluation-harness/blob/master/lm_eval/tasks/minerva_math.py
def doc_to_text(doc: dict) -> str:
    return "Problem:" + "\n" + doc["problem"] + "\n\n" + "Solution:"


def process_docs(dataset: datasets.Dataset) -> datasets.Dataset:
    def _process_answer(doc: dict) -> list:
        if isinstance(doc['Answer'], bool):
            return [str(doc['Answer']), None]
        elif isinstance(doc['Answer'], (list, int, float)):
            return [str(doc['Answer']), doc['Answer']]
        else:
            return [str(doc['Answer']), None]
        
    def _process_doc(doc: dict) -> dict:
        out_doc = {
            "problem": doc["Question"],
            "answer": _process_answer(doc)
        }
        if getattr(doc, "few_shot", None) is not None:
            out_doc["few_shot"] = True
        return out_doc

    return dataset.map(_process_doc)


def list_fewshot_samples() -> list[dict]:
    return [
        {
            "problem": 'In a 10 Gigabit Ethernet network, the average size of a frame is 1500 bytes. If a burst of noise lasting 1ms interrupts the network, how many frames are lost?',
            "answer": 'First, calculate the data rate in bytes/s:\n\n10 Gigabit/s * (1 Byte / 8 bits) = 1.25 * 10^9 Bytes/s\n\nNext, calculate the data loss in bytes due to the noise:\n\n1 ms * 1.25 * 10^9 Bytes/s = 1.25 * 10^6 Bytes\n\nFinally, divide the data loss by the average frame size to get the number of frames lost:\n\n1.25 * 10^6 Bytes / 1500 Bytes/frame ≈ 833.33 frames\nThe answer is 833.33',
            "few_shot": "1",
        },
        {
            "problem": 'Given x = 0.157, what is the value of x \\times \\frac{\\prod_{n=1}^\\infty (1 - \\frac{x^2}{n^2 \\pi^2})}{\\sin(x)}?',
            "answer": "To evaluate the expression $x \\times \\frac{\\prod_{n=1}^{\\infty} (1 - \\frac{x^2}{n^2 \\pi^2})}{\\sin(x)}$ given x = 0.157, we first recognize that the product in the numerator is related to the sine function through the Euler's reflection formula for the sine function, which can be expressed as:\n\n$$\\sin(x) = x \\prod_{n=1}^{\\infty} \\left(1 - \\frac{x^2}{n^2 \\pi^2}\\right)$$\n\nTherefore, the given expression simplifies to: $x \\times \\frac{\\sin(x)}{\\sin(x)}$\n\nBecause sin(x) in the numerator and denominator cancels out, the expression simplifies further to just x.\n\nSo, given x = 0.157, the value of the expression is 0.157. This result is derived from the properties of the sine function and does not require computational evaluation.\nThe answer is 0.157",
            "few_shot": "1",
        },
        {
            "problem": 'Consider the basis C of \\mathbb{R}^2 consisting of vectors u_1 = [2, 4] and u_2 = [1, -1]. If y = [8, 12], find the C-coordinate vector of y.',
            "answer": "The goal is to express y as a linear combination of the basis vectors of C, i.e., $y = a\\cdot u_1 + b\\cdot u_2$, where a and b are the scalar coefficients that we want to find. These coefficients will form the C-coordinate vector of y, which we'll denote as $[a, b]_C$.\n\nGiven:\n- $u_1 = [2, 4]$,\n- $u_2 = [1, -1]$,\n- $y = [8, 12]$.\n\nWe need to solve the system of linear equations:\n2a + 1b = 8\n4a - 1b = 12\n\nLet's solve this system of equations to find a and b.\n\nThe solution to the system of equations is $a = \\frac{10}{3} and b = \\frac{4}{3}$. Therefore, the C-coordinate vector of y in the basis consisting of vectors u_1 = [2, 4] and u_2 = [1, -1] is $\\left[\\frac{10}{3}, \\frac{4}{3}\\right]_C$. \nLet's calculate the numerical value of $\\left[\x0crac{10}{3}, \x0crac{4}{3}\right]_C$ as [3.33, 1.33].\nThe answer is [3.33, 1.33]",
            "few_shot": "1",
        },
        {
            "problem": 'One can draw a simple, connected planar graph with 200 vertices and 397 edges. Is this statement Trur or False?',
            "answer": "To determine the answer, we can use Euler's formula for planar graphs, which states that for any finite, connected, planar graph, $V - E + F = 2$, where V is the number of vertices, E is the number of edges, and F is the number of faces.\n\nGiven the modified question, we have V = 200 vertices and E = 397 edges. We want to find if we can have a graph that satisfies these conditions, adhering to Euler's formula.\n\nFirst, let's rearrange Euler's formula to solve for F:  F = E - V + 2\n\nSubstituting the given values: F = 397 - 200 + 2,  F = 199\n\nThis means a graph with 200 vertices and 397 edges would have 199 faces. However, to determine the truth of this possibility, we should check if this graph doesn't violate any other planar graph constraints, particularly regarding the number of edges.\n\nFor a simple, connected planar graph, there's also a relationship between vertices, edges, and faces given by the inequality: $E \\leq 3V - 6$\n\nSubstituting V = 200 gives: $E \\leq 3*200 - 6 = 594$\n\nWith E = 397, the condition $E \\leq 594$ is satisfied, meaning it's theoretically possible in terms of the edge condition for a planar graph.\n\nTherefore, one can draw a simple, connected planar graph with 200 vertices and 397 edges, resulting in 199 faces, without violating the conditions for it to be planar according to both Euler's formula and the constraint on the maximum number of edges.\nThe answer is True",
            "few_shot": "1",
        },
        {
            "problem": 'Given a finite group G, and a collection of permutations H on a set. Then (a) there always exists H such that G is isomorphic to H; (b) for any H, G is isomorphic to H; (c) G can never be isomorphic to H; (d) none of the above. Which option is correct?',
            "answer": "This is based on Cayley's theorem, which states that every group G is isomorphic to a subgroup of the symmetric group acting on G. \nIn other words, for every finite group G, there exists a collection of permutations H (which in this context, can be thought of as the set of permutations representing the action of G on itself) such that G is isomorphic to H.\n\nTherefore, there always exists H such that G is isomorphic to H.\nThe answer is (a)",
            "few_shot": "1",
        }
    ]


def floatify(num: str):
    try:
        num = float(num)
        if num.is_integer():
            return round(num)
        else:
            return num
    except Exception:
        return None


def within_eps(pred: float, gt: float):
    eps = abs(gt) * 0.04
    if pred >= gt - eps and pred <= gt + eps:
        return True
    else:
        return False


def clean_units(pred_str: str):
    """Clean the units in the number."""
    def convert_pi_to_number(code_string):
        code_string = code_string.replace('\\pi', 'π')
        # Replace \pi or π not preceded by a digit or } with 3.14
        code_string = re.sub(r'(?<![\d}])\\?π', '3.14', code_string)
        # Replace instances where π is preceded by a digit but without a multiplication symbol, e.g., "3π" -> "3*3.14"
        code_string = re.sub(r'(\d)(\\?π)', r'\1*3.14', code_string)
        # Handle cases where π is within braces or followed by a multiplication symbol
        # This replaces "{π}" with "3.14" directly and "3*π" with "3*3.14"
        code_string = re.sub(r'\{(\\?π)\}', '3.14', code_string)
        code_string = re.sub(r'\*(\\?π)', '*3.14', code_string)
        return code_string

    pred_str = convert_pi_to_number(pred_str)
    pred_str = pred_str.replace('%', '/100')
    pred_str = pred_str.replace('$', '')
    pred_str = pred_str.replace('¥', '')
    pred_str = pred_str.replace('°C', '')
    pred_str = pred_str.replace(' C', '')
    pred_str = pred_str.replace('°', '')
    return pred_str


def number_it(num):
    if isinstance(num, (int, float)):
        return num

    num = clean_units(num)
    try:
        num = str(latex2sympy(num))
    except Exception:
        pass

    if floatify(num) is not None:
        return floatify(num)
    else:
        try:
            num = eval(num)
            if isinstance(num, list) or isinstance(num, tuple):
                num = num[0]
            if floatify(num) is not None:
                return floatify(num)
            else:
                return None
        except Exception:
            return None


def compare_two_numbers(p, gt):
    try:
        if math.isnan(p):
            return False
        if isinstance(gt, int):
            return round(p) == gt
        else:
            return within_eps(pred=p, gt=gt)
    except Exception:
        return False


def compare_two_list(pred, gt):
    if not isinstance(pred, list):
        return False
    elif len(pred) != len(gt):
        return False
    elif any([not isinstance(x, (int, float)) for x in pred]):
        return False
    else:
        pred = sorted(pred)
        gt = sorted(gt)
        return all([compare_two_numbers(p, g) for p, g in zip(pred, gt)])
    
def process_results(doc: dict, results: List[str]) -> Dict[str, int]:
    candidates = results[0]
    groundtruth = doc['answer']
    answer = answer_clean(['The answer is:', 'The answer is', 'the answer is'], candidates)
    import pdb
    
    if isinstance(groundtruth, str):
        groundtruth = [groundtruth]
    if compare_answer_with_groundtruth(answer, *groundtruth):
        retval = 1
    else:
        retval = 0
    # pdb.set_trace()
    results = {
        "exact_match": retval,
    }
    return results


def extract_theoremqa_answer(pred: str, answer_flag: bool = True):
    if any([option in pred.lower() for option in ['yes', 'true']]):
        pred = 'True'
    elif any([option in pred.lower() for option in ['no', 'false']]):
        pred = 'False'
    elif any([option in pred.lower() for option in ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']]):
        pass
    else:
        if answer_flag:
            # Extract the numbers out of the string
            pred = pred.split('=')[-1].strip()
            pred = clean_units(pred)
            try:
                tmp = str(latex2sympy(pred))
                pred = str(eval(tmp))
            except Exception:
                if re.match(r'-?[\d\.]+\s\D+$', pred):
                    pred = pred.split(' ')[0]
                elif re.match(r'-?[\d\.]+\s[^\s]+$', pred):
                    pred = pred.split(' ')[0]
        else:
            # desparate search over the last number
            preds = re.findall(r'-?\d*\.?\d+', pred)
            if(len(preds) >= 1):
                pred = preds[-1]
            else:
                pred = ''

    return pred


def answer_clean(direct_answer_trigger_for_fewshot: tuple, pred: str):
    pred = pred.strip('\n')

    # Determine if this is ICL, if so, use \n\n to split the first chunk.
    ICL = False
    for trigger in direct_answer_trigger_for_fewshot:
        if pred.count(trigger) > 1:
            ICL = True
    if ICL:
        pred = pred.split('\n\n')[0]

    # Split the trigger to find the answer.
    preds = re.split('|'.join(direct_answer_trigger_for_fewshot), pred)
    if len(preds) > 1:
        answer_flag = True
        pred = preds[-1]
    else:
        answer_flag = False

    pred = pred.strip('\n').rstrip('.').rstrip('/').strip(' ')

    pred = [extract_theoremqa_answer(pred, answer_flag)]

    # If there is no candidate in list, null is set.
    if len(pred) == 0:
        pred = ""
    else:
        if answer_flag:
            # choose the first element in list ...
            pred = pred[0]
        else:
            # choose the last e
            pred = pred[-1]

    # Remove the period at the end, again!
    pred = pred.rstrip('.').rstrip('/')

    return pred



def compare_answer_with_groundtruth(answer: str, groundtruth_str: str, groundtruth_num = None):
    if groundtruth_str.lower() in ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']:
        return groundtruth_str.lower() in answer.lower()
    elif answer.lower() == groundtruth_str.lower():
        return True
    elif groundtruth_num is not None:
        if isinstance(groundtruth_num, (int, float)):
            return compare_two_numbers(number_it(answer), groundtruth_num)
        else:
            if answer.startswith('(') and answer.endswith(')'):
                try:
                    answer = list(eval(answer))
                    answer = [number_it(a) for a in answer]
                except Exception as e:
                    return False
                return compare_two_list(answer, groundtruth_num)
            else:
                return False
    else:
        return False