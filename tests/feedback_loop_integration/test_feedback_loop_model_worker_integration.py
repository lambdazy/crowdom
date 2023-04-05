import datetime
from itertools import chain

import toloka.client as toloka

from crowdom import (
    base,
    classification,
    classification_loop,
    evaluation,
    feedback_loop,
    pool as pool_config,
    worker,
)
from crowdom.objects import Text
from crowdom.control import Control, RuleBuilder
from crowdom.duration import get_const_task_duration_function

from .stub import TolokaClientStub
from .data import (
    markup_task_mapping,
    check_task_mapping,
    pool_input_objects_model,
    markup_assignments_by_iterations_model_check,
    markup_assignments_by_iterations_model_markup,
    check_assignments_by_iterations_model_markup,
    markup_pool_id,
    check_pool_id,
    control_audios,
    markup_project,
    check_project,
    model_check,
    model_markup,
)


def test_integration_model_check():
    stub = TolokaClientStub(markup_assignments_by_iterations_model_check, [], markup_project, check_project)
    fb_loop = feedback_loop.FeedbackLoop(
        pool_input_objects=pool_input_objects_model,
        markup_task_mapping=markup_task_mapping,
        check_task_mapping=check_task_mapping,
        check_params=classification_loop.Params(
            aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
            control=Control(rules=[]),
            overlap=classification_loop.StaticOverlap(overlap=1),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        markup_params=feedback_loop.Params(
            control=Control(rules=RuleBuilder().add_static_reward(0.5).build()),
            assignment_check_sample=None,
            overlap=classification_loop.DynamicOverlap(min_overlap=1, max_overlap=2, confidence=0.6),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        client=stub,  # noqa
        lang='EN',
        model_check=model_check,
    )

    markup_pool_config = pool_config.MarkupConfig(
        project_id=markup_project.id,
        private_name=markup_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=40),
        real_tasks_count=6,
        control_params=fb_loop.markup_params.control,
    )
    check_pool_config = pool_config.ClassificationConfig(
        project_id=check_project.id,
        private_name=check_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=20),
        real_tasks_count=12,
        control_tasks_count=1,
        overlap=1,
        control_params=fb_loop.check_params.control,
    )

    markup_pool, check_pool = fb_loop.create_pools(control_audios, markup_pool_config, check_pool_config)

    fb_loop.loop(markup_pool.id, check_pool.id)

    object_results, worker_weights = fb_loop.get_results(markup_pool.id, check_pool.id)

    markup_assignment_0_accuracy = 4 / 6
    markup_assignment_1_accuracy = 2 / 6
    markup_assignment_2_accuracy = 4 / 6

    false, true = base.BinaryEvaluation(ok=False), base.BinaryEvaluation(ok=True)
    check_worker = worker.Human(toloka.Assignment(user_id='asr', id=''))
    markup_workers = [
        worker.Human(assignment=assignment) for assignment in chain(*markup_assignments_by_iterations_model_check)
    ]

    expected_results = [
        [
            feedback_loop.Solution(
                solution=(Text(text='семнадцать'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1,
                    worker_labels=[(true, check_worker)],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=1,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='нет не надо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1,
                    worker_labels=[(true, check_worker)],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=1,
            ),
            feedback_loop.Solution(
                solution=(Text(text='нет надо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0,
                    worker_labels=[(false, check_worker)],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=1,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='хорошо до свидания'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1,
                    worker_labels=[(true, check_worker)],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=1,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='нет'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1,
                    worker_labels=[(true, check_worker)],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=1,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='?'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0,
                    worker_labels=[(false, check_worker)],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=1,
            ),
            feedback_loop.Solution(
                solution=(Text(text='абонент'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0,
                    worker_labels=[(false, check_worker)],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=1,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='да я оплатил'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1,
                    worker_labels=[(true, check_worker)],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=1,
            ),
            feedback_loop.Solution(
                solution=(Text(text='я оплатил'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0,
                    worker_labels=[(false, check_worker)],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=1,
            ),
        ],
    ]
    assert object_results == expected_results

    expected_calls = [
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                            'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav')",
                        },
                        id=f'task {audio_index}',
                        pool_id='markup pool',
                    )
                    for audio_index in range(6)
                ],
            ),
        ),
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': 'https://storage.net/82.wav',
                            'output': 'алло',
                            'id': "Audio(url='https://storage.net/82.wav') Text(text='алло')",
                        },
                        known_solutions=[toloka.Task.KnownSolution(output_values={'ok': True}, correctness_weight=1)],
                        id='task 6',
                        infinite_overlap=True,
                        pool_id='check pool',
                    ),
                ],
            ),
        ),
        ('open_pool', ('markup pool',)),
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                            'output': f'{text}',
                            'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                        },
                        id=f'task {7 + i}',
                        pool_id='check pool',
                        unavailable_for=[f'markup-{user_id}'],
                    )
                    for i, (audio_index, text, user_id) in enumerate(
                        [
                            (1, 'нет надо', 0),
                            (2, 'хорошо до свидания', 0),
                            (0, 'семнадцать', 0),
                            (3, 'нет', 1),
                            (5, 'я оплатил', 1),
                            (4, 'абонент', 1),
                        ]
                    )
                ],
            ),
        ),
        (
            'patch_assignment',
            (
                'markup assignment 0',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
        (
            'patch_assignment',
            (
                'markup assignment 1',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED,
                    public_comment='Check the tasks with numbers: 2, 3. Learn more about tasks acceptance and filing '
                    'appeals in the project instructions.',
                ),
            ),
        ),
        ('patch_task_overlap_or_min', ('task 1', toloka.task.TaskOverlapPatch(overlap=2))),
        ('patch_task_overlap_or_min', ('task 5', toloka.task.TaskOverlapPatch(overlap=2))),
        ('patch_task_overlap_or_min', ('task 4', toloka.task.TaskOverlapPatch(overlap=2))),
        ('open_pool', ('markup pool',)),
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                            'output': f'{text}',
                            'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                        },
                        id=f'task {13 + i}',
                        pool_id='check pool',
                        unavailable_for=[f'markup-{user_id}'],
                    )
                    for i, (audio_index, text, user_id) in enumerate(
                        [
                            (4, '?', 2),
                            (1, 'нет не надо', 2),
                            (5, 'да я оплатил', 2),
                        ]
                    )
                ],
            ),
        ),
        (
            'patch_assignment',
            (
                'markup assignment 2',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
    ]
    assert stub.calls[1:2] + stub.calls[3:] == expected_calls  # skip pools creation


def test_integration_model_markup():
    stub = TolokaClientStub(
        markup_assignments_by_iterations_model_markup,
        check_assignments_by_iterations_model_markup,
        markup_project,
        check_project,
        has_model_markup=True,
    )
    fb_loop = feedback_loop.FeedbackLoop(
        pool_input_objects=pool_input_objects_model,
        markup_task_mapping=markup_task_mapping,
        check_task_mapping=check_task_mapping,
        check_params=classification_loop.Params(
            aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
            control=Control(rules=RuleBuilder().add_static_reward(0.5).build()),  # not used
            overlap=classification_loop.StaticOverlap(overlap=2),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        markup_params=feedback_loop.Params(
            control=Control(rules=RuleBuilder().add_static_reward(0.7).build()),
            assignment_check_sample=None,
            overlap=classification_loop.DynamicOverlap(min_overlap=1, max_overlap=2, confidence=0.7),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        client=stub,  # noqa
        lang='EN',
        model_markup=model_markup,
    )

    markup_pool_config = pool_config.MarkupConfig(
        project_id=markup_project.id,
        private_name=markup_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=40),
        real_tasks_count=3,
        control_params=fb_loop.markup_params.control,
    )
    check_pool_config = pool_config.ClassificationConfig(
        project_id=check_project.id,
        private_name=check_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=20),
        real_tasks_count=4,
        control_tasks_count=1,
        overlap=2,
        control_params=fb_loop.check_params.control,
    )

    markup_pool, check_pool = fb_loop.create_pools(control_audios, markup_pool_config, check_pool_config)

    fb_loop.loop(markup_pool.id, check_pool.id)

    object_results, worker_weights = fb_loop.get_results(markup_pool.id, check_pool.id)

    markup_assignment_model_accuracy = 2 / 6
    markup_assignment_0_accuracy = 1 / 3
    markup_assignment_1_accuracy = 1

    false, true = base.BinaryEvaluation(ok=False), base.BinaryEvaluation(ok=True)

    check_workers = [
        worker.Human(assignment=assignment) for assignment in chain(*check_assignments_by_iterations_model_markup)
    ]
    markup_model_worker = worker.Human(toloka.Assignment(user_id='asr', id=''))
    markup_workers = [
        worker.Human(assignment=assignment) for assignment in chain(*markup_assignments_by_iterations_model_markup)
    ]

    expected_results = [
        [
            feedback_loop.Solution(
                solution=(Text(text='семнадцать'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_model_worker,
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[0]), (true, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_model_accuracy,
                assignment_evaluation_recall=1.0,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='нет надо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 2,
                    worker_labels=[(true, check_workers[0]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=1.0,
            ),
            feedback_loop.Solution(
                solution=(Text(text='нет надо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_model_worker,
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 2,
                    worker_labels=[(true, check_workers[0]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_model_accuracy,
                assignment_evaluation_recall=1.0,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='хорошо до свидания'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_model_worker,
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[0]), (true, check_workers[1])],
                ),
                assignment_accuracy=markup_assignment_model_accuracy,
                assignment_evaluation_recall=1.0,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='ну нет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 2,
                    worker_labels=[(true, check_workers[3]), (false, check_workers[4])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=1.0,
            ),
            feedback_loop.Solution(
                solution=(Text(text='нет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_model_worker,
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 2,
                    worker_labels=[(false, check_workers[0]), (true, check_workers[1])],
                ),
                assignment_accuracy=markup_assignment_model_accuracy,
                assignment_evaluation_recall=1.0,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='абонент недоступен'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[3]), (true, check_workers[4])],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=1.0,
            ),
            feedback_loop.Solution(
                solution=(Text(text='абонент'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_model_worker,
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0,
                    worker_labels=[(false, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_model_accuracy,
                assignment_evaluation_recall=1.0,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='да я оплатил'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[3]), (true, check_workers[4])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=1.0,
            ),
            feedback_loop.Solution(
                solution=(Text(text='я оплатил'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_model_worker,
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 2,
                    worker_labels=[(true, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_model_accuracy,
                assignment_evaluation_recall=1.0,
            ),
        ],
    ]
    assert object_results == expected_results

    expected_calls = [
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                            'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav')",
                        },
                        id=f'task {audio_index}',
                        pool_id='markup pool',
                    )
                    for audio_index in range(6)
                ],
            ),
        ),
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': 'https://storage.net/82.wav',
                            'output': 'алло',
                            'id': "Audio(url='https://storage.net/82.wav') Text(text='алло')",
                        },
                        known_solutions=[toloka.Task.KnownSolution(output_values={'ok': True}, correctness_weight=1)],
                        id='task 6',
                        infinite_overlap=True,
                        pool_id='check pool',
                    ),
                ],
            ),
        ),
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                            'output': f'{text}',
                            'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                        },
                        id=f'task {7 + i}',
                        pool_id='check pool',
                        unavailable_for=['asr'],
                    )
                    for i, (audio_index, text) in enumerate(
                        [
                            (0, 'семнадцать'),
                            (1, 'нет надо'),
                            (2, 'хорошо до свидания'),
                            (3, 'нет'),
                            (4, 'абонент'),
                            (5, 'я оплатил'),
                        ]
                    )
                ],
            ),
        ),
        ('open_pool', ('check pool',)),
        (
            'patch_assignment',
            (
                'check assignment 0',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
        (
            'patch_assignment',
            (
                'check assignment 1',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
        (
            'patch_assignment',
            (
                'check assignment 2',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
        ('patch_task_overlap_or_min', ('task 1', toloka.task.TaskOverlapPatch(overlap=1))),
        ('patch_task_overlap_or_min', ('task 3', toloka.task.TaskOverlapPatch(overlap=1))),
        ('patch_task_overlap_or_min', ('task 4', toloka.task.TaskOverlapPatch(overlap=1))),
        ('patch_task_overlap_or_min', ('task 5', toloka.task.TaskOverlapPatch(overlap=1))),
        ('open_pool', ('markup pool',)),
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                            'output': f'{text}',
                            'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                        },
                        id=f'task {13 + i}',
                        pool_id='check pool',
                        unavailable_for=[f'markup-{user_id}'],
                    )
                    for i, (audio_index, text, user_id) in enumerate(
                        [
                            (3, 'ну нет', 0),
                            (5, 'да я оплатил', 0),
                            (4, 'абонент недоступен', 1),
                        ]
                    )
                ],
            ),
        ),
        ('open_pool', ('check pool',)),
        (
            'patch_assignment',
            (
                'check assignment 3',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
        (
            'patch_assignment',
            (
                'check assignment 4',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
        (
            'patch_assignment',
            (
                'markup assignment 0',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED,
                    public_comment='Check the tasks with numbers: 1, 2. Learn more about tasks acceptance and filing '
                    'appeals in the project instructions.',
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                'markup assignment 1',
                toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
            ),
        ),
    ]
    assert stub.calls[1:2] + stub.calls[3:] == expected_calls  # skip pools creation
