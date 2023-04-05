from copy import deepcopy
import datetime
import decimal
from typing import Tuple

from mock import patch
from pytest import approx
import toloka.client as toloka

from crowdom import base, classification, control, duration, evaluation, mapping, worker
from crowdom.objects import Audio, Image, Text
from . import lib


def test_collect_evaluations_from_check_assignments():
    false, true = base.BinaryEvaluation(ok=False), base.BinaryEvaluation(ok=True)
    alice, bob, peter = [worker.Human(assignment=toloka.Assignment(user_id=name)) for name in ['Alice', 'Bob', 'Peter']]
    audios = [Audio(url=f'https://storage.net/{i + 1}.wav') for i in range(3)]

    pool_input_objects = [
        (audios[0], Text(text='hi')),
        (audios[1], Text(text='good bye')),
        (audios[2], Text(text='hallo')),
    ]

    task_ids = [mapping.TaskID(input_objects) for input_objects in pool_input_objects]

    assignments_1 = [
        lib.create_check_assignment(
            pool_input_objects, [(0, True), (2, False), (None, False), (1, False)], worker_id='Alice'
        )
    ]
    assignments_2 = [
        lib.create_check_assignment(
            pool_input_objects, [(0, False), (2, True), (None, False), (1, True)], worker_id='Alice'
        ),
        lib.create_check_assignment(
            pool_input_objects, [(None, True), (2, True), (1, False), (0, False)], worker_id='Bob'
        ),
        lib.create_check_assignment(
            pool_input_objects, [(1, True), (2, True), (0, True), (None, True)], worker_id='Peter'
        ),
    ]

    for assignments, confidence_threshold, pool_input_objects, aggregation_algorithm, expected_result in (
        (
            assignments_1,
            0.6,
            pool_input_objects,
            classification.AggregationAlgorithm.MAJORITY_VOTE,
            {
                task_ids[0]: evaluation.SolutionEvaluation(ok=True, confidence=1.0, worker_labels=[(true, alice)]),
                task_ids[1]: evaluation.SolutionEvaluation(ok=False, confidence=0.0, worker_labels=[(false, alice)]),
                task_ids[2]: evaluation.SolutionEvaluation(ok=False, confidence=0.0, worker_labels=[(false, alice)]),
            },
        ),
        (
            assignments_2,
            0.6,
            pool_input_objects,
            classification.AggregationAlgorithm.MAJORITY_VOTE,
            {
                task_ids[0]: evaluation.SolutionEvaluation(
                    ok=False, confidence=1 / 3, worker_labels=[(false, alice), (false, bob), (true, peter)]
                ),
                task_ids[1]: evaluation.SolutionEvaluation(
                    ok=True, confidence=2 / 3, worker_labels=[(true, alice), (false, bob), (true, peter)]
                ),
                task_ids[2]: evaluation.SolutionEvaluation(
                    ok=True, confidence=3 / 3, worker_labels=[(true, alice), (true, bob), (true, peter)]
                ),
            },
        ),
        (
            assignments_2,
            0.7,
            pool_input_objects,
            classification.AggregationAlgorithm.MAJORITY_VOTE,
            {
                task_ids[0]: evaluation.SolutionEvaluation(
                    ok=False, confidence=1 / 3, worker_labels=[(false, alice), (false, bob), (true, peter)]
                ),
                task_ids[1]: evaluation.SolutionEvaluation(
                    ok=False, confidence=2 / 3, worker_labels=[(true, alice), (false, bob), (true, peter)]
                ),
                task_ids[2]: evaluation.SolutionEvaluation(
                    ok=True, confidence=3 / 3, worker_labels=[(true, alice), (true, bob), (true, peter)]
                ),
            },
        ),
        (
            assignments_2,
            0.7,
            # feedback loop case, no strict order for pool input objects, which are obtained from check
            # assignments (and order is obtained accordingly), in our case 3rd and 2nd objects swapped
            None,
            classification.AggregationAlgorithm.MAJORITY_VOTE,
            {
                task_ids[0]: evaluation.SolutionEvaluation(
                    ok=False, confidence=1 / 3, worker_labels=[(false, alice), (false, bob), (true, peter)]
                ),
                task_ids[2]: evaluation.SolutionEvaluation(
                    ok=True, confidence=3 / 3, worker_labels=[(true, alice), (true, bob), (true, peter)]
                ),
                task_ids[1]: evaluation.SolutionEvaluation(
                    ok=False, confidence=2 / 3, worker_labels=[(true, alice), (false, bob), (true, peter)]
                ),
            },
        ),
        (
            assignments_1,
            0.6,
            pool_input_objects,
            classification.AggregationAlgorithm.MAX_LIKELIHOOD,
            {
                task_ids[0]: evaluation.SolutionEvaluation(
                    ok=True, confidence=approx(0.8), worker_labels=[(true, alice)]
                ),
                task_ids[1]: evaluation.SolutionEvaluation(
                    ok=False, confidence=approx(0.2), worker_labels=[(false, alice)]
                ),
                task_ids[2]: evaluation.SolutionEvaluation(
                    ok=False, confidence=approx(0.2), worker_labels=[(false, alice)]
                ),
            },
        ),
        (
            assignments_2,
            0.6,
            pool_input_objects,
            classification.AggregationAlgorithm.MAX_LIKELIHOOD,
            {
                task_ids[0]: evaluation.SolutionEvaluation(
                    ok=False, confidence=approx(3 / 7), worker_labels=[(false, alice), (false, bob), (true, peter)]
                ),
                task_ids[1]: evaluation.SolutionEvaluation(
                    ok=True, confidence=approx(300 / 325), worker_labels=[(true, alice), (false, bob), (true, peter)]
                ),
                task_ids[2]: evaluation.SolutionEvaluation(
                    ok=False, confidence=approx(4 / 7), worker_labels=[(true, alice), (true, bob), (true, peter)]
                ),
            },
        ),
    ):
        assert (
            evaluation.collect_evaluations_from_check_assignments(
                assignments=assignments,
                check_task_mapping=lib.audio_transcript_check_mapping,
                pool_input_objects=pool_input_objects,
                aggregation_algorithm=aggregation_algorithm,
                confidence_threshold=confidence_threshold,
                worker_weights={'Alice': 0.8, 'Bob': 0.25, 'Peter': 0.5},
            )
            == expected_result
        )


