from datetime import timedelta
from time import sleep
from threading import Thread
from typing import List, Tuple

from toloka.client.exceptions import IncorrectActionsApiError, DoesNotExistApiError

from crowdom import bots, classification_loop, client, mapping, pricing, task_spec as spec

from . import util


def test_restrictions(
    register: bots.NDARegisterClient,
    toloka_client: bots.CallRecorderClient,
    task_duration_hint: timedelta,
    task_spec_p: spec.PreparedTaskSpec,
    config_and_params: Tuple[pricing.PoolPricingConfig, classification_loop.Params],
    input_objects: List[mapping.Objects],
    control_objects: List[mapping.TaskSingleSolution],
    solved_tasks: List[mapping.TaskSingleSolution],
):
    client.define_task(task_spec_p, toloka_client)

    pricing_config, params = config_and_params
    params.overlap.min_overlap = 1
    params.overlap.max_overlap = 1
    params.overlap.confidence = 0.0
    prj = client.check_project(task_spec_p, toloka_client)

    assert not list(toloka_client.get_pools(project_id=prj.id, status='OPEN')), 'Unexpected pools found before launch'

    task_count = pricing_config.real_tasks_count * 2

    launch_thread = Thread(
        target=client.launch,
        args=(
            task_spec_p,
            client.ClassificationLaunchParams(
                launch_params=client.LaunchParams(pricing_config=pricing_config, task_duration_hint=task_duration_hint),
                params=params,
            ),
            input_objects[:task_count],
            control_objects,
            bots.NDATolokaClient(toloka_client.token),
        ),
    )

    launch_thread.start()

    complexity = {bots.TaskComplexity.EASY: len(solved_tasks)}
    solutions = bots.create_tasks_info_dict(task_spec_p, solved_tasks, tasks_complexity=complexity)

    while not list(toloka_client.get_pools(project_id=prj.id, status='OPEN')):
        sleep(10)

    pools = list(toloka_client.get_pools(project_id=prj.id, status='OPEN'))

    assert len(pools) == 1, 'More than one pool created in launch'

    pool = pools[0]

    tasks = list(toloka_client.get_tasks(pool.id))

    for task in tasks:
        assert task.known_solutions is not None or task.overlap == 1, 'Task with unexpected overlap'

    worker_infos = [register.create_user() for _ in range(4)]
    animal = task_spec_p.function.cls

    fast_worker = bots.Worker(
        worker_info=worker_infos[0],
        pool_id=pool.id,
        task_spec=task_spec_p,
        task_duration_hint=task_duration_hint,
        solutions=solutions,
        config=bots.WorkerConfig(bots.WorkerSpeed.RAND, 1.0, obj_cls=animal),
    )

    fast_worker.time_policy = lambda task_count: 0

    wrong_worker = bots.Worker(
        worker_info=worker_infos[1],
        pool_id=pool.id,
        task_spec=task_spec_p,
        task_duration_hint=task_duration_hint,
        solutions=solutions,
        config=bots.WorkerConfig(bots.WorkerSpeed.FAST, 0.0, obj_cls=animal),
    )

    good_workers = [
        bots.Worker(
            worker_info=info,
            pool_id=pool.id,
            task_spec=task_spec_p,
            task_duration_hint=task_duration_hint,
            solutions=solutions,
            config=bots.WorkerConfig(bots.WorkerSpeed.FAST, 1.0, obj_cls=animal),
        )
        for info in worker_infos[2:]
    ]

    for worker in [fast_worker, wrong_worker]:
        work = worker.get_target()
        assert not work(), 'Unsuccessful attempt to solve an assignment'

    util.wait_for_loop_iteration(toloka_client, pool.id, 2)

    for worker in [fast_worker, wrong_worker]:
        try:
            worker.client.request_assignment(pool_id=worker.pool_id)
            assert False, 'Got an assignment after restriction'
        except IncorrectActionsApiError:
            pass
        except Exception as e:
            assert f'Unexpected exception: {e}'

    for worker in good_workers:
        work = worker.get_target()
        assert not work(), 'Unsuccessful attempt to solve an assignment'

    launch_thread.join()
    restrictions = list(toloka_client.get_user_restrictions())
    assert len(restrictions) == 4, 'Incorrect number of restrictions created'

    for restriction in restrictions:
        if restriction.user_id == fast_worker.id:
            assert restriction.private_comment == 'Fast submits, fraud'
            assert (
                timedelta(minutes=-5)
                <= (restriction.will_expire - restriction.created) - timedelta(days=1)
                <= timedelta(minutes=5)
            ), 'Incorrect restriction duration'
        elif restriction.user_id == wrong_worker.id:
            assert (
                restriction.private_comment == 'Control tasks: '
                f'[0, {int(0.5 * pricing_config.control_tasks_count)}) done correctly'
            )
            assert (
                timedelta(minutes=-5)
                <= (restriction.will_expire - restriction.created) - timedelta(hours=1)
                <= timedelta(minutes=5)
            ), 'Incorrect restriction duration'
        else:
            assert False, 'Unexpected worker found'
