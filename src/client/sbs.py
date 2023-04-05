from random import choice
import threading
from typing import List, Tuple, Optional

import toloka.client as toloka

from .. import base, classification, mapping, task_spec as spec

from .launch import Params, launch
from .relaunch import get_swaps


# In a side-by-side comparison, client has two variants of objects, list of A's and list of B's, and want to know which
# variant, A or B, is better according to his criteria. By default, we place A's to the left, but to avoid workers bias
# of left/right variants of task UI or different exploits, we always randomly swap each pair of variants before creating
# tasks for workers. Overall process looks like:
# - take A's and B's (client input)
# - random swap, create L's and R's for tasks (remember swaps)
# - labeling
# - get results as L's and R's
# - convert L's and R's back to A's and B's (using remembered swaps)
# - return results for each pair in A's and B's terms (client output)
def launch_sbs(
    task_spec: spec.PreparedTaskSpec,
    params: Params,
    input_objects: List[mapping.Objects],
    control_objects: List[mapping.TaskSingleSolution],  # assisted by us
    client: toloka.TolokaClient,
    interactive: bool = False,
    name: Optional[str] = None,
) -> Tuple[classification.Results, Optional[classification.WorkerWeights]]:
    assert isinstance(task_spec.function, base.SbSFunction)

    # [hint, option_a, option_b] = [choice_a | choice_b]
    # swap: option_a <-> option_b, choice_a <-> choice_b

    h_cnt = len(task_spec.function.get_hints())
    i_cnt = len(task_spec.function.get_inputs())
    a_fr = h_cnt
    b_fr = h_cnt + i_cnt
    b_to = h_cnt + i_cnt * 2

    def swap_task(task: mapping.Objects) -> mapping.Objects:
        result = list(task)
        result[a_fr:b_fr], result[b_fr:b_to] = result[b_fr:b_to], result[a_fr:b_fr]
        return tuple(result)

    def swap_task_solution(task_solution: mapping.TaskSingleSolution) -> mapping.TaskSingleSolution:
        task, solution = task_solution
        return swap_task(task), (solution[0].swap(),) + solution[1:]

    input_objects_swapped = []
    swaps = get_swaps(name, input_objects)
    for swap, task_input_objects in zip(swaps, input_objects):
        swaps.append(swap)
        if swap:
            task_input_objects = swap_task(task_input_objects)
        input_objects_swapped.append(task_input_objects)

    control_objects_swapped = []
    for control_object in control_objects:
        swap = choice((True, False))
        if swap:
            control_object = swap_task_solution(control_object)
        control_objects_swapped.append(control_object)

    results_swapped, worker_weights = launch(
        task_spec=task_spec,
        params=params,
        input_objects=input_objects_swapped,
        control_objects=control_objects_swapped,
        client=client,
        interactive=interactive,
        name=name,
    )

    results = []
    for (labels_probas, worker_labels), swap in zip(results_swapped, swaps):
        assert labels_probas is not None
        if swap:
            labels_probas = {label.swap(): proba for label, proba in labels_probas.items()}
            worker_labels = [(label.swap(), worker) for label, worker in worker_labels]
        results.append((labels_probas, worker_labels))
    return results, worker_weights