@patch('crowdom.evaluation.shuffle')
def test_find_markup_solutions_to_check(shuffle):  # noqa
    assignments = [
        lib.create_markup_assignment(
            [
                (Audio(url='https://storage.net/01.wav'), Text(text='foar')),
                (Audio(url='https://storage.net/02.wav'), Text(text='good day')),
                (Audio(url='https://storage.net/03.wav'), Text(text='halloe')),
                (Audio(url='https://storage.net/04.wav'), Text(text='')),
            ]
        ),
        lib.create_markup_assignment(
            [
                # trick, same solution but other task
                (Audio(url='https://storage.net/05.wav'), Text(text='foar')),
                (Audio(url='https://storage.net/06.wav'), Text(text='no thanks')),
                (Audio(url='https://storage.net/07.wav'), Text(text='')),
                (Audio(url='https://storage.net/08.wav'), Text(text='good boe')),
            ]
        ),
    ]
    checked_solutions = {
        mapping.TaskID((Audio(url='https://storage.net/01.wav'), Text(text='foar'))),
        mapping.TaskID((Audio(url='https://storage.net/03.wav'), Text(text='halloe'))),
        mapping.TaskID((Audio(url='https://storage.net/04.wav'), Text(text=''))),
        mapping.TaskID((Audio(url='https://storage.net/08.wav'), Text(text='good boe'))),
        mapping.TaskID((Audio(url='https://storage.net/09.wav'), Text(text='where is my cargo'))),
    }
    assert evaluation.find_markup_solutions_to_check(
        assignments, checked_solutions, lib.audio_transcript_check_mapping, check_sample=None
    ) == (
        [
            # assignment 1
            ((Audio(url='https://storage.net/02.wav'), Text(text='good day')), worker.Human(assignments[0][0])),
            # assignment 2
            ((Audio(url='https://storage.net/05.wav'), Text(text='foar')), worker.Human(assignments[1][0])),
            ((Audio(url='https://storage.net/06.wav'), Text(text='no thanks')), worker.Human(assignments[1][0])),
            ((Audio(url='https://storage.net/07.wav'), Text(text='')), worker.Human(assignments[1][0])),
        ],
        {
            mapping.TaskID((Audio(url='https://storage.net/01.wav'), Text(text='foar'))),
            mapping.TaskID((Audio(url='https://storage.net/03.wav'), Text(text='halloe'))),
            mapping.TaskID((Audio(url='https://storage.net/04.wav'), Text(text=''))),
            mapping.TaskID((Audio(url='https://storage.net/08.wav'), Text(text='good boe'))),
        },
    )

    assert evaluation.find_markup_solutions_to_check(
        assignments,
        checked_solutions,
        lib.audio_transcript_check_mapping,
        check_sample=evaluation.AssignmentCheckSample(
            max_tasks_to_check=2, assignment_accuracy_finalization_threshold=None
        ),
    ) == (
        [
            # assignment 1
            ((Audio(url='https://storage.net/02.wav'), Text(text='good day')), worker.Human(assignments[0][0])),
            # assignment 2
            ((Audio(url='https://storage.net/05.wav'), Text(text='foar')), worker.Human(assignments[1][0])),
            ((Audio(url='https://storage.net/06.wav'), Text(text='no thanks')), worker.Human(assignments[1][0])),
        ],
        {
            mapping.TaskID((Audio(url='https://storage.net/01.wav'), Text(text='foar'))),
            mapping.TaskID((Audio(url='https://storage.net/03.wav'), Text(text='halloe'))),
            mapping.TaskID((Audio(url='https://storage.net/04.wav'), Text(text=''))),
            mapping.TaskID((Audio(url='https://storage.net/08.wav'), Text(text='good boe'))),
        },
    )


