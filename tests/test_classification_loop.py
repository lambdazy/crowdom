import datetime
import itertools
from typing import List, Union, Iterable, Dict, Tuple

from pytest import approx
import toloka.client as toloka

from crowdom import (
    classification,
    classification_loop,
    control,
    duration,
    evaluation,
    mapping,
    pool as pool_config,
    worker,
)
from crowdom.objects import Audio, Image, Text
from . import lib


def test_loop_e2e():
    assignment_start = datetime.datetime(year=2020, month=10, day=5, hour=13, minute=15)

    project = toloka.Project(
        id='project',
        task_spec=toloka.project.TaskSpec(
            input_spec=lib.image_classification_mapping.to_toloka_input_spec(),
            output_spec=lib.image_classification_mapping.to_toloka_output_spec(),
        ),
    )

    class TolokaClientStub(lib.TolokaClientIntegrationStub):
        assignments_by_iterations: List[List[toloka.Assignment]]
        assignments_requests: int
        id_to_assignment: Dict[str, toloka.Assignment]

        def __init__(self, assignments_by_iterations: List[List[toloka.Assignment]]):
            self.assignments_by_iterations = assignments_by_iterations
            self.assignments_requests = 0
            super(TolokaClientStub, self).__init__(list(itertools.chain(*assignments_by_iterations)), [project])

        # Emulation of task execution by workers. The logic of this method strongly depends on the current
        # implementation of classification loop.
        def get_assignments(
            self,
            status: Union[toloka.Assignment.Status, List[toloka.Assignment.Status]],
            pool_id: str,
        ) -> List[toloka.Assignment]:
            if not isinstance(status, list):
                status = [status]
            if status == [toloka.Assignment.SUBMITTED]:
                # Each loop iteration contains 3 API requests to assignments.
                loop_iteration = self.assignments_requests // 3
                assignments = self.assignments_by_iterations[loop_iteration]
            else:
                assignments = [
                    assignment for assignment in self.id_to_assignment.values() if assignment.status in status
                ]
            self.assignments_requests += 1
            return assignments

    overlap = 2

    task_duration_hint = datetime.timedelta(seconds=10)
    control_tasks_count = 2
    real_tasks_count = 2
    ratio_rand, ratio_poor = 0.1, 0.3

    control_params = control.Control(
        rules=control.RuleBuilder()
        .add_static_reward(threshold=0.5)
        .add_speed_control(ratio_rand, ratio_poor)
        .add_control_task_control(control_tasks_count, 1, 2)
        .build()
    )

    pool_id = 'fake pool'
    pool_cfg = pool_config.ClassificationConfig(
        project_id=project.id,
        private_name=pool_id,
        reward_per_assignment=0.01,
        task_duration_hint=task_duration_hint,
        real_tasks_count=real_tasks_count,
        control_tasks_count=control_tasks_count,
        overlap=overlap,
        control_params=control_params,
    )

    dog, cat, crow = lib.dog, lib.cat, lib.crow
    images = [Image(url=f'https://storage.net/{i}.jpg') for i in range(6)]
    control_images = [(Image(url=f'https://storage.net/{i}_control.jpg'), cat if i % 2 == 0 else dog) for i in range(4)]
    # 2 real tasks, 2 control tasks, 1/2 correct control tasks for accept
    # static overlap 2
    assignments = [
        # iteration 0
        [
            lib.create_classification_assignment(
                image_class_pairs,
                control_images,
                user_id=user_id,
                duration=datetime.timedelta(seconds=duration),
                assignment_start=assignment_start,
                pool_id=pool_id,
            )[0]
            for image_class_pairs, user_id, duration in [
                #   john  [(0.jpg cat) (1_control.jpg cat [bad]) (3.jpg cat) (2_control.jpg cat [ok])]  ACCEPTED
                (
                    [(images[0], cat), (control_images[1][0], cat), (images[3], cat), (control_images[2][0], cat)],
                    'john',
                    35,
                ),
                #   bob   [(0_control.jpg dog [bad]) (2.jpg cat) (1.jpg dog) (2_control.jpg dog [bad])] REJECTED
                (
                    [(control_images[0][0], dog), (images[2], cat), (images[1], dog), (control_images[2][0], dog)],
                    'bob',
                    31,
                ),
                #   mary  [(5.jpg cat) (4.jpg dog) (1_control.jpg cat [bad]) (3_control.jpg cat [bad])] REJECTED
                (
                    [(images[5], cat), (images[4], dog), (control_images[1][0], cat), (control_images[3][0], cat)],
                    'mary',
                    39,
                ),
                #   bob   [(4.jpg dog) (3_control.jpg cat [bad]) (1_control.jpg cat [bad]) (0.jpg cat)] REJECTED
                (
                    [(images[4], dog), (control_images[3][0], cat), (control_images[1][0], cat), (images[0], cat)],
                    'bob',
                    20,
                ),
                #   alice [(2.jpg dog) (3.jpg cat) (2_control.jpg cat [ok]) (0_control.jpg cat [ok])]   ACCEPTED
                (
                    [(images[2], dog), (images[3], cat), (control_images[2][0], cat), (control_images[0][0], cat)],
                    'alice',
                    22,
                ),
                #   john  [(2_control.jpg dog [ok]) (5.jpg dog) (1.jpg dog) (0_control.jpg dog [bad])]
                #   control tasks OK (1/2), but REJECTED BY PRIOR
                (
                    [(control_images[2][0], cat), (images[5], dog), (images[1], dog), (control_images[0][0], dog)],
                    'john',
                    3,
                ),
            ]
        ],
        # result (BEFORE -> SUBMITTED -> ACCEPTED -> RESULT):
        #   0.jpg () -> (cat|john, cat|bob) -> (cat|john), 0.5 conf
        #   1.jpg () -> (dog|bob, dog|john) -> ()
        #   2.jpg () -> (cat|bob, dog|alice) -> (dog|alice), 0.83 conf, but only one answer
        #   3.jpg () -> (cat|john, cat|alice) -> (cat|john, cat|alice), 0.90 conf
        #   4.jpg () -> (dog|mary, dog|bob) -> ()
        #   5.jpg () -> (cat|mary, dog|john) -> ()
        #
        #   mary, bob and john are blocked now
        #
        # iteration 1
        [
            lib.create_classification_assignment(
                image_class_pairs,
                control_images,
                user_id=user_id,
                duration=datetime.timedelta(seconds=duration),
                assignment_start=assignment_start,
                pool_id=pool_id,
            )[0]
            for image_class_pairs, user_id, duration in [
                #   martha  [(0_control.jpg dog [ok]) (5.jpg cat) (4.jpg dog) (2_control.jpg dog [ok])]
                #   control tasks OK (2/2), but REJECTED BY PRIOR
                (
                    [(control_images[0][0], cat), (images[5], cat), (images[4], dog), (control_images[2][0], cat)],
                    'martha',
                    2,
                ),
                #   fedor [(1.jpg dog) (5.jpg cat) (1_control.jpg dog [ok]) (2_control.jpg cat [ok])]  ACCEPTED, POOR TIME
                (
                    [(images[1], dog), (images[5], cat), (control_images[1][0], dog), (control_images[2][0], cat)],
                    'fedor',
                    10,
                ),
                #   alice [(4.jpg dog) (2_control.jpg dog [bad]) (1.jpg cat) (1_control.jpg cat [bad])] REJECTED
                (
                    [(images[4], dog), (control_images[2][0], dog), (images[1], cat), (control_images[1][0], cat)],
                    'alice',
                    39,
                ),
                #   paul   [(0_control.jpg cat [ok]) (3_control.jpg cat [bad]) (2.jpg cat) (0.jpg cat)]  ACCEPTED
                (
                    [(control_images[0][0], cat), (control_images[3][0], cat), (images[2], cat), (images[0], cat)],
                    'paul',
                    30,
                ),
            ]
        ],
        # result (BEFORE -> SUBMITTED -> ACCEPTED -> RESULT):
        #   0.jpg (cat|john) -> (cat|paul) -> (cat|paul) -> (cat|john, cat|paul), 0.66 conf
        #   1.jpg () -> (dog|fedor, cat|alice) -> (dog|fedor) -> (dog|fedor), 0.83 conf, but only one answer
        #   2.jpg (dog|alice) -> (cat|paul) -> (cat|paul) -> (dog|alice, cat|paul), 0.4 conf
        #   3.jpg (cat|john, cat|alice) -> () -> () -> (cat|john, cat|alice), 0.66 conf, dropped from 0.9, now uncertain
        #   4.jpg () -> (dog|martha, dog|alice) -> () -> ()
        #   5.jpg () -> (cat|martha, cat|fedor) -> (cat|fedor) -> (cat|fedor), 0.83 conf, but only one answer
        #
        #   martha, alice and fedor are blocked now
        #
        # iteration 2, duration=40
        [
            lib.create_classification_assignment(
                image_class_pairs, control_images, user_id=user_id, assignment_start=assignment_start, pool_id=pool_id
            )[0]
            for image_class_pairs, user_id in [
                #   paul  [(1_control.jpg dog [ok]) (1.jpg dog) (4.jpg cat) (2_control.jpg cat [ok])]  ACCEPTED
                (
                    [(control_images[1][0], dog), (images[1], dog), (images[4], cat), (control_images[2][0], cat)],
                    'paul',
                ),
                #   ivan  [(0_control.jpg dog [bad]) (2_control.jpg cat [ok]) (4.jpg dog) (2.jpg cat)] ACCEPTED
                (
                    [(control_images[0][0], dog), (control_images[2][0], cat), (images[4], dog), (images[2], cat)],
                    'ivan',
                ),
                #   paul  [(3.jpg dog) (5.jpg cat) (0_control.jpg cat [ok]) (3_control.jpg dog [ok])]  ACCEPTED
                (
                    [(images[3], dog), (images[5], dog), (control_images[0][0], cat), (control_images[3][0], dog)],
                    'paul',
                ),
                # incomplete assignment (we ran out of regular tasks)
                #   tom  [(1_control.jpg cat [bad]) (0.jpg cat) (3_control.jpg dog [ok])] ACCEPTED
                ([(control_images[1][0], cat), (images[0], cat), (control_images[3][0], dog)], 'tom'),
            ]
        ],
        # result (BEFORE -> SUBMITTED -> ACCEPTED -> RESULT):
        #   0.jpg (cat|john, cat|bob) -> (cat|tom) -> (cat|tom) -> (cat|john, cat|bob, cat|tom), 0.93 conf
        #   1.jpg (dog|fedor) -> (dog|paul) -> (dog|paul) -> (dog|fedor, dog|paul), 0.97 conf
        #   2.jpg (dog|alice, cat|paul) -> (cat|ivan) -> (cat|ivan) -> (dog|alice, cat|paul, cat|ivan), 0.83 conf
        #   3.jpg (cat|john, cat|alice) -> (dog|paul) -> (dog|paul) -> (cat|john, cat|alice, dog|paul), 0.59 conf
        #   4.jpg () -> (cat|paul, dog|ivan) -> (cat|paul, dog|ivan) -> (cat|paul, dog|ivan), 0.70 conf
        #   5.jpg (cat|fedor) -> (dog|paul) -> (dog|paul) -> (cat|fedor, dog|paul), 0.54 conf
        #
        #   tom is now blocked, because he did only 1 / 2 control correctly
        #   but this is a minor offence with short block time, and we assume it has passed between the iterations
        #
        # iteration 3, duration=40
        [
            lib.create_classification_assignment(
                image_class_pairs, control_images, user_id=user_id, assignment_start=assignment_start, pool_id=pool_id
            )[0]
            for image_class_pairs, user_id in [
                #   tom  [(2_control.jpg cat [ok]) (4.jpg cat) (3.jpg crow) (0_control.jpg crow [bad])] ACCEPTED
                (
                    [(control_images[2][0], cat), (images[4], cat), (images[3], crow), (control_images[0][0], crow)],
                    'tom',
                ),
                #   dylan  [(5.jpg crow) (0_control.jpg cat [ok]) (3_control.jpg dog [ok])]  ACCEPTED
                ([(images[5], crow), (control_images[0][0], cat), (control_images[3][0], dog)], 'dylan'),
            ]
        ],
        # result (BEFORE -> SUBMITTED -> ACCEPTED -> RESULT):
        #   0.jpg (cat|john, cat|bob, cat|tom) -> () -> () -> (cat|john, cat|bob, cat|tom), 0.93 conf
        #   1.jpg (dog|fedor, dog|paul) -> () -> () -> (dog|fedor, dog|paul), 0.97 conf
        #   2.jpg (dog|alice, cat|paul, cat|ivan) -> () -> () -> (dog|alice, cat|paul, cat|ivan), 0.83 conf
        #   3.jpg (cat|john, cat|alice, dog|paul) -> (crow|tom) -> (crow|tom) ->
        #                               (cat|john, cat|alice, dog|paul, crow|tom), 0.55 conf, but 4 answers already
        #   4.jpg (cat|paul, dog|ivan) -> (cat|tom) -> (cat|tom) -> (cat|paul, dog|ivan, cat|tom), 0.83 conf
        #   5.jpg (cat|fedor, dog|paul) -> (crow|dylan) -> (crow|dylan) -> (cat|fedor, dog|paul, crow|dylan), 0.36 conf
        #
        #
        #   tom is blocked now for 1 / 2 control tasks done correctly one more time
        #
        # iteration 4, duration=40
        [
            lib.create_classification_assignment(
                image_class_pairs,
                control_images,
                user_id=user_id,
                duration=datetime.timedelta(seconds=duration),
                assignment_start=assignment_start,
                pool_id=pool_id,
            )[0]
            for image_class_pairs, user_id, duration in [
                # assignment incompleteness is considered by prior filter, not rejected, but restricted
                #   theresa  [(2_control.jpg cat [ok]) (5.jpg dog) (1_control.jpg dog [ok])]  ACCEPTED
                ([(control_images[2][0], cat), (images[5], crow), (control_images[1][0], dog)], 'theresa', 4)
            ]
        ],
        # result (BEFORE -> SUBMITTED -> ACCEPTED -> RESULT):
        #   0.jpg (cat|john, cat|bob, cat|tom) -> () -> () -> (cat|john, cat|bob, cat|tom), 0.93 conf
        #   1.jpg (dog|fedor, dog|paul) -> () -> () -> (dog|fedor, dog|paul), 0.97 conf
        #   2.jpg (dog|alice, cat|paul, cat|ivan) -> () -> () -> (dog|alice, cat|paul, cat|ivan), 0.83 conf
        #   3.jpg (cat|john, cat|alice, dog|paul, crow|tom) -> () -> () ->
        #                               (cat|john, cat|alice, dog|paul, crow|tom), 0.55 conf, but 4 answers already
        #   4.jpg (cat|paul, dog|ivan, cat|tom) -> () -> () -> (cat|paul, dog|ivan, cat|tom), 0.83 conf
        #   5.jpg (cat|fedor, dog|paul, crow|dylan) -> (crow|theresa) -> (crow|theresa) ->
        #                               (cat|fedor, dog|paul, crow|dylan, crow|theresa), 0.85 conf
    ]
    i = 0
    for iteration_assignments in assignments:
        for assignment in iteration_assignments:
            assignment.id = f'{str(i)}_{assignment.user_id}'
            assignment.status = toloka.Assignment.SUBMITTED
            i += 1

    pool_input_objects = [(image,) for image in images]
    stub = TolokaClientStub(assignments)

    loop = classification_loop.ClassificationLoop(
        client=stub,  # noqa
        task_mapping=lib.image_classification_mapping,
        params=classification_loop.Params(
            aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
            overlap=classification_loop.DynamicOverlap(min_overlap=2, max_overlap=4, confidence=0.8),
            control=control_params,
            task_duration_function=duration.get_const_task_duration_function(task_duration_hint),
        ),
        lang='EN',
    )
    pool = loop.create_pool(control_objects=[((image,), (cls,)) for image, cls in control_images], pool_cfg=pool_cfg)
    loop.add_input_objects(pool.id, pool_input_objects)
    loop.loop(pool.id)
    results, worker_weights = loop.get_results(pool.id, pool_input_objects)

    assert results == [
        (
            {cat: approx(88 / 94), dog: approx(3 / 94), crow: approx(3 / 94)},
            [
                (cat, worker.Human(assignments[0][0])),
                (cat, worker.Human(assignments[1][3])),
                (cat, worker.Human(assignments[2][3])),
            ],
        ),
        (
            {cat: approx(3 / 226), dog: approx(220 / 226), crow: approx(3 / 226)},
            [(dog, worker.Human(assignments[1][1])), (dog, worker.Human(assignments[2][0]))],
        ),
        (
            {cat: approx(44 / 53), dog: approx(6 / 53), crow: approx(3 / 53)},
            [
                (dog, worker.Human(assignments[0][4])),
                (cat, worker.Human(assignments[1][3])),
                (cat, worker.Human(assignments[2][1])),
            ],
        ),
        (
            {cat: approx(30 / 100), dog: approx(55 / 100), crow: approx(15 / 100)},
            [
                (cat, worker.Human(assignments[0][0])),
                (cat, worker.Human(assignments[0][4])),
                (dog, worker.Human(assignments[2][2])),
                (crow, worker.Human(assignments[3][0])),
            ],
        ),
        (
            {cat: approx(44 / 53), dog: approx(6 / 53), crow: approx(3 / 53)},
            [
                (cat, worker.Human(assignments[2][0])),
                (dog, worker.Human(assignments[2][1])),
                (cat, worker.Human(assignments[3][0])),
            ],
        ),
        (
            {dog: approx(22 / 352), cat: approx(30 / 352), crow: approx(300 / 352)},
            [
                (cat, worker.Human(assignments[1][1])),
                (dog, worker.Human(assignments[2][2])),
                (crow, worker.Human(assignments[3][1])),
                (crow, worker.Human(assignments[4][0])),
            ],
        ),
    ]

    assert worker_weights == {
        'john': 1 / 2,
        'bob': 1 / 10,
        'fedor': 5 / 6,
        'mary': 1 / 6,
        'alice': 1 / 2,
        'martha': 5 / 6,
        'paul': 99 / 126,
        'ivan': 1 / 2,
        'tom': 1 / 2,
        'dylan': 5 / 6,
        'theresa': 5 / 6,
    }

    assert stub.calls[1:] == [  # skip pool creation
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/0_control.jpg',
                            'id': "Image(url='https://storage.net/0_control.jpg')",
                        },
                        known_solutions=[
                            toloka.Task.KnownSolution(output_values={'choice': 'cat'}, correctness_weight=1)
                        ],
                        id='task 0',
                        infinite_overlap=True,
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/1_control.jpg',
                            'id': "Image(url='https://storage.net/1_control.jpg')",
                        },
                        known_solutions=[
                            toloka.Task.KnownSolution(output_values={'choice': 'dog'}, correctness_weight=1)
                        ],
                        id='task 1',
                        infinite_overlap=True,
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/2_control.jpg',
                            'id': "Image(url='https://storage.net/2_control.jpg')",
                        },
                        known_solutions=[
                            toloka.Task.KnownSolution(output_values={'choice': 'cat'}, correctness_weight=1)
                        ],
                        id='task 2',
                        infinite_overlap=True,
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/3_control.jpg',
                            'id': "Image(url='https://storage.net/3_control.jpg')",
                        },
                        known_solutions=[
                            toloka.Task.KnownSolution(output_values={'choice': 'dog'}, correctness_weight=1)
                        ],
                        id='task 3',
                        infinite_overlap=True,
                        pool_id=pool_id,
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
                            'image_url': 'https://storage.net/0.jpg',
                            'id': "Image(url='https://storage.net/0.jpg')",
                        },
                        id='task 4',
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/1.jpg',
                            'id': "Image(url='https://storage.net/1.jpg')",
                        },
                        id='task 5',
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/2.jpg',
                            'id': "Image(url='https://storage.net/2.jpg')",
                        },
                        id='task 6',
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/3.jpg',
                            'id': "Image(url='https://storage.net/3.jpg')",
                        },
                        id='task 7',
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/4.jpg',
                            'id': "Image(url='https://storage.net/4.jpg')",
                        },
                        id='task 8',
                        pool_id=pool_id,
                    ),
                    toloka.Task(
                        input_values={
                            'image_url': 'https://storage.net/5.jpg',
                            'id': "Image(url='https://storage.net/5.jpg')",
                        },
                        id='task 9',
                        pool_id=pool_id,
                    ),
                ],
            ),
        ),
        ('open_pool', (pool_id,)),
        # Apply prior filter by time first
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Fast submits, <= 0.1',
                    user_id='john',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=3) + datetime.timedelta(days=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                '5_john',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED, public_comment='Too few correct solutions'
                ),
            ),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [1, 2) done correctly',
                    user_id='john',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=35) + datetime.timedelta(hours=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('0_john', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [0, 1) done correctly',
                    user_id='bob',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=31) + datetime.timedelta(hours=8),
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                '1_bob',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED,
                    public_comment='Check the tasks with numbers: 1, 4. Learn more about tasks acceptance and filing '
                    'appeals in the project instructions.',
                ),
            ),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [0, 1) done correctly',
                    user_id='mary',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=39) + datetime.timedelta(hours=8),
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                '2_mary',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED,
                    public_comment='Check the tasks with numbers: 3, 4. Learn more about tasks acceptance and filing '
                    'appeals in the project instructions.',
                ),
            ),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [0, 1) done correctly',
                    user_id='bob',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=20) + datetime.timedelta(hours=8),
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                '3_bob',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED,
                    public_comment='Check the tasks with numbers: 2, 3. Learn more about tasks acceptance and filing '
                    'appeals in the project instructions.',
                ),
            ),
        ),
        (
            'patch_assignment',
            ('4_alice', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        ('patch_task_overlap_or_min', ('task 4', toloka.task.TaskOverlapPatch(overlap=3))),
        ('patch_task_overlap_or_min', ('task 6', toloka.task.TaskOverlapPatch(overlap=3))),
        ('patch_task_overlap_or_min', ('task 5', toloka.task.TaskOverlapPatch(overlap=4))),
        ('patch_task_overlap_or_min', ('task 9', toloka.task.TaskOverlapPatch(overlap=4))),
        ('patch_task_overlap_or_min', ('task 8', toloka.task.TaskOverlapPatch(overlap=4))),
        ('open_pool', (pool_id,)),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Fast submits, <= 0.1',
                    user_id='martha',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=2) + datetime.timedelta(days=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                '6_martha',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED, public_comment='Too few correct solutions'
                ),
            ),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Fast submits, 0.1 < time <= 0.3',
                    user_id='fedor',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=10) + datetime.timedelta(hours=8),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('7_fedor', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [0, 1) done correctly',
                    user_id='alice',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=39) + datetime.timedelta(hours=8),
                ),
            ),
        ),
        (
            'patch_assignment',
            (
                '8_alice',
                toloka.assignment.AssignmentPatch(
                    status=toloka.Assignment.REJECTED,
                    public_comment='Check the tasks with numbers: 2, 4. Learn more about tasks acceptance and filing '
                    'appeals in the project instructions.',
                ),
            ),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [1, 2) done correctly',
                    user_id='paul',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=30) + datetime.timedelta(hours=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('9_paul', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        ('patch_task_overlap_or_min', ('task 4', toloka.task.TaskOverlapPatch(overlap=4))),
        ('patch_task_overlap_or_min', ('task 7', toloka.task.TaskOverlapPatch(overlap=3))),
        ('patch_task_overlap_or_min', ('task 6', toloka.task.TaskOverlapPatch(overlap=4))),
        ('patch_task_overlap_or_min', ('task 5', toloka.task.TaskOverlapPatch(overlap=5))),
        ('patch_task_overlap_or_min', ('task 9', toloka.task.TaskOverlapPatch(overlap=5))),
        ('patch_task_overlap_or_min', ('task 8', toloka.task.TaskOverlapPatch(overlap=6))),
        ('open_pool', (pool_id,)),
        (
            'patch_assignment',
            ('10_paul', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [1, 2) done correctly',
                    user_id='ivan',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=40) + datetime.timedelta(hours=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('11_ivan', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        (
            'patch_assignment',
            ('12_paul', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [1, 2) done correctly',
                    user_id='tom',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=40) + datetime.timedelta(hours=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('13_tom', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        ('patch_task_overlap_or_min', ('task 7', toloka.task.TaskOverlapPatch(overlap=4))),
        ('patch_task_overlap_or_min', ('task 9', toloka.task.TaskOverlapPatch(overlap=6))),
        ('patch_task_overlap_or_min', ('task 8', toloka.task.TaskOverlapPatch(overlap=7))),
        ('open_pool', (pool_id,)),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Control tasks: [1, 2) done correctly',
                    user_id='tom',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=40) + datetime.timedelta(hours=1),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('14_tom', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        (
            'patch_assignment',
            ('15_dylan', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
        ('patch_task_overlap_or_min', ('task 9', toloka.task.TaskOverlapPatch(overlap=7))),
        ('open_pool', (pool_id,)),
        (
            'set_user_restriction',
            (
                toloka.user_restriction.PoolUserRestriction(
                    private_comment='Fast submits, 0.1 < time <= 0.3',
                    user_id='theresa',
                    pool_id=pool_id,
                    will_expire=assignment_start + datetime.timedelta(seconds=4) + datetime.timedelta(hours=8),
                ),
            ),
        ),
        (
            'patch_assignment',
            ('16_theresa', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
        ),
    ]


class TestTaskIdToOverlapIncrease:
    images = [Image(url=f'https://storage.net/{i}.jpg') for i in range(4)]
    control_images = [
        (Image(url=f'https://storage.net/{i}_control.jpg'), lib.cat if i % 2 == 0 else lib.dog) for i in range(4)
    ]

    class TolokaClientStub:
        def __init__(self, assignments: List[toloka.Assignment]):
            self.assignments = assignments
            self.tasks = [
                lib.image_classification_mapping.to_task((image,)) for image in TestTaskIdToOverlapIncrease.images
            ]
            for task in self.tasks:
                task.id = task.input_values[mapping.TASK_ID_FIELD]

        def get_assignments(
            self,
            status: Union[toloka.Assignment.Status, List[toloka.Assignment.Status]],
            pool_id: str,
        ):
            if not isinstance(status, list):
                status = [status]
            return [assignment for assignment in self.assignments if assignment.status in status]

        def get_tasks(self, *args, **kwargs):
            return self.tasks

    def get_task_id_overlaps(self, image_index_to_overlap: Dict[int, int]) -> Dict[mapping.TaskID, int]:
        return {mapping.TaskID((self.images[index],)): overlap for index, overlap in image_index_to_overlap.items()}

    def test_static_overlap(self):
        cat = lib.cat
        images = self.images

        def gen_assignment_objects(*args) -> List[Tuple[Image, lib.ImageClass]]:
            return [(images[i], cat) for i in args]

        assignments_objects = [
            gen_assignment_objects(0, 1, 3),
            gen_assignment_objects(1, 2, 3),
            gen_assignment_objects(0, 2, 3),
            gen_assignment_objects(0, 1, 2),
        ]

        for objects, statuses, overlap, expected_task_id_to_overlap_increase in [
            (assignments_objects, [toloka.Assignment.ACCEPTED] * 4, 3, {}),
            (
                assignments_objects,
                [toloka.Assignment.REJECTED] * 2 + [toloka.Assignment.ACCEPTED] * 2,
                3,
                self.get_task_id_overlaps({0: 1, 1: 2, 2: 1, 3: 2}),
            ),
            (
                assignments_objects,
                [toloka.Assignment.ACCEPTED] * 2 + [toloka.Assignment.REJECTED] * 2,
                3,
                self.get_task_id_overlaps({0: 2, 1: 1, 2: 2, 3: 1}),
            ),
            (
                assignments_objects[:2],
                [toloka.Assignment.ACCEPTED] * 2,
                3,
                self.get_task_id_overlaps({0: 2, 1: 1, 2: 2, 3: 1}),
            ),
            (
                assignments_objects,
                [toloka.Assignment.ACCEPTED] * 4,
                4,
                self.get_task_id_overlaps({0: 1, 1: 1, 2: 1, 3: 1}),
            ),
            (
                assignments_objects,
                [toloka.Assignment.REJECTED] * 2 + [toloka.Assignment.ACCEPTED] * 2,
                4,
                self.get_task_id_overlaps({0: 2, 1: 3, 2: 2, 3: 3}),
            ),
        ]:
            assignments = [
                lib.create_classification_assignment(assignment_objects, [])[0] for assignment_objects in objects
            ]
            for assignment, status in zip(assignments, statuses):
                assignment.status = status
            stub = self.TolokaClientStub(assignments)
            loop = classification_loop.ClassificationLoop(
                client=stub,  # noqa
                task_mapping=lib.image_classification_mapping,
                params=classification_loop.Params(
                    aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
                    overlap=classification_loop.StaticOverlap(overlap),
                    control=control.Control(rules=control.RuleBuilder().add_static_reward(threshold=0.5).build()),
                    task_duration_function=None,  # noqa
                ),
                lang='RU',
            )
            assert loop.get_task_id_to_overlap_increase('fake') == expected_task_id_to_overlap_increase

    def test_dynamic_overlap(self):
        dog, cat, crow = lib.ImageClass.possible_instances()
        control_images = self.control_images
        images = self.images
        all_assignments = [
            lib.create_classification_assignment(image_class_pairs, control_images, user_id=user_id)[0]
            for image_class_pairs, user_id in [
                #   john  [(0.jpg cat) (1_control.jpg dog [ok]) (3.jpg dog) (2_control.jpg cat [ok])]
                (
                    [(images[0], cat), (control_images[1][0], dog), (images[3], dog), (control_images[2][0], cat)],
                    'john',
                ),
                #   john   [(0_control.jpg cat [ok]) (2.jpg cat) (1.jpg dog) (2_control.jpg cat [ok])]
                (
                    [(control_images[0][0], cat), (images[2], cat), (images[1], dog), (control_images[2][0], cat)],
                    'john',
                ),
                #   mary  [(0.jpg cat) (2.jpg dog) (1_control.jpg dog [ok]) (3_control.jpg dog [ok])]
                (
                    [(images[0], cat), (images[2], dog), (control_images[1][0], dog), (control_images[3][0], dog)],
                    'mary',
                ),
                #   bob   [(0.jpg dog) (3_control.jpg dog [ok]) (1_control.jpg dog [ok]) (2.jpg cat)]
                ([(images[0], dog), (control_images[3][0], dog), (control_images[1][0], dog), (images[2], cat)], 'bob'),
                #   alice [(2.jpg dog) (3.jpg cat) (2_control.jpg dog [bad]) (0_control.jpg dog [bad])]
                (
                    [(images[2], dog), (images[3], cat), (control_images[2][0], dog), (control_images[0][0], dog)],
                    'alice',
                ),
                #   alice  [(2_control.jpg cat [ok]) (0.jpg dog) (1.jpg cat) (0_control.jpg cat [ok])]
                (
                    [(control_images[2][0], cat), (images[0], dog), (images[1], cat), (control_images[0][0], cat)],
                    'alice',
                ),
            ]
        ]

        accepted, rejected = toloka.Assignment.ACCEPTED, toloka.Assignment.REJECTED
        for assignment_indices, statuses, min_overlap, max_overlap, conf, expected_task_id_to_overlap_increase in [
            [
                (0, 1),
                (accepted, rejected),
                3,
                4,
                1.0,  # residual, tasks 0 & 3 have 1 accepted solution each
                self.get_task_id_overlaps({0: 2, 1: 3, 2: 3, 3: 2}),
            ],
            # 0 - 4 attempts already, no more attempts can be done
            # 1 - 2 attempts, 0.85 confidence, not enough, need 1 more attempt at least
            # 2 - 3 attempts, 0.94 confidence, enough, no more attempts needed
            # 3 - 1 attempt only, need 1 more for min_overlap
            [
                (0, 1, 2, 3, 4, 5),
                (accepted, accepted, accepted, accepted, rejected, accepted),
                2,
                4,
                0.9,
                self.get_task_id_overlaps({1: 1, 3: 1}),
            ],
        ]:
            assignments = [all_assignments[i] for i in assignment_indices]
            for assignment, status in zip(assignments, statuses):
                assignment.status = status

            stub = self.TolokaClientStub(assignments)
            loop = classification_loop.ClassificationLoop(
                client=stub,  # noqa
                task_mapping=lib.image_classification_mapping,
                params=classification_loop.Params(
                    aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
                    overlap=classification_loop.DynamicOverlap(
                        min_overlap=min_overlap, max_overlap=max_overlap, confidence=conf
                    ),
                    control=control.Control(rules=control.RuleBuilder().add_static_reward(threshold=0.5).build()),
                    task_duration_function=None,  # noqa
                ),
                lang='RU',
            )
            assert loop.get_task_id_to_overlap_increase('fake') == expected_task_id_to_overlap_increase


class TolokaClientStub(lib.TolokaClientCallRecorderStub):
    def __init__(self, tasks: List[toloka.Task]):
        self.tasks = tasks
        super(TolokaClientStub, self).__init__()

    def get_tasks(self, request: toloka.search_requests.TaskSearchRequest):
        return self.tasks


def test_re_markup_not_finalized_objects():
    audios = [(Audio(url=f'https://storage.net/{i}.wav'),) for i in range(6)]

    def create_assignment(indexes: Iterable[int]) -> mapping.AssignmentSolutions:
        # text is not important here
        return lib.create_markup_assignment([(audios[i][0], Text(text='')) for i in indexes])

    assignments = [
        # [0] #1 attempt BAD, [1] #1 attempt BAD, [2] #1 attempt BAD, [3] #1 attempt OK
        create_assignment([0, 1, 2, 3]),
        # [0] #2 attempt BAD, [1] #2 attempt OK, [4] #1 attempt BAD, [5] #1 attempt OK
        create_assignment([0, 1, 4, 5]),
    ]

    tasks = []
    for i, audio in enumerate(audios):
        task = lib.audio_transcript_mapping.to_task(audio)
        task.id = f'task-{i}'
        tasks.append(task)

    for task_id_to_overlap_increase, expected_objects_to_re_markup, expected_toloka_calls in (
        (
            {task_id: 1 for task_id in [lib.audio_transcript_mapping.task_id(audios[i]) for i in (0, 2, 4)]},
            3,
            [
                ('patch_task_overlap_or_min', ('task-0', toloka.task.TaskOverlapPatch(overlap=3))),
                ('patch_task_overlap_or_min', ('task-2', toloka.task.TaskOverlapPatch(overlap=2))),
                ('patch_task_overlap_or_min', ('task-4', toloka.task.TaskOverlapPatch(overlap=2))),
                ('open_pool', ('fake',)),
            ],
        ),
        (
            {},
            0,
            [],
        ),
    ):
        stub = TolokaClientStub(tasks)
        tasks_to_rework = classification_loop.rework_not_finalized_tasks(
            client=stub,  # noqa
            assignments=assignments,
            task_mapping=lib.audio_transcript_mapping,
            task_id_to_overlap_increase=task_id_to_overlap_increase,
            pool_id='fake',
        )

        assert tasks_to_rework == expected_objects_to_re_markup
        assert stub.calls == expected_toloka_calls


def test_calculate_label_probas():
    dog, cat, crow = lib.dog, lib.cat, lib.crow
    images = [Image(url=f'https://storage.net/{i}.jpg') for i in range(4)]
    control_images = [(Image(url=f'https://storage.net/{i}_control.jpg'), cat if i % 2 == 0 else dog) for i in range(4)]
    task_mapping = lib.image_classification_mapping
    assignment_evaluation_strategy = evaluation.ControlTasksAssignmentAccuracyEvaluationStrategy(task_mapping)
    assignment_solutions = [
        lib.create_classification_assignment(image_class_pairs, control_images, user_id=user_id, status=status)
        for image_class_pairs, user_id, status in [
            ([(images[0], cat), (control_images[0][0], cat), (images[1], dog)], 'john', toloka.Assignment.ACCEPTED),
            ([(images[2], cat), (images[3], crow), (control_images[1][0], crow)], 'kate', toloka.Assignment.REJECTED),
            ([(control_images[2][0], crow), (images[2], dog), (images[0], cat)], 'nolan', toloka.Assignment.REJECTED),
            ([(images[1], dog), (control_images[3][0], dog), (images[3], dog)], 'nolan', toloka.Assignment.ACCEPTED),
        ]
    ]

    # we collect worker weights from both accepted and rejected assignments
    # however, for label aggregation we only use answers from accepted assignments
    # images[0] - [(cat|john)]
    # images[1] - [(dog|john), (dog|nolan)]
    # images[2] - [] - no answers at all
    # images[3] - [(dog|nolan)]

    tasks = []
    task_ids = []
    for i, image in enumerate(images):
        task = task_mapping.to_task((image,))
        task.id = f'task-{i}'
        tasks.append(task)
        task_id = mapping.TaskID((image,))
        task_ids.append(task_id)

    stub = TolokaClientStub(tasks)
    expected = {task_ids[0]: (cat, approx(0.75)), task_ids[1]: (dog, approx(6 / 7)), task_ids[3]: (dog, approx(0.5))}

    assert (
        classification_loop.calculate_label_probas(
            client=stub,  # noqa
            task_mapping=task_mapping,
            assignment_evaluation_strategy=assignment_evaluation_strategy,
            aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
            assignment_solutions=assignment_solutions,
            pool_id='fake',
        )
        == expected
    )
