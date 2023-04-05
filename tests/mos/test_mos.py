import datetime
from datetime import timedelta
from mock import patch
from pytest import fixture
from typing import List, Dict, Set

import toloka.client as toloka
import numpy as np

from crowdom import (
    base,
    classification,
    classification_loop,
    control,
    duration,
    mos,
    mapping,
    objects,
    task_spec as spec,
)

from .. import lib


class MOS(base.ScoreEvaluation):
    BAD = '1'
    POOR = '2'
    FAIR = '3'
    GOOD = '4'
    EXCELLENT = '5'


@fixture
def task_duration_hint() -> timedelta:
    return timedelta(seconds=9)


@fixture
def task_spec_en() -> spec.PreparedTaskSpec:
    lang = 'EN'
    function = base.ClassificationFunction(inputs=(objects.Audio,), cls=MOS)
    name = {'EN': 'Speech quality evaluation'}
    description = {'EN': 'Rate the quality of audio files on a scale of 1 to 5'}
    task_spec = base.TaskSpec(id='mos', function=function, name=name, description=description, instruction=description)
    return spec.PreparedTaskSpec(task_spec, lang)


@fixture
def params(task_duration_hint: timedelta) -> classification_loop.Params:
    return classification_loop.Params(
        overlap=classification_loop.StaticOverlap(3),
        aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
        control=control.Control(
            rules=control.RuleBuilder()
            .add_static_reward(0.5)
            .add_complex_speed_control([control.BlockTimePicker(0.1, '2d', True)])
            .build(),
        ),
        task_duration_function=duration.get_const_task_duration_function(task_duration_hint),
    )


@fixture
def default_solutions() -> Dict[str, List[MOS]]:
    return {
        'alice': [MOS('3'), MOS('4'), MOS('5')],
        'bob': [MOS('5'), MOS('4'), MOS('4')],
        'carl': [
            MOS('4'),
            MOS('3'),
            MOS('3'),
            MOS('3'),
        ],
        'dan': [MOS('5')],
        'evan': [MOS('1')],
        'filip': [MOS('4'), MOS('5'), MOS('5')],
        'hank': [MOS('4'), MOS('5')],
    }


def get_worker_assignment(
    worker: str,
    tasks: List[dict],
    solutions: Dict[str, List[MOS]],
    time_ratios: Dict[str, float],
    task_spec: spec.PreparedTaskSpec,
    task_duration_hint: timedelta,
) -> toloka.Assignment:
    created = datetime.datetime(2020, 11, 5, 10, 30)

    solutions_w = solutions[worker]
    solutions_i = np.random.choice(solutions_w, size=len(tasks))
    return toloka.Assignment(
        tasks=tasks,
        solutions=[task_spec.task_mapping.to_solution((solution,)) for solution in solutions_i],
        user_id=worker,
        created=created,
        submitted=created + task_duration_hint * len(tasks) * time_ratios[worker],
    )


def get_assignment_solutions(
    task_spec: spec.PreparedTaskSpec, solutions: Dict[str, List[MOS]], task_duration_hint: timedelta
):
    np.random.seed(0)
    audios = [objects.Audio(url=str(i)) for i in range(100)]
    tasks = [task_spec.task_mapping.to_task((audio,)) for audio in audios]
    workers = ['alice', 'bob', 'carl', 'dan', 'evan', 'filip']
    time_ratios = {'alice': 1.0, 'bob': 0.01, 'carl': 0.35, 'dan': 0.1, 'evan': 0.3, 'filip': 0.4, 'hank': 1.0}

    assignments = []
    for i in range(30):
        worker = workers[i % len(workers)]
        tasks_i = tasks[
            i * 3 : i * 3 + 10
        ]  # 10 tasks per assignment, and we use overlapping intervals to emulate overlap
        assignments.append(
            get_worker_assignment(worker, tasks_i, solutions, time_ratios, task_spec, task_duration_hint)
        )
    assignments.append(get_worker_assignment('hank', tasks[:1], solutions, time_ratios, task_spec, task_duration_hint))
    return mapping.get_assignments_solutions(assignments, task_spec.task_mapping, with_control_tasks=True)