def test_get_objects_markup_attempts():
    for with_model, expected_task_id_to_attempts in (
        (
            True,
            {
                mapping.TaskID((Audio(url='https://storage.net/01.wav'),)): 1,
                mapping.TaskID((Audio(url='https://storage.net/02.wav'),)): 2,
                mapping.TaskID((Audio(url='https://storage.net/03.wav'),)): 2,
                mapping.TaskID((Audio(url='https://storage.net/04.wav'),)): 1,
            },
        ),
        (
            False,
            {
                mapping.TaskID((Audio(url='https://storage.net/01.wav'),)): 1,
                mapping.TaskID((Audio(url='https://storage.net/02.wav'),)): 1,
                mapping.TaskID((Audio(url='https://storage.net/03.wav'),)): 1,
                mapping.TaskID((Audio(url='https://storage.net/04.wav'),)): 0,
            },
        ),
    ):
        assert (
            evaluation.get_tasks_attempts(
                [
                    lib.create_markup_assignment(
                        [
                            (Audio(url='https://storage.net/01.wav'), Text(text='hi')),
                            (Audio(url='https://storage.net/02.wav'), Text(text='')),
                            (Audio(url='https://storage.net/03.wav'), Text(text='hallo')),
                        ]
                    ),
                    lib.create_markup_assignment(
                        [
                            (Audio(url='https://storage.net/02.wav'), Text(text='?')),
                            (Audio(url='https://storage.net/03.wav'), Text(text='hello')),
                            (Audio(url='https://storage.net/04.wav'), Text(text='no thanks')),
                        ],
                        id='',  # model worker
                    ),
                ],
                lib.audio_transcript_mapping,
                with_model,
            )
            == expected_task_id_to_attempts
        )


def test_evaluate_markup_assignment():
    assignment, solutions = lib.create_markup_assignment(
        audio_text_pairs=[
            (Audio(url='https://storage.net/01.wav'), Text(text='hallo')),
            (Audio(url='https://storage.net/02.wav'), Text(text='michael')),
            (Audio(url='https://storage.net/03.wav'), Text(text='good bye')),
            (Audio(url='https://storage.net/04.wav'), Text(text='no thanks')),
            (Audio(url='https://storage.net/05.wav'), Text(text='')),
        ],
        id='123',
        user_id='gleb',
    )
    assert evaluation.CheckAssignmentAccuracyEvaluationStrategy(
        solution_id_to_evaluation=lib.generate_evaluations(
            [
                # audio matches, but solution differs
                ('https://storage.net/01.wav', '? hallo', True),
                # match, BAD
                ('https://storage.net/01.wav', 'hallo', False),
                # audio matches, but solution differs
                ('https://storage.net/02.wav', '?', True),
                # match, OK
                ('https://storage.net/03.wav', 'good bye', True),
                # audio not matches
                ('https://storage.net/00.wav', 'how', False),
                # no checks for 04.wav
                # match, BAD
                ('https://storage.net/05.wav', '', False),
            ]
        ),
        check_task_mapping=lib.audio_transcript_check_mapping,
    ).evaluate_assignment((assignment, solutions)) == evaluation.AssignmentEvaluation(
        assignment=assignment, ok_checks=1, total_checks=3, objects=5, incorrect_solution_indexes=[0, 4]
    )


def test_evaluate_classification_assignment():
    # TODO: need to test optional solution objects
    dog, cat = lib.dog, lib.cat
    images = [Image(url=f'https://storage.net/{i + 1}.jpg') for i in range(3)]
    control_images = [Image(url=f'https://storage.net/c_{i + 1}.jpg') for i in range(3)]
    assignment, solutions = lib.create_classification_assignment(
        image_class_solutions=[
            (control_images[1], dog),  # BAD (cat)
            (images[0], cat),
            (images[1], dog),
            (control_images[2], dog),  # OK
            (control_images[0], cat),  # BAD (dog)
            (images[2], cat),
        ],
        image_class_controls=[(control_images[0], dog), (control_images[1], cat), (control_images[2], dog)],
        user_id='bob',
        id='321',
    )
    assert evaluation.ControlTasksAssignmentAccuracyEvaluationStrategy(
        task_mapping=lib.image_classification_mapping,
    ).evaluate_assignment((assignment, solutions)) == evaluation.AssignmentEvaluation(
        assignment=assignment, ok_checks=1, total_checks=3, objects=6, incorrect_solution_indexes=[0, 4]
    )


