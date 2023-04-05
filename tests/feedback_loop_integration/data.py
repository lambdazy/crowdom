import datetime
from typing import List

import toloka.client as toloka

from crowdom import base, mapping, objects, worker
from .. import lib

audios = [objects.Audio(url=f'https://storage.net/{i:02d}.wav') for i in range(22)]
control_audios = [
    ((objects.Audio(url='https://storage.net/82.wav'), objects.Text(text='алло')), (base.BinaryEvaluation(ok=True),))
]

markup_pool_id = 'markup pool'
check_pool_id = 'check pool'

markup_task_mapping = mapping.TaskMapping(input_mapping=(lib.audio_mapping,), output_mapping=(lib.text_mapping,))
check_task_mapping = mapping.TaskMapping(
    input_mapping=(lib.audio_mapping, lib.text_mapping), output_mapping=(lib.binary_evaluation_mapping,)
)

pool_input_objects = [(audio,) for audio in audios]
pool_input_objects_model = [(audio,) for audio in audios[:6]]


def generate_assignments(assignments_iterations, has_model_markup: bool = False, has_durations: bool = False):
    tasks = []
    markup_tasks = [
        toloka.Task(
            pool_id=markup_pool_id,
            input_values={'audio_link': audio.url, 'id': lib.audio_transcript_mapping.task_id((audio,)).id},
            id=f'task {i}',
        )
        for i, audio in enumerate(audios)
    ]
    tasks += markup_tasks
    task_index = len(markup_tasks)

    control_tasks = [
        toloka.Task(
            pool_id=check_pool_id,
            input_values={
                'audio_link': control_audio[0][0].url,
                'output': control_audio[0][1].text,
                'id': lib.audio_transcript_check_mapping.task_id(
                    (objects.Audio(url=control_audio[0][0].url), objects.Text(text=control_audio[0][1].text)),
                ).id,
            },
            known_solutions=[
                toloka.Task.KnownSolution(output_values={'ok': control_audio[1][0].ok}, correctness_weight=1)
            ],
            infinite_overlap=True,
            id=f'task {task_index + i}',
        )
        for i, control_audio in enumerate(control_audios)
    ]
    task_index += len(control_audios)
    tasks += control_tasks

    model_markup_assignment = None
    if has_model_markup:
        model_markup_assignment = worker.ModelWorkspace(model_markup, markup_task_mapping).get_solutions(
            pool_input_objects_model
        )

    markup_assignments = []
    check_assignments = []
    markup_assignments_count = 0
    check_assignments_count = 0
    created = datetime.datetime(year=2020, month=10, day=5, hour=13, minute=15)

    for assignments in assignments_iterations:
        markup_assignments_data, check_assignments_data = assignments
        if not has_durations:
            markup_assignments_data = [
                (assignment, datetime.timedelta(minutes=1)) for assignment in markup_assignments_data
            ]
        iteration_markup_assignments = []
        for assignment, duration in markup_assignments_data:
            assignment_tasks = []
            assignment_solutions = []
            for obj_index, text in assignment:
                solution = toloka.solution.Solution(output_values={'output': text})
                assignment_tasks.append(markup_tasks[obj_index])
                assignment_solutions.append(solution)
            iteration_markup_assignments.append(
                toloka.Assignment(
                    id=f'markup assignment {markup_assignments_count}',
                    user_id=f'markup-{markup_assignments_count}',
                    tasks=assignment_tasks,
                    solutions=assignment_solutions,
                    status=toloka.Assignment.SUBMITTED,
                    created=created,
                    submitted=created + duration,
                    pool_id='markup pool',
                )
            )
            markup_assignments_count += 1
        markup_assignments += [iteration_markup_assignments]

        iteration_check_assignments = []
        markup_assignment_solution_index_to_check_task = {}
        if not has_durations:
            check_assignments_data = [
                (assignment, datetime.timedelta(minutes=5)) for assignment in check_assignments_data
            ]
        for assignment, duration in check_assignments_data:
            assignment_tasks = []
            assignment_solutions = []
            for markup_assignment_index, solution_index, ok in assignment:
                if markup_assignment_index is None:
                    # control task, solution index is index of control task
                    check_task = tasks[len(markup_tasks) + solution_index]
                else:
                    pair = (markup_assignment_index, solution_index)
                    if pair not in markup_assignment_solution_index_to_check_task:
                        if markup_assignment_index == -1:
                            markup_assignment = model_markup_assignment
                        else:
                            markup_assignment = iteration_markup_assignments[markup_assignment_index]
                        url = markup_assignment.tasks[solution_index].input_values['audio_link']
                        text = markup_assignment.solutions[solution_index].output_values['output']
                        check_task = toloka.Task(
                            pool_id=check_pool_id,
                            input_values={
                                'audio_link': url,
                                'output': text,
                                'id': lib.audio_transcript_check_mapping.task_id(
                                    (objects.Audio(url=url), objects.Text(text=text))
                                ).id,
                            },
                            id=f'task {task_index}',
                        )
                        task_index += 1
                        tasks.append(check_task)
                        markup_assignment_solution_index_to_check_task[pair] = check_task
                    check_task = markup_assignment_solution_index_to_check_task[pair]
                assignment_tasks.append(check_task)
                assignment_solutions.append(toloka.solution.Solution(output_values={'ok': ok}))
            iteration_check_assignments.append(
                toloka.Assignment(
                    id=f'check assignment {check_assignments_count}',
                    tasks=assignment_tasks,
                    solutions=assignment_solutions,
                    user_id=f'check-{check_assignments_count}',
                    status=toloka.Assignment.SUBMITTED,
                    created=created,
                    submitted=created + duration,
                )
            )
            check_assignments_count += 1
        check_assignments += [iteration_check_assignments]
    return tasks, markup_assignments, check_assignments


