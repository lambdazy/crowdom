from typing import List, Union

import mock

from crowdom import base, client, mapping, objects


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


@mock.patch('crowdom.client.sbs.choice')
@mock.patch('crowdom.client.relaunch.choice')
@mock.patch('crowdom.client.sbs.launch')
def test_sbs_swaps(launch, relaunch_choice, choice):
    swaps = [False, True, False, True, True, True, False]
    # swaps for 5 real tasks will be created in relaunch.get_swaps
    relaunch_choice.side_effect = swaps[:5]
    # swaps for 2 control objects will be created in sbs.launch
    choice.side_effect = swaps[5:]

    task_spec = base.TaskSpec(
        function=base.SbSFunction(inputs=(objects.Audio, objects.Text), hints=(objects.Image,)),
        id='id',
        name=base.EMPTY_STRING,  # noqa
        description=None,
        instruction=None,
    )  # noqa

    input_objects = generate_tasks(5)
    control_objects = generate_tasks(2, control=True)

    a_win, b_win = base.SbSChoice.A, base.SbSChoice.B
    workers = [f'w{i}' for i in range(30)]  # precise type does not matter for this test

    # results for swapped pairs
    launch.return_value = [
        (
            {a_win: 0.9, b_win: 0.1},
            [(b_win, workers[27]), (b_win, workers[9]), (a_win, workers[2]), (a_win, workers[7])],
        ),
        ({a_win: 0.3, b_win: 0.7}, [(b_win, workers[1]), (b_win, workers[27]), (a_win, workers[15])]),
        ({a_win: 0.5, b_win: 0.5}, [(a_win, workers[11]), (b_win, workers[12])]),
        ({a_win: 0.8, b_win: 0.2}, [(a_win, workers[10]), (b_win, workers[3]), (a_win, workers[7])]),
        ({a_win: 1.0, b_win: 0.0}, [(a_win, workers[19]), (a_win, workers[3]), (a_win, workers[20])]),
    ], None

    results, worker_weights = client.launch_sbs(task_spec, None, input_objects, control_objects, None, None)  # noqa

    # expected swaps for pairs
    expected_input_objects_swapped = [
        (
            objects.Image(url=f'https://storage.net/{i}.jpg'),
            objects.Audio(url=f'https://storage.net/{a}.wav'),
            objects.Text(text=f'text {a}'),
            objects.Audio(url=f'https://storage.net/{b}.wav'),
            objects.Text(text=f'text {b}'),
        )
        for i, (a, b) in enumerate([(0, 'a'), ('b', 1), (2, 'c'), ('d', 3), ('e', 4)])
    ]
    expected_control_objects_swapped = [
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
    ]

    launch.assert_called_with(
        task_spec=task_spec,
        params=None,
        input_objects=expected_input_objects_swapped,
        control_objects=expected_control_objects_swapped,
        client=None,
        interactive=None,
        name=None,
    )

    # results for un-swapped pairs
    assert results == [
        (
            {a_win: 0.9, b_win: 0.1},
            [(b_win, workers[27]), (b_win, workers[9]), (a_win, workers[2]), (a_win, workers[7])],
        ),
        ({b_win: 0.3, a_win: 0.7}, [(a_win, workers[1]), (a_win, workers[27]), (b_win, workers[15])]),
        ({a_win: 0.5, b_win: 0.5}, [(a_win, workers[11]), (b_win, workers[12])]),
        ({b_win: 0.8, a_win: 0.2}, [(b_win, workers[10]), (a_win, workers[3]), (b_win, workers[7])]),
        ({b_win: 1.0, a_win: 0.0}, [(b_win, workers[19]), (b_win, workers[3]), (b_win, workers[20])]),
    ]