@patch('crowdom.control.rule.datetime', wraps=datetime)
def test_apply_rules_to_assignment(mock_datetime):
    now = datetime.datetime(2020, 11, 5)
    mock_datetime.datetime.now.return_value = now
    total_checks = 3
    control_params = control.Control(
        control.RuleBuilder().add_static_reward(threshold=0.5).add_control_task_control(total_checks, 2, 3).build()
    )
    set_verdict_rules = control_params.filter_rules(control.AssignmentAccuracyPredicate, control.SetAssignmentStatus)
    block_rules = control_params.filter_rules(control.AssignmentAccuracyPredicate, control.BlockUser)
    for incorrect_solution_indexes, expected_toloka_calls in (  # add case
        (
            [0, 1],
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='gleb',
                            pool_id='fake',
                            private_comment='Control tasks: [0, 2) done correctly',
                            will_expire=datetime.datetime(2020, 11, 5) + datetime.timedelta(hours=8),
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        '123',
                        toloka.assignment.AssignmentPatch(
                            status=toloka.Assignment.REJECTED,
                            public_comment='Тапсырмаларды нөмірлермен тексеріңіз: 1, 2. Тапсырмаларды тексеру және '
                            'апелляцияларды беру туралы толығырақ жоба нұсқаулығынан оқыңыз.',
                        ),
                    ),
                ),
            ],
        ),
        (
            [0],
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='gleb',
                            pool_id='fake',
                            private_comment='Control tasks: [2, 3) done correctly',
                            will_expire=datetime.datetime(2020, 11, 5) + datetime.timedelta(hours=1),
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    ('123', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
                ),
            ],
        ),
        (
            [],
            [
                (
                    'patch_assignment',
                    ('123', toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment='')),
                )
            ],
        ),
    ):
        ok_checks = total_checks - len(incorrect_solution_indexes)
        stub = lib.TolokaClientCallRecorderStub()
        evaluation.apply_rules_to_assignment(
            set_verdict_rules=set_verdict_rules,
            block_rules=block_rules,
            evaluation=evaluation.AssignmentEvaluation(
                assignment=toloka.Assignment(id='123', user_id='gleb'),
                total_checks=total_checks,
                ok_checks=ok_checks,
                objects=3,
                incorrect_solution_indexes=incorrect_solution_indexes,
            ),
            client=stub,  # noqa
            lang='KK',
            pool_id='fake',
        )
        assert stub.calls == expected_toloka_calls