tasks, markup_assignments_by_iterations, check_assignments_by_iterations = generate_assignments(
    [
        (  # iteration 1
            (  # markups assignments received on this iteration
                (  # 1/4 tasks OK
                    # list of (object index, text)
                    (1, 'нет надо'),  # BAD by 1/3
                    (2, 'хорошо до свидания'),  # OK by 2/3
                    (3, 'не'),  # BAD by 0/3
                    (5, 'я оплатил'),  # BAD by 1/3
                    (0, 'семнадцать'),  # unknown
                    (4, 'абонент'),  # unknown, BAD in further assignment check
                ),
                (  # 0/4 tasks OK
                    (6, '?'),  # BAD by 0/3
                    (7, 'где посмотреть какой счет'),  # BAD by 1/3
                    (9, 'спасибо'),  # BAD by 1/3
                    (10, 'улица горчакова'),  # BAD by 1/3
                    (8, 'два три пять'),  # unknown
                    (11, 'перезвоните позднее'),  # unknown
                ),
                (  # 2/4 tasks OK
                    (13, 'алло'),  # OK by 3/3
                    (15, '?'),  # BAD by 0/3
                    (16, 'я смотрю сейчас насчет'),  # BAD by 1/3
                    (17, 'да'),  # OK by 2/3
                    (12, 'восемь четыре'),  # unknown, finalized
                    (14, 'абонент временно недоступен'),  # unknown, finalized
                ),
                (  # 1/4 tasks OK
                    (18, 'суббот'),  # BAD by 0/3
                    (19, 'не нужно'),  # BAD by 1/3
                    (20, 'да хорошо'),  # OK by 2/3
                    (21, 'четыре четыре шесть восемь'),  # BAD by 1/3
                ),
            ),
            (  # check assignments received on this iteration
                (
                    # list of (markup assignment index, solution index, OK)
                    (0, 0, False),  # (0, 0) 1/3
                    (0, 1, True),  # (0, 1) 1/3
                    (0, 2, False),  # (0, 2) 1/3
                    (0, 3, False),  # (0, 3) 1/3
                    (1, 0, False),  # (1, 0) 1/3
                    (1, 1, True),  # (1, 1) 1/3
                    (1, 2, False),  # (1, 2) 1/3
                    (1, 3, False),  # (1, 3) 1/3
                    (2, 0, True),  # (2, 0) 1/3
                    (2, 1, False),  # (2, 1) 1/3
                    (2, 2, True),  # (2, 2) 1/3
                    (2, 3, True),  # (2, 3) 1/3,
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 0, True),  # (0, 0) 2/3
                    (0, 1, True),  # (0, 1) 2/3
                    (1, 0, False),  # (1, 0) 2/3
                    (1, 1, False),  # (1, 1) 2/3
                    (1, 2, True),  # (1, 2) 2/3
                    (1, 3, False),  # (1, 3) 2/3
                    (2, 0, True),  # (2, 0) 2/3
                    (2, 1, False),  # (2, 1) 2/3
                    (2, 2, False),  # (2, 2) 2/3
                    (2, 3, False),  # (2, 3) 2/3
                    (3, 0, False),  # (3, 0) 1/3
                    (3, 1, True),  # (3, 1) 1/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 0, False),  # (0, 0) 3/3
                    (0, 1, False),  # (0, 1) 3/3
                    (0, 2, False),  # (0, 2) 2/3
                    (0, 3, False),  # (0, 3) 2/3
                    (1, 0, False),  # (1, 0) 3/3
                    (1, 1, False),  # (1, 1) 3/3
                    (1, 2, False),  # (1, 2) 3/3
                    (1, 3, True),  # (1, 3) 3/3
                    (3, 0, False),  # (3, 0) 2/3
                    (3, 1, False),  # (3, 1) 2/3
                    (3, 2, False),  # (3, 2) 1/3
                    (3, 3, False),  # (3, 3) 1/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 2, False),  # (0, 2) 3/3
                    (0, 3, True),  # (0, 3) 3/3
                    (2, 0, True),  # (2, 0) 3/3
                    (2, 1, False),  # (2, 1) 3/3
                    (2, 2, False),  # (2, 2) 3/3
                    (2, 3, True),  # (2, 3) 3/3
                    (3, 0, False),  # (3, 0) 3/3
                    (3, 1, False),  # (3, 1) 3/3
                    (3, 2, True),  # (3, 2) 2/3
                    (3, 3, True),  # (3, 3) 2/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (3, 2, True),  # (3, 2) 3/3
                    (3, 3, False),  # (3, 3) 3/3
                    (None, 0, True),  # control audio, OK
                ),
            ),
        ),
        (  # iteration 2
            (
                (  # 3/4 tasks OK
                    (0, 'семнадцать'),  # BAD by 1/3 (already seen but not checked yet)
                    (1, 'а нет не надо'),  # OK by 2/3
                    (5, 'я уже оплатил'),  # OK by 2/3
                    (6, 'где'),  # OK by 2/3
                    (3, 'нет'),  # unknown, finalized
                    (4, 'абонент не'),  # unknown, finalized
                ),
                (  # 1/4 tasks OK
                    (9, 'спасибо'),  # BAD already seen
                    (7, 'а где посмотреть мой счет'),  # BAD by 1/3
                    (8, 'два три пять восемь'),  # OK by 2/3
                    (10, 'улица ?'),  # BAD by 1/3
                    (15, 'ха'),  # BAD by 0/3
                    (11, 'перезвоните познее'),  # unknown
                ),
                (  # 0/4 tasks OK
                    (16, 'я смотрю сейчас счет'),  # BAD by 1/3
                    (21, 'четыре четыре шесть восемь'),  # BAD already seen
                    (18, '?'),  # BAD by 0/3
                    (19, 'ни нужно'),  # BAD by 0/3
                ),
            ),
            (
                (
                    (0, 0, False),  # (0, 0) 1/3
                    (0, 1, True),  # (0, 1) 1/3
                    (0, 2, False),  # (0, 2) 1/3
                    (0, 3, True),  # (0, 3) 1/3
                    (1, 1, False),  # (1, 1) 1/3
                    (1, 2, True),  # (1, 2) 1/3
                    (1, 3, True),  # (1, 3) 1/3
                    (1, 4, False),  # (1, 4) 1/3
                    (2, 0, False),  # (2, 0) 1/3
                    (2, 2, False),  # (2, 2) 1/3
                    (2, 3, False),  # (2, 3) 1/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 0, True),  # (0, 0) 2/3
                    (0, 1, False),  # (0, 1) 2/3
                    (0, 2, True),  # (0, 2) 2/3
                    (0, 3, True),  # (0, 3) 2/3
                    (1, 1, False),  # (1, 1) 2/3
                    (1, 2, True),  # (1, 2) 2/3
                    (1, 3, False),  # (1, 3) 2/3
                    (1, 4, False),  # (1, 4) 2/3
                    (2, 0, False),  # (2, 0) 2/3
                    (2, 2, False),  # (2, 2) 2/3
                    (2, 3, False),  # (2, 3) 2/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 0, False),  # (0, 0) 3/3
                    (0, 1, True),  # (0, 1) 3/3
                    (0, 2, True),  # (0, 2) 3/3
                    (0, 3, False),  # (0, 3) 3/3
                    (1, 1, True),  # (1, 1) 3/3
                    (1, 2, False),  # (1, 2) 3/3
                    (1, 3, False),  # (1, 3) 3/3
                    (1, 4, False),  # (1, 4) 3/3
                    (2, 0, True),  # (2, 0) 3/3
                    (2, 2, False),  # (2, 2) 3/3
                    (2, 3, False),  # (2, 3) 3/3
                    (None, 0, True),  # control audio, OK
                ),
            ),
        ),
        (  # iteration 3
            (
                (  # 1/4 tasks OK
                    (0, '? семнадцать'),  # BAD by 1/3
                    (7, 'а где посмотреть на мой счет'),  # OK by 3/3
                    (15, '?'),  # BAD already seen
                    (9, 'не спасибо'),  # BAD by 1/3
                    (11, 'перезвните позднее'),  # BAD by 0/3
                    (10, 'улица гончарова'),  # unknown
                ),
                (  # 2/4 tasks OK
                    (16, 'я смотрю сейчас на свой счет'),  # OK by 2/3
                    (18, '? да'),  # BAD by 1/3
                    (19, 'нет не нужно'),  # OK by 2/3
                    (21, 'один четыре восемь'),  # BAD by 1/3
                ),
            ),
            (
                (
                    (0, 0, True),  # (0, 0) 1/3
                    (0, 1, True),  # (0, 1) 1/3
                    (0, 3, False),  # (0, 3) 1/3
                    (0, 4, False),  # (0, 4) 1/3
                    (1, 0, False),  # (1, 0) 1/3
                    (1, 1, False),  # (1, 1) 1/3
                    (1, 2, True),  # (1, 2) 1/3
                    (1, 3, False),  # (1, 3) 1/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 0, False),  # (0, 0) 2/3
                    (0, 1, True),  # (0, 1) 2/3
                    (0, 3, False),  # (0, 3) 2/3
                    (0, 4, False),  # (0, 4) 2/3
                    (1, 0, True),  # (1, 0) 2/3
                    (1, 1, True),  # (1, 1) 2/3
                    (1, 2, False),  # (1, 2) 2/3
                    (1, 3, True),  # (1, 3) 2/3
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 0, False),  # (0, 0) 3/3
                    (0, 1, True),  # (0, 1) 3/3
                    (0, 3, True),  # (0, 3) 3/3
                    (0, 4, False),  # (0, 4) 3/3
                    (1, 0, True),  # (1, 0) 3/3
                    (1, 1, False),  # (1, 1) 3/3
                    (1, 2, True),  # (1, 2) 3/3
                    (1, 3, False),  # (1, 3) 3/3
                    (None, 0, True),  # control audio, OK
                ),
            ),
        ),
    ]
)

