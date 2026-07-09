from functools import partial
import datasets
import ast
from lm_eval.tasks.musr_generative.tree import LogicTree
from lm_eval.tasks.musr_generative.icl import murder_mystery_solved_ex, object_placements_solved_ex, team_allocation_solved_ex

ablations = {
    'regular': {
        'prompt': 'regular',
        'self_consistency_n': None,
        'use_example': False
    },
    'cot': {
        'prompt': 'cot',
        'self_consistency_n': None,
        'use_example': False
    },
    'cot+': {
        'prompt': 'cot+',
        'self_consistency_n': None,
        'use_example': False
    },
    'cot+ 1-shot': {
        'prompt': 'cot+',
        'self_consistency_n': 1,
        'use_example': True
    },
    'cot+ s.c.': {
        'prompt': 'cot+',
        'self_consistency_n': 3,
        'use_example': False
    },
    'cot+ s.c. 1-shot': {
        'prompt': 'cot+',
        'self_consistency_n': 3,
        'use_example': True
    }
}

puzzles = {
    'murder_mysteries': {
        'name': 'murder_mysteries',
        'ex': murder_mystery_solved_ex,
        'hint': '''
            Before selecting a choice, explain your reasoning step by step. The murderer 
            needs to have a means (access to weapon), motive (reason to kill the victim), 
            and opportunity (access to crime scene) in order to have killed the victim. 
            Innocent suspects may have two of these proven, but not all three. An innocent 
            suspect may be suspicious for some other reason, but they will not have all of 
            motive, means, and opportunity established.

            If you believe that both suspects have motive, means, and opportunity, you should 
            make an educated guess pick the one for whom these are best established. If you 
            believe that neither suspect has all three established, then choose the suspect 
            where these are most clearly established.
        '''
    },
    
    'object_placements': {
        'name': 'object_placements',
        'ex': object_placements_solved_ex,
        'skip_ablated': True,
        'ablation_depth_modifier': 2,
        'hint': '''
            Based on this story, we want to identify where someone believes that a certain 
            object is at the end of the story. In order to do that, you need to read the 
            story and keep track of where they think the object is at each point. When an 
            object is moved, the person may observe its new location if they saw it move.

            To see where an object ends up, they must be able to see the location that it 
            moves to and not be too distracted by what they are doing. If they do not 
            observe the object moving, then they will still believe it to be in the last 
            location where they observed it.
        ''',
        'hint_before_question': True
    },
    
    'team_allocation': {
        'name': 'team_allocation',
        'ex': team_allocation_solved_ex,
        'hint': '''
            The story should allow you to determine how good each person is at a skill. 
            Roughly, each person is either great, acceptable, or bad at a task. We want 
            to find an optimal assignment of people to tasks that uses their skills as 
            well as possible. In addition, one task will have to have two people assigned 
            to it. The effectiveness of their teamwork (great team, acceptable team, or 
            bad team) also impacts the overall quality of the assignment.

            When two people need to work on a task and one is bad at it, they don't 
            necessarily benefit from the other person being good, unless they work well 
            together.

            With different strengths, weaknesses, and interpersonal dynamics at play, you 
            should allocate your team to find the single assignment to ensure that the 
            tasks overall are completed as effectively as possible.
        '''
    }
}

def process_docs(dataset: datasets.Dataset, subject: str) -> datasets.Dataset:
    def _process_doc(doc: dict) -> dict:
        
        ablation = ablations['regular']
        dataset_info = puzzles[subject]
        prompt_data = process_example(doc['narrative'], doc['question'], doc['choices'], ablation, dataset_info)
        out_doc = {
            "prompt": prompt_data,
            "choices": doc['choices'],
            "answer_index": doc['answer_index'],
            "answer_choice": doc['answer_choice']
        }
        return out_doc

    return dataset.map(_process_doc)

process_team_allocation = partial(process_docs, subject="team_allocation")
process_object_placements = partial(process_docs, subject="object_placements")
process_murder_mysteries = partial(process_docs, subject="murder_mysteries")

def process_example(context, question, choices, ablation_info, dataset_info):

    # Format choices
    choices = ast.literal_eval(choices)
    choices = "\n".join([f'{idx} - {x}' for idx, x in enumerate(choices)])
    
    # Get example string if needed
    ex_str = ''
    if ablation_info.get('use_example') and dataset_info.get('ex'):
        ex_str = ('Here is an example of solving the task:\n\n' + 
                 dataset_info.get('ex') + 
                 '\n\nThis is the end of the example. The real task is below.\n\n---\n\n')
    
    # Generate prompt based on style
    prompt_style = ablation_info.get('prompt')
    
    if prompt_style == 'regular':
        prompt = (f'{ex_str}{context}\n\n{question}\n\n'
                 f'Pick one of the following choices:\n{choices}\n\n'
                 f'You must pick one option. Finally, the last thing you generate should be '
                 f'"ANSWER: (your answer here, include the choice number)"')
    
    elif prompt_style == 'cot':
        prompt = (f'{ex_str}{context}\n\n{question}\n\n'
                 f'Pick one of the following choices:\n{choices}\n\n'
                 f'You must pick one option. Explain your reasoning step by step before you answer. '
                 f'Finally, the last thing you generate should be '
                 f'"ANSWER: (your answer here, include the choice number)"')
    
    elif prompt_style == 'cot+':
        if dataset_info.get("hint_before_question"):
            prompt = (f'{ex_str}{context}\n\n{dataset_info["hint"]}\n\n'
                     f'{question}\n\n'
                     f'Pick one of the following choices:\n{choices}\n\n'
                     f'You must pick one option. Explain your reasoning step by step before you answer. '
                     f'Finally, the last thing you generate should be '
                     f'"ANSWER: (your answer here, including the choice number)"')
        else:
            prompt = (f'{ex_str}{context}\n\n{question}\n\n'
                     f'Pick one of the following choices:\n{choices}\n\n'
                     f'You must pick one option. {dataset_info["hint"]} '
                     f'Explain your reasoning step by step before you answer. '
                     f'Finally, the last thing you generate should be '
                     f'"ANSWER: (your answer here, including the choice number)"')
    
    else:
        if len(question["intermediate_trees"]) == 0 or dataset_info.get('skip_ablated'):
            return None
            
        prompt = f'{ex_str}Answer the following questions given the list of facts per answer choice.\n\n'
        for c, t in zip(choices.split('\n'), question['intermediate_trees']):
            facts = list(set([x.value for x in LogicTree.from_json(t).get_facts(
                include_cs=ablation_info.get('include_cs', False),
                include_deductions_past_level=-1,
                no_facts_after_depth=ablation_info.get('no_facts_after_depth', 3) + 
                                   dataset_info.get('ablation_depth_modifier', 0))]))
            
            if dataset_info.get('allow_sorted_facts', True):
                facts = sorted(facts)
                
            facts_str = "\n".join([f'- {x}' for x in facts])
            prompt += f'Facts for Choice {c}:\n{facts_str}\n\n'
            
        prompt += (f'Given the list of facts per answer choice answer the following question\n\n'
                  f'{question}\n\nPick one of the following choices:\n{choices}\n\n'
                  f'You must pick on option. After you have found the answer, '
                  f'say it in this format "ANSWER: (your answer here, include the choice number)"')
    
    
    return prompt