@patch('crowdom.control.rule.datetime', wraps=datetime)
def test_evaluate_submitted_markup_assignments_and_apply_rules(mock_datetime):
    now = datetime.datetime(2020, 11, 5)
    mock_datetime.datetime.now.return_value = now
    assignment_1 = lib.create_markup_assignment(
        audio_text_pairs=[
            # unknown
            (Audio(url='https://storage.net/00.wav'), Text(text='hi')),
            # evaluations_1 OK
            (Audio(url='https://storage.net/01.wav'), Text(text='no thanks')),
            # evaluations_1 BAD
            (Audio(url='https://storage.net/02.wav'), Text(text='good bye')),
            # unknown
            (Audio(url='https://storage.net/03.wav'), Text(text='hallo yes')),
            # evaluations_1 OK
            (Audio(url='https://storage.net/04.wav'), Text(text='baker street')),
            # unknown
            (Audio(url='https://storage.net/05.wav'), Text(text='no')),
            # evaluations_1 BAD
            (Audio(url='https://storage.net/06.wav'), Text(text='')),
            # unknown
            (Audio(url='https://storage.net/07.wav'), Text(text='yes')),
        ],
        id='assignment 0',
        user_id='user 0',
    )
    assignment_2 = lib.create_markup_assignment(
        audio_text_pairs=[
            # unknown
            (Audio(url='https://storage.net/00.wav'), Text(text='hi')),
            # evaluations_1 BAD
            (Audio(url='https://storage.net/01.wav'), Text(text='no')),
            # unknown
            (Audio(url='https://storage.net/02.wav'), Text(text='')),
            # evaluations_1 OK
            (Audio(url='https://storage.net/03.wav'), Text(text='aw yes')),
            # evaluations_1 BAD
            (Audio(url='https://storage.net/04.wav'), Text(text='boker street')),
        ],
        id='assignment 1',
        user_id='user 1',
    )
    assignment_model = deepcopy(assignment_2)
    assignment_model[0].id = ''
    assignment_model[0].user_id = 'model'

    evaluations_1 = lib.generate_evaluations(
        [
            ('https://storage.net/01.wav', 'no', False),
            ('https://storage.net/01.wav', 'no thanks', True),
            ('https://storage.net/02.wav', 'good bye', False),
            ('https://storage.net/03.wav', 'aw', False),
            ('https://storage.net/03.wav', 'aw yes', True),
            ('https://storage.net/04.wav', 'baker street', True),
            ('https://storage.net/04.wav', 'boker street', False),
            ('https://storage.net/06.wav', '', False),
        ]
    )

    for (
        assignments,
        min_correct_solutions_ratio_for_acceptance,
        solution_id_to_evaluation,
        expected_toloka_calls,
        expected_statuses,
    ) in (
        (
            [assignment_1, assignment_2],
            0.5,
            evaluations_1,
            [
                (
                    'patch_assignment',
                    (
                        'assignment 0',
                        toloka.assignment.AssignmentPatch(
                            status=toloka.Assignment.ACCEPTED,
                            public_comment='',
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='user 1',
                            pool_id='fake',
                            private_comment='Control tasks: [1, 2) done correctly',
                            will_expire=datetime.datetime(2020, 11, 5) + datetime.timedelta(hours=1),
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        'assignment 1',
                        toloka.assignment.AssignmentPatch(
                            status=toloka.Assignment.REJECTED,
                            public_comment='Check the tasks with numbers: 2, 5. Learn more about tasks acceptance and filing '
                            'appeals in the project instructions.',
                        ),
                    ),
                ),
            ],
            [toloka.Assignment.ACCEPTED, toloka.Assignment.REJECTED],
        ),
        (
            [assignment_1],
            0.6,
            evaluations_1,
            [
                (
                    'patch_assignment',
                    (
                        'assignment 0',
                        toloka.assignment.AssignmentPatch(
                            status=toloka.Assignment.REJECTED,
                            public_comment='Check the tasks with numbers: 3, 7. Learn more about tasks acceptance and filing '
                            'appeals in the project instructions.',
                        ),
                    ),
                ),
            ],
            [toloka.Assignment.REJECTED],
        ),
        (
            [assignment_2],
            0.3,
            evaluations_1,
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='user 1',
                            pool_id='fake',
                            private_comment='Control tasks: [1, 2) done correctly',
                            will_expire=datetime.datetime(2020, 11, 5) + datetime.timedelta(hours=1),
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        'assignment 1',
                        toloka.assignment.AssignmentPatch(
                            status=toloka.Assignment.ACCEPTED,
                            public_comment='',
                        ),
                    ),
                ),
            ],
            [toloka.Assignment.ACCEPTED],
        ),
        (
            [assignment_model],
            0.3,
            evaluations_1,
            [],
            [toloka.Assignment.ACCEPTED],
        ),
    ):
        stub = lib.TolokaClientCallRecorderStub()
        actual_statuses = evaluation.evaluate_submitted_assignments_and_apply_rules(
            submitted_assignments=assignments,
            assignment_accuracy_evaluation_strategy=evaluation.CheckAssignmentAccuracyEvaluationStrategy(
                solution_id_to_evaluation=solution_id_to_evaluation,
                check_task_mapping=lib.audio_transcript_check_mapping,
            ),
            control_params=control.Control(
                rules=control.RuleBuilder()
                .add_static_reward(threshold=min_correct_solutions_ratio_for_acceptance)
                # control task count is not exact for all test cases
                .add_control_task_control(4, 1, 2)
                .build()
            ),
            client=stub,  # noqa
            lang='EN',
            pool_id='fake',
        )
        assert actual_statuses == expected_statuses
        assert stub.calls == expected_toloka_calls
        for assignment, expected_status in zip(assignments, expected_statuses):
            if not assignment[0].id:
                # statuses for model assignments should be set on the fly
                assert assignment[0].status == expected_status


def test_get_markup_task_id():
    check_task = mapping.TaskID((Audio(url='https://storage.net/1.wav'), Text(text='hi')))
    assert check_task.id == "Audio(url='https://storage.net/1.wav') Text(text='hi')"
    assert (
        evaluation.get_markup_task_id(check_task, lib.audio_transcript_mapping).id
        == "Audio(url='https://storage.net/1.wav')"
    )