_, speed_markup_assignments_by_iterations, speed_check_assignments_by_iterations = generate_assignments(
    [
        (  # iteration 1
            (  # markups assignments received on this iteration
                (
                    (  # 1/3 tasks OK
                        # list of (object index, text)
                        (1, 'нет надо'),  # BAD by 0/1
                        (2, 'хорошо до свидания'),  # BAD by 0/1
                        (0, 'семнадцать'),  # OK by 1/1
                        (3, 'нет спа'),  # unknown
                    ),
                    datetime.timedelta(minutes=3),
                ),
                (
                    (  # REJECTED, too fast
                        (6, '?'),
                        (7, 'где посмотреть какой счет'),
                        (4, 'спасибо'),
                        (5, 'улица горчакова'),
                    ),
                    datetime.timedelta(seconds=3),
                ),
                (
                    ((8, 'алло'),),  # 1/1 tasks OK  # OK by 1/1
                    datetime.timedelta(minutes=3),
                ),
            ),
            (  # check assignments received on this iteration
                (
                    (
                        # list of (markup assignment index, solution index, OK)
                        (0, 0, False),  # (0, 0) 1/1
                        (0, 1, False),  # (0, 1) 1/1
                        (0, 2, True),  # (0, 2) 1/1
                        (2, 0, True),  # (2, 0) 1/1
                        (None, 0, True),  # control audio, OK
                    ),
                    datetime.timedelta(minutes=5),
                ),
            ),
        ),
        (  # iteration 2
            (
                (
                    (  # 2/3 tasks OK
                        (6, 'да конечно'),  # OK by 1/1
                        (4, 'спасибо'),  # OK by 1/1
                        (7, 'где посмотреть какой счет'),  # BAD by 1/1
                        (5, 'улица горчакова'),  # unknown
                    ),
                    datetime.timedelta(minutes=3),
                ),
                (
                    (  # REJECTED, too fast
                        (1, '?'),
                        (2, 'тот свидание'),
                        (3, '?'),
                    ),
                    datetime.timedelta(seconds=3),
                ),
            ),
            (
                (
                    (
                        (0, 0, True),  # (0, 0) 1/1
                        (0, 1, True),  # (0, 1) 1/1
                        (0, 2, False),  # (0, 2) 1/1
                        (None, 0, True),  # control audio, OK
                    ),
                    datetime.timedelta(minutes=5),
                ),
            ),
        ),
        (  # iteration 3
            (
                (
                    (  # 2/3 tasks OK
                        (1, 'не надо'),  # OK by 1/1
                        (7, 'а где посмотреть на мой счет'),  # OK by 1/1
                        (5, 'на улице горчакова'),  # BAD by 0/1
                        (3, 'не спасибо'),  # unknown, later - OK by 1/1
                    ),
                    datetime.timedelta(minutes=3),
                ),
                (
                    ((2, 'хорошо да до свидания'),),  # 1/1 tasks OK  # OK by 1/1
                    datetime.timedelta(minutes=3),
                ),
            ),
            (
                (
                    (
                        (0, 0, True),  # (0, 0) 1/1
                        (0, 1, True),  # (0, 1) 1/1
                        (0, 2, False),  # (0, 3) 1/1
                        (1, 0, True),  # (1, 0) 1/1
                        (None, 0, True),  # control audio, OK
                    ),
                    datetime.timedelta(minutes=5),
                ),
            ),
        ),
        (  # iteration 4
            (
                (
                    (  # 1/2 tasks OK
                        (5, 'на уличке горчакова'),  # BAD by 0/1
                        (3, 'не спасибо'),  # OK by 1/1
                    ),
                    datetime.timedelta(minutes=3),
                ),
            ),
            (
                (
                    (
                        (0, 0, False),  # (0, 0) 1/1
                        (0, 1, True),  # (0, 1) 1/1
                        (None, 0, True),  # control audio, OK
                    ),
                    datetime.timedelta(minutes=5),
                ),
            ),
        ),
    ],
    has_durations=True,
)


