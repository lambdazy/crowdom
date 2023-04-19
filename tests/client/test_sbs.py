from typing import List, Union

import mock

from crowdom import base, mapping, objects
from crowdom.lzy import SbSLoop


def generate_tasks(count: int, control: bool = False) -> List[Union[mapping.Objects, mapping.TaskSingleSolution]]:
    control_prefix = 'control-' if control else ''
    tasks = [
        (
            objects.Image(url=f'https://storage.net/{control_prefix}{i}.jpg'),
            objects.Audio(url=f'https://storage.net/{control_prefix}{i}.wav'),
            objects.Text(text=f'{control_prefix}text {i}'),
            objects.Audio(url=f'https://storage.net/{control_prefix}{chr(ord("a") + i)}.wav'),
            objects.Text(text=f'{control_prefix}text {chr(ord("a") + i)}'),
        )
        for i in range(count)
    ]
    if control:
        return [(task, (base.SbSChoice.A,) if i % 2 == 0 else (base.SbSChoice.B,)) for i, task in enumerate(tasks)]
    return tasks


@mock.patch('crowdom.classification_loop.ClassificationLoop.get_results')
@mock.patch('crowdom.classification_loop.ClassificationLoop.add_input_objects')
@mock.patch('crowdom.classification_loop.ClassificationLoop.create_pool')
@mock.patch('crowdom.lzy.workflows.sbs.choice')
def test_sbs_new(choice, create_pool, add_input_objects, get_results):
    loop = SbSLoop(
        client=None,  # noqa
        task_mapping=None,  # noqa
        params=None,  # noqa
        lang=None,  # noqa
        with_control_tasks=True,
        model=None,
        task_function=base.SbSFunction(inputs=(objects.Audio, objects.Text), hints=(objects.Image,)),
    )

    pool_cfg = None
    pool_id = 'pool_id'

    control_objects = generate_tasks(2, control=True)
    choice.side_effect = [True, False]  # control objects swaps
    loop.create_pool(control_objects, pool_cfg)
    create_pool.assert_called_with([
        (
            (
                objects.Image(url=f'https://storage.net/control-{i}.jpg'),
                objects.Audio(url=f'https://storage.net/control-{a}.wav'),
                objects.Text(text=f'control-text {a}'),
                objects.Audio(url=f'https://storage.net/control-{b}.wav'),
                objects.Text(text=f'control-text {b}'),
            ),
            (choice,),
        )
        for i, (a, b, choice) in enumerate([('a', 0, base.SbSChoice.B), (1, 'b', base.SbSChoice.B)])
    ], pool_cfg)

    input_objects = generate_tasks(5)
    loop.swaps = [False, True, False, True, True]  # input objects swaps
    loop.add_input_objects(pool_id, input_objects)
    add_input_objects.assert_called_with(pool_id, [
        (
            objects.Image(url=f'https://storage.net/{i}.jpg'),
            objects.Audio(url=f'https://storage.net/{a}.wav'),
            objects.Text(text=f'text {a}'),
            objects.Audio(url=f'https://storage.net/{b}.wav'),
            objects.Text(text=f'text {b}'),
        )
        for i, (a, b) in enumerate([(0, 'a'), ('b', 1), (2, 'c'), ('d', 3), ('e', 4)])
    ])

    a_win, b_win = base.SbSChoice.A, base.SbSChoice.B
    workers = [f'w{i}' for i in range(30)]  # precise type does not matter for this test

    # swapped results
    get_results.side_effect = [(
        [
            (
                {a_win: 0.9, b_win: 0.1},
                [(b_win, workers[27]), (b_win, workers[9]), (a_win, workers[2]), (a_win, workers[7])],
            ),
            ({a_win: 0.3, b_win: 0.7}, [(b_win, workers[1]), (b_win, workers[27]), (a_win, workers[15])]),
            ({a_win: 0.5, b_win: 0.5}, [(a_win, workers[11]), (b_win, workers[12])]),
            ({a_win: 0.8, b_win: 0.2}, [(a_win, workers[10]), (b_win, workers[3]), (a_win, workers[7])]),
            ({a_win: 1.0, b_win: 0.0}, [(a_win, workers[19]), (a_win, workers[3]), (a_win, workers[20])]),
        ],
        None,
    )]
    assert loop.get_results(pool_id, input_objects) == (
        [
            (
                {a_win: 0.9, b_win: 0.1},
                [(b_win, workers[27]), (b_win, workers[9]), (a_win, workers[2]), (a_win, workers[7])],
            ),
            ({b_win: 0.3, a_win: 0.7}, [(a_win, workers[1]), (a_win, workers[27]), (b_win, workers[15])]),
            ({a_win: 0.5, b_win: 0.5}, [(a_win, workers[11]), (b_win, workers[12])]),
            ({b_win: 0.8, a_win: 0.2}, [(b_win, workers[10]), (a_win, workers[3]), (b_win, workers[7])]),
            ({b_win: 1.0, a_win: 0.0}, [(b_win, workers[19]), (b_win, workers[3]), (b_win, workers[20])]),
        ],
        None
    )