def test_find_finalized_objects():
    assignments = [
        # Finalize by accuracy: NO
        lib.create_markup_assignment(
            audio_text_pairs=[
                # attempt 1, UNKNOWN
                (Audio(url='https://storage.net/00.wav'), Text(text='hello')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/01.wav'), Text(text='no need')),
                # attempt 1, OK (finalized by quality)
                (Audio(url='https://storage.net/02.wav'), Text(text='bye')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/03.wav'), Text(text='? yes')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/04.wav'), Text(text='boker street')),
                # attempt 1, UNKNOWN
                (Audio(url='https://storage.net/05.wav'), Text(text='no')),
            ],
            id='assignment 0',
            user_id='user 0',
        ),
        # Finalize by accuracy: YES
        lib.create_markup_assignment(
            audio_text_pairs=[
                # attempt 1, OK (finalized by quality)
                (Audio(url='https://storage.net/06.wav'), Text(text='')),
                # attempt 1, UNKNOWN (finalized by assignment accuracy)
                (Audio(url='https://storage.net/07.wav'), Text(text='where ?')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/08.wav'), Text(text='ok led')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/09.wav'), Text(text='switch to the orator')),
                # attempt 1, OK (finalized by quality)
                (Audio(url='https://storage.net/10.wav'), Text(text='market')),
                # attempt 1, UNKNOWN (finalized by assignment accuracy)
                (Audio(url='https://storage.net/11.wav'), Text(text='yeah')),
            ],
            id='assignment 1',
            user_id='user 0',
        ),
        # Finalize by accuracy: NO
        lib.create_markup_assignment(
            audio_text_pairs=[
                # attempt 2, UNKNOWN
                (Audio(url='https://storage.net/03.wav'), Text(text='hhm yes')),
                # attempt 2, OK (finalized by quality)
                (Audio(url='https://storage.net/05.wav'), Text(text='what no')),
                # attempt 2, BAD
                (Audio(url='https://storage.net/08.wav'), Text(text='? let')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/12.wav'), Text(text='two foar seven')),
                # attempt 1, UNKNOWN
                (Audio(url='https://storage.net/13.wav'), Text(text='come back later')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/14.wav'), Text(text='call ? mary')),
            ],
            id='assignment 2',
            user_id='user 1',
        ),
        # Finalize by accuracy: NO
        lib.create_markup_assignment(
            audio_text_pairs=[
                # attempt 3, BAD (finalized by max attempts)
                (Audio(url='https://storage.net/03.wav'), Text(text='? yes')),
                # attempt 3, UNKNOWN (finalized by max attempts)
                (Audio(url='https://storage.net/08.wav'), Text(text='yes let')),
                # attempt 2, BAD
                (Audio(url='https://storage.net/13.wav'), Text(text='com latar')),
                # attempt 2, OK (finalized by quality)
                (Audio(url='https://storage.net/14.wav'), Text(text='call mary')),
                # attempt 1, BAD
                (Audio(url='https://storage.net/15.wav'), Text(text='')),
                # attempt 1, UNKNOWN
                (Audio(url='https://storage.net/16.wav'), Text(text='')),
            ],
            id='assignment 3',
            user_id='user 2',
        ),
    ]

    evaluations = lib.generate_evaluations(
        [
            # assignment 0
            ('https://storage.net/01.wav', 'no need', False),
            ('https://storage.net/02.wav', 'bye', True),
            ('https://storage.net/03.wav', '? yes', False),
            ('https://storage.net/04.wav', 'boker street', False),
            # assignment 1
            ('https://storage.net/06.wav', '', True),
            ('https://storage.net/08.wav', 'ok led', False),
            ('https://storage.net/09.wav', 'switch to the orator', False),
            ('https://storage.net/10.wav', 'market', True),
            # assignment 2
            ('https://storage.net/05.wav', 'what no', True),
            ('https://storage.net/08.wav', '? let', False),
            ('https://storage.net/12.wav', 'two foar seven', False),
            ('https://storage.net/14.wav', 'call ? mary', False),
            # assignment 3
            # already present: ('https://storage.net/03.wav', '? yes', False),
            ('https://storage.net/13.wav', 'com latar', False),
            ('https://storage.net/14.wav', 'call mary', True),
            ('https://storage.net/15.wav', '', False),
        ]
    )

    finalized_task_ids = evaluation.find_finalized_tasks(
        markup_assignments=assignments,
        solution_id_to_evaluation=evaluations,
        markup_task_mapping=lib.audio_transcript_mapping,
        check_task_mapping=lib.audio_transcript_check_mapping,
        check_sample=evaluation.AssignmentCheckSample(
            assignment_accuracy_finalization_threshold=0.5, max_tasks_to_check=4
        ),
        max_object_markup_attempts=3,
    )

    assert {task.id for task in finalized_task_ids} == set(
        f"Audio(url='https://storage.net/{i:02d}.wav')" for i in [2, 6, 7, 10, 11, 5, 3, 8, 14]
    )


def test_ok_objects_ratio():
    assert (
        evaluation.get_ok_tasks_ratio(
            lib.generate_evaluations(
                [
                    # OK
                    ('https://storage.net/01.wav', 'ok see you', True),
                    ('https://storage.net/01.wav', 'ok yes bye', False),
                    # BAD
                    ('https://storage.net/02.wav', 'bye', False),
                    # OK
                    ('https://storage.net/03.wav', 'aw', True),
                    # BAD
                    ('https://storage.net/04.wav', 'buker street', False),
                    ('https://storage.net/04.wav', 'boker street', False),
                    # OK
                    ('https://storage.net/05.wav', '', True),
                ]
            ),
            lib.audio_transcript_mapping,
        )
        == 3 / 5
    )


def test_calculate_bonuses_for_markup_assignment():
    rules = [
        control.Rule(
            predicate=control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.AssignmentAccuracyPredicate(threshold=0.5, comparison=control.ComparisonType('>')),
                    control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('<')),
                ],
            ),
            action=control.GiveBonusToUser(amount_usd=0.03),
        ),
        control.Rule(
            predicate=control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('>=')),
                    control.AssignmentAccuracyPredicate(threshold=0.9, comparison=control.ComparisonType('<')),
                ],
            ),
            action=control.GiveBonusToUser(amount_usd=0.04),
        ),
        control.Rule(
            predicate=control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.AssignmentAccuracyPredicate(threshold=0.9, comparison=control.ComparisonType('>=')),
                    control.AssignmentAccuracyPredicate(threshold=1.0, comparison=control.ComparisonType('<=')),
                ],
            ),
            action=control.GiveBonusToUser(amount_usd=0.1),
        ),
    ]

    for assignment_evaluation, expected_bonuses in (
        (
            evaluation.AssignmentEvaluation(
                assignment=toloka.Assignment(id='assignment0', user_id='user1'),
                incorrect_solution_indexes=[],
                ok_checks=9,
                total_checks=10,
                objects=10,
            ),
            [
                toloka.user_bonus.UserBonus(
                    user_id='user1', assignment_id='assignment0', amount=decimal.Decimal(0.1), without_message=True
                ),
            ],
        ),
        (
            evaluation.AssignmentEvaluation(
                assignment=toloka.Assignment(id='assignment1', user_id='user2'),
                incorrect_solution_indexes=[],
                ok_checks=8,
                total_checks=10,
                objects=10,
            ),
            [
                toloka.user_bonus.UserBonus(
                    user_id='user2', assignment_id='assignment1', amount=decimal.Decimal(0.04), without_message=True
                )
            ],
        ),
        (
            evaluation.AssignmentEvaluation(
                assignment=toloka.Assignment(id='assignment2', user_id='user3'),
                incorrect_solution_indexes=[],
                ok_checks=5,
                total_checks=10,
                objects=10,
            ),
            [],
        ),
    ):
        assert evaluation.calculate_bonuses_for_markup_assignment(rules, assignment_evaluation) == expected_bonuses