def model_check_func(pool_input_objects: List[mapping.Objects]) -> List[mapping.Objects]:
    checks = {
        'нет надо': False,
        'хорошо до свидания': True,
        'семнадцать': True,
        'нет': True,
        'я оплатил': False,
        'абонент': False,
        '?': False,
        'нет не надо': True,
        'да я оплатил': True,
    }
    return [(base.BinaryEvaluation(ok=checks[text.text]),) for _, text in pool_input_objects]


model_check = worker.Model(name='asr', func=model_check_func)

_, markup_assignments_by_iterations_model_check, _ = generate_assignments(
    [
        (  # iteration 1
            (
                (  # 2/3 tasks OK
                    (1, 'нет надо'),  # BAD
                    (2, 'хорошо до свидания'),  # OK
                    (0, 'семнадцать'),  # OK
                ),
                (  # 1/3 tasks OK
                    (3, 'нет'),  # OK
                    (5, 'я оплатил'),  # BAD
                    (4, 'абонент'),  # BAD
                ),
            ),
            [],  # checks are provided by model, see model_check_func()
        ),
        (  # iteration 2
            (
                (  # 2/3 tasks OK
                    (4, '?'),  # BAD
                    (1, 'нет не надо'),  # OK
                    (5, 'да я оплатил'),  # OK
                ),
            ),
            [],  # checks are provided by model, see model_check_func()
        ),
    ]
)