@fixture
def default_assignment_solutions(
    task_spec_en: spec.PreparedTaskSpec,
    task_duration_hint: timedelta,
    default_solutions: Dict[str, List[MOS]],
) -> List[mapping.AssignmentSolutions]:
    return get_assignment_solutions(task_spec_en, default_solutions, task_duration_hint)


@fixture
def metadata_solutions() -> Dict[str, List[MOS]]:
    return {
        'alice': [MOS('4'), MOS('5'), MOS('5'), MOS('5')],
        'bob': [MOS('5'), MOS('4'), MOS('4')],
        'carl': [MOS('4'), MOS('5'), MOS('4')],
        'dan': [MOS('5'), MOS('4'), MOS('4')],
        'evan': [MOS('1')],
        'filip': [MOS('4'), MOS('5'), MOS('4'), MOS('3')],
        'hank': [MOS('4'), MOS('5'), MOS('3')],
    }


@fixture
def metadata_assignment_solutions(
    task_spec_en: spec.PreparedTaskSpec,
    task_duration_hint: timedelta,
    metadata_solutions: Dict[str, List[MOS]],
) -> List[mapping.AssignmentSolutions]:
    return get_assignment_solutions(task_spec_en, metadata_solutions, task_duration_hint)


@fixture
def mos_metadata(
    metadata_assignment_solutions: List[mapping.AssignmentSolutions],
) -> Dict[mapping.Objects, mos.ObjectsMetadata]:
    metadata = {}
    for _, solution in metadata_assignment_solutions:
        for inputs, _ in solution:
            index = int(inputs[0].url)
            metadata[inputs] = mos.ObjectsMetadata(item_id=str(index % 50), algorithm='1' if index < 50 else '2')

    return metadata


def get_ci(
    task_spec_en: spec.PreparedTaskSpec,
    params: classification_loop.Params,
    assignment_solutions: List[mapping.AssignmentSolutions],
    outlying_workers: Set[str],
    objects_metadata=None,
) -> Dict[str, mos.MOSCI]:
    loop = classification_loop.MOSLoop(
        lib.TolokaClientCallRecorderStub(),  # noqa
        task_spec_en.task_mapping,
        params,
        task_spec_en.lang,
        inputs_to_metadata=objects_metadata,
    )
    fast_workers = {'bob', 'dan'}
    bad_workers = {'evan', 'filip'}

    rejected_workers = fast_workers | bad_workers

    filtered_assignment_solutions = [
        (assignment, solution)
        for (assignment, solution) in assignment_solutions
        if assignment.user_id not in rejected_workers | outlying_workers
    ]
    strategy: mos.MOSEvaluationStrategy = loop.assignment_evaluation_strategy
    strategy.update(assignment_solutions)
    assert strategy.rejected_workers == rejected_workers
    assert strategy.final_assignments == filtered_assignment_solutions

    return strategy.final_assignment_set.get_algorithm_ci()


@patch('crowdom.mos.MIN_ASSIGNMENTS', 2)
@patch('crowdom.mos.STUB_CORRELATION', 0.8)
def test_mos(
    task_spec_en: spec.PreparedTaskSpec,
    params: classification_loop.Params,
    default_assignment_solutions: List[mapping.AssignmentSolutions],
):
    outlying_workers = {
        'hank',  # only 1 assignment
        'carl',  # low correlation
    }

    assert get_ci(task_spec_en, params, default_assignment_solutions, outlying_workers) == {
        'default': mos.MOSCI(mu=3.88, ci=1.67)
    }


def test_mos_with_metadata(
    task_spec_en: spec.PreparedTaskSpec,
    params: classification_loop.Params,
    metadata_assignment_solutions: List[mapping.AssignmentSolutions],
    mos_metadata: Dict[mapping.Objects, mos.ObjectsMetadata],
):
    assert get_ci(task_spec_en, params, metadata_assignment_solutions, {'hank'}, mos_metadata) == {
        '1': mos.MOSCI(mu=4.57, ci=0.59),
        '2': mos.MOSCI(mu=4.43, ci=0.71),
    }