def test_process_assignment_by_duration():
    task_duration_hint = datetime.timedelta(seconds=10)
    control_params = control.Control(
        rules=control.RuleBuilder().add_speed_control(ratio_rand=0.1, ratio_poor=0.6).rules
    )

    reject_rules = control_params.filter_rules(
        predicate_type=control.AssignmentDurationPredicate, action_type=control.SetAssignmentStatus
    )

    block_rules = control_params.filter_rules(
        predicate_type=control.AssignmentDurationPredicate, action_type=control.BlockUser
    )

    assignment_start = datetime.datetime(year=2020, month=11, day=3)

    image = Image(url='https://storage.net/1.jpg')
    dog = lib.dog
    tasks_count = 4

    for assignment_duration, expected_verdict, expected_toloka_calls in (
        (
            datetime.timedelta(seconds=1) * tasks_count,
            toloka.Assignment.Status.REJECTED,
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='fake_user',
                            private_comment='Fast submits, <= 0.1',
                            will_expire=datetime.datetime(year=2020, month=11, day=4, second=4),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        'fake',
                        toloka.AssignmentPatch(
                            public_comment='Too few correct solutions', status=toloka.Assignment.Status.REJECTED
                        ),
                    ),
                ),
            ],
        ),
        (
            datetime.timedelta(seconds=6) * tasks_count,
            None,
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='fake_user',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=24),
                            pool_id='fake_pool',
                        ),
                    ),
                )
            ],
        ),
        (datetime.timedelta(seconds=7) * tasks_count, None, []),
    ):
        assignment = lib.create_classification_assignment(
            image_class_solutions=[(image, dog) for _ in range(tasks_count)],
            image_class_controls=[],
            duration=assignment_duration,
            assignment_start=assignment_start,
            user_id='fake_user',
            pool_id='fake_pool',
        )[0]
        stub = lib.TolokaClientCallRecorderStub()
        verdict = evaluation.process_assignment_by_duration(
            reject_rules=reject_rules,
            block_rules=block_rules,
            assignment=assignment,
            lang='EN',
            client=stub,
            assignment_duration_hint=task_duration_hint * len(assignment.tasks),
        )  # noqa
        assert stub.calls == expected_toloka_calls
        assert verdict == expected_verdict