def model_markup_func(pool_input_objects: List[mapping.Objects]) -> List[mapping.Objects]:
    markups = {
        f'https://storage.net/{audio_index:02d}.wav': text
        for audio_index, text in {
            0: 'семнадцать',  # OK by 2/2
            1: 'нет надо',  # BAD by 1/2
            2: 'хорошо до свидания',  # OK by 2/2
            3: 'нет',  # BAD by 1/2
            4: 'абонент',  # BAD by 0/2
            5: 'я оплатил',  # BAD by 1/2
        }.items()
    }
    return [(objects.Text(text=markups[input_objects[0].url]),) for input_objects in pool_input_objects]


model_markup = worker.Model(name='asr', func=model_markup_func)

_, markup_assignments_by_iterations_model_markup, check_assignments_by_iterations_model_markup = generate_assignments(
    [
        (  # iteration 1
            [],  # first iteration markups are provided by model, see model_markup_func()
            (
                (
                    # list of (markup assignment index, solution index, OK)
                    (-1, 0, True),  # (-1, 0) 2/2
                    (-1, 1, True),  # (-1, 1) 1/2
                    (-1, 2, True),  # (-1, 2) 2/2
                    (-1, 3, False),  # (-1, 3) 1/2
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (-1, 2, True),  # (-1, 2) 2/2
                    (-1, 3, True),  # (-1, 3) 1/2
                    (-1, 4, False),  # (-1, 4) 0/2
                    (-1, 5, True),  # (-1, 5) 1/2
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (-1, 0, True),  # (-1, 0) 2/2
                    (-1, 1, False),  # (-1, 1) 1/2
                    (-1, 4, False),  # (-1, 4) 0/2
                    (-1, 5, False),  # (-1, 5) 1/2
                    (None, 0, True),  # control audio, OK
                ),
            ),
        ),
        (  # iteration 2
            (
                (  # 1/3 tasks OK
                    (1, 'нет надо'),  # BAD already seen in model
                    (3, 'ну нет'),  # BAD by 1/2
                    (5, 'да я оплатил'),  # OK by 2/2
                ),
                ((4, 'абонент недоступен'),),  # 1/1 tasks OK  # OK by 2/2
            ),
            (
                (
                    (0, 1, True),  # (0, 3) 1/2
                    (0, 2, True),  # (0, 4) 2/2
                    (1, 0, True),  # (0, 5) 2/2
                    (None, 0, True),  # control audio, OK
                ),
                (
                    (0, 1, False),  # (0, 3) 1/2
                    (0, 2, True),  # (0, 4) 2/2
                    (1, 0, True),  # (0, 5) 2/2
                    (None, 0, True),  # control audio, OK
                ),
            ),
        ),
    ],
    has_model_markup=True,
)

markup_project = toloka.Project(
    id='markup project',
    task_spec=toloka.project.TaskSpec(
        input_spec=lib.audio_transcript_mapping.to_toloka_input_spec(),
        output_spec=lib.audio_transcript_mapping.to_toloka_output_spec(),
    ),
)
check_project = toloka.Project(
    id='check project',
    task_spec=toloka.project.TaskSpec(
        input_spec=lib.audio_transcript_check_mapping.to_toloka_input_spec(),
        output_spec=lib.audio_transcript_check_mapping.to_toloka_output_spec(),
    ),
)