def test_prior_filter_assignments():
    task_duration_hint = datetime.timedelta(seconds=10)
    control_params = control.Control(
        rules=control.RuleBuilder().add_speed_control(ratio_rand=0.1, ratio_poor=0.6).rules
    )

    assignment_start = datetime.datetime(year=2020, month=11, day=3)

    images = [Image(url=str(i)) for i in range(5)]
    dog = lib.dog

    assignments = [
        lib.create_classification_assignment(
            image_class_solutions=[(images[i], dog) for i in range(tasks_count)],
            image_class_controls=[],
            duration=datetime.timedelta(seconds=assignment_duration_seconds),
            assignment_start=assignment_start,
            user_id=f'duration-{assignment_duration_seconds}-tasks-{tasks_count}',
            id=f'duration-{assignment_duration_seconds}-tasks-{tasks_count}',
            pool_id='fake_pool',
        )
        for assignment_duration_seconds, tasks_count in zip([4, 5, 24, 25, 7, 7], [4] * 4 + [2, 1])
    ]

    def custom_task_duration_function(input_objects: Tuple[Image]) -> datetime.timedelta:
        image = input_objects[0]
        return task_duration_hint * (int(image.url) + 1)

    for task_duration_function, expected_assignments, expected_fast_assignments, expected_calls in [
        (
            duration.get_const_task_duration_function(task_duration_hint),
            [assignments[i] for i in range(1, 6)],
            [assignments[0]],
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-4-tasks-4',
                            private_comment='Fast submits, <= 0.1',
                            will_expire=datetime.datetime(year=2020, month=11, day=4, second=4),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        'duration-4-tasks-4',
                        toloka.AssignmentPatch(
                            public_comment='Too few correct solutions', status=toloka.Assignment.Status.REJECTED
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-5-tasks-4',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=5),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-24-tasks-4',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=24),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                # incomplete assignment, no reject, but restrict
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-7-tasks-2',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=7),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
            ],
        ),
        (
            custom_task_duration_function,
            [assignments[i] for i in [2, 3, 4, 5]],
            [assignments[i] for i in [0, 1]],
            [
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-4-tasks-4',
                            private_comment='Fast submits, <= 0.1',
                            will_expire=datetime.datetime(year=2020, month=11, day=4, second=4),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        'duration-4-tasks-4',
                        toloka.AssignmentPatch(
                            public_comment='Too few correct solutions', status=toloka.Assignment.Status.REJECTED
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-5-tasks-4',
                            private_comment='Fast submits, <= 0.1',
                            will_expire=datetime.datetime(year=2020, month=11, day=4, hour=0, second=5),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'patch_assignment',
                    (
                        'duration-5-tasks-4',
                        toloka.AssignmentPatch(
                            public_comment='Too few correct solutions', status=toloka.Assignment.Status.REJECTED
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-24-tasks-4',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=24),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-25-tasks-4',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=25),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
                (
                    'set_user_restriction',
                    (
                        toloka.user_restriction.PoolUserRestriction(
                            user_id='duration-7-tasks-2',
                            private_comment='Fast submits, 0.1 < time <= 0.6',
                            will_expire=datetime.datetime(year=2020, month=11, day=3, hour=8, second=7),
                            pool_id='fake_pool',
                        ),
                    ),
                ),
            ],
        ),
    ]:
        stub = lib.TolokaClientCallRecorderStub()

        filtered_assignments, fast_assignments = evaluation.prior_filter_assignments(
            client=stub,  # noqa
            submitted_assignments=assignments,
            control_params=control_params,
            lang='EN',
            task_duration_function=task_duration_function,
        )

        assert filtered_assignments == expected_assignments
        assert fast_assignments == expected_fast_assignments
        assert stub.calls == expected_calls


def test_calculate_worker_weights():
    dog, cat = lib.dog, lib.cat
    images = [Image(url=f'https://storage.net/{i}.jpg') for i in range(6)]
    control_images = [(Image(url=f'https://storage.net/{i}_control.jpg'), cat if i % 2 == 0 else dog) for i in range(4)]
    assignments = [
        lib.create_classification_assignment(
            image_class_pairs, control_images, user_id=user_id, duration=datetime.timedelta(seconds=duration)
        )
        for image_class_pairs, user_id, duration in [
            #   john 2 bad, 2 ok
            (
                [(images[0], cat), (control_images[1][0], cat), (images[3], dog), (control_images[2][0], cat)],
                'john',
                35,
            ),
            ([(control_images[2][0], cat), (images[5], dog), (images[1], dog), (control_images[0][0], dog)], 'john', 3),
            #   bob  4 bad, 0 ok
            ([(control_images[0][0], dog), (images[2], cat), (images[1], dog), (control_images[2][0], dog)], 'bob', 31),
            ([(images[4], dog), (control_images[3][0], cat), (control_images[1][0], cat), (images[0], cat)], 'bob', 20),
            #   mary  2 bad, 0 ok
            (
                [(images[5], cat), (images[4], dog), (control_images[1][0], cat), (control_images[3][0], cat)],
                'mary',
                39,
            ),
            #   alice 0 bad, 2 ok
            (
                [(images[2], dog), (images[3], cat), (control_images[2][0], cat), (control_images[0][0], cat)],
                'alice',
                22,
            ),
        ]
    ]

    assert evaluation.calculate_worker_weights(
        assignments,
        evaluation.ControlTasksAssignmentAccuracyEvaluationStrategy(lib.image_classification_mapping),
    ) == {'alice': 2.5 / 3, 'bob': 0.5 / 5, 'john': 2.5 / 5, 'mary': 0.5 / 3}
