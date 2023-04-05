import datetime
from time import sleep
from typing import Tuple

from pytest import skip
import toloka.client as toloka

from crowdom import base, bots, classification_loop, datasource, client, pricing, task_spec as spec

from .. import util


def test_only_left(
    toloka_client: toloka.TolokaClient,
    task_duration_hint: datetime.timedelta,
    sbs_task_spec_p: spec.PreparedTaskSpec,
    sbs_config_and_params: Tuple[pricing.PoolPricingConfig, classification_loop.Params],
):
    client.define_task(sbs_task_spec_p, toloka_client)
    pricing_config, params = sbs_config_and_params
    prj = client.check_project(sbs_task_spec_p, toloka_client)
    control_objects = datasource.read_tasks_from_json_file(
        'control-tasks.json', sbs_task_spec_p.task_mapping, has_solutions=True
    )
    solved_tasks = datasource.read_tasks_from_json_file(
        'bots-tasks.json', sbs_task_spec_p.task_mapping, has_solutions=True
    )
    input_objects = datasource.read_tasks_from_json_file('tasks.json', sbs_task_spec_p.task_mapping)
    assert not list(
        toloka_client.get_pools(project_id=prj.id, status='OPEN')
    ), 'Unexpected pools found before sbs_launch'
    launch_thread = bots.ThreadWithReturnValue(
        target=client.launch_sbs,
        args=(
            sbs_task_spec_p,
            client.ClassificationLaunchParams(
                launch_params=client.LaunchParams(pricing_config=pricing_config, task_duration_hint=task_duration_hint),
                params=params,
            ),
            input_objects,
            control_objects,
            toloka_client,
        ),
    )

    launch_thread.start()

    worker_types = [
        (bots.SbSWorkerConfig(speed=bots.WorkerSpeed.SLOW, quality=0.95, left_bias=0.0), 10),
        (bots.SbSWorkerConfig(speed=bots.WorkerSpeed.MEDIUM, quality=0.9, left_bias=0.0), 10),
        (bots.SbSWorkerConfig(speed=bots.WorkerSpeed.FAST, quality=0.8, left_bias=0.0), 10),
        (bots.SbSWorkerConfig(speed=bots.WorkerSpeed.POOR, quality=0.5, left_bias=0.0), 10),
        (bots.SbSWorkerConfig(speed=bots.WorkerSpeed.RAND, quality=1 / 3, left_bias=0.0), 10),
    ]

    solutions = bots.create_tasks_info_dict(sbs_task_spec_p, solved_tasks)

    while not list(toloka_client.get_pools(project_id=prj.id, status='OPEN')):
        sleep(10)

    pools = list(toloka_client.get_pools(project_id=prj.id, status='OPEN'))

    assert len(pools) == 1, 'More than one pool created in sbs_launch'

    pool = pools[0]

    wg = bots.WorkerGroup(
        pool.id, sbs_task_spec_p, task_duration_hint, worker_types, solutions, worker_cls=bots.SbSWorker
    )
    wg.start()

    raw_results, worker_weights = launch_thread.join()
    wg.stop()

    results = client.ClassificationResults(input_objects, raw_results, sbs_task_spec_p, worker_weights)

    counts = results.predict()['result'].value_counts().to_dict()
    q = len(input_objects) / len(counts)
    for value in counts.values():
        assert 0.8 * q <= value <= 1.2 * q, f'Expected {0.8 * q} <= {value} <= {1.2 * q}, got skewed results'

    util.check_worker_swaps(wg.workers)


@skip(
    reason='cannot achieve both: 1.loop convergence - enough right answers to control tasks and'
    '2. reliably produce only "b" results in original terms, probably due to asymmetric bias matrix'
)
def test_only_b(
    toloka_client: toloka.TolokaClient,
    task_duration_hint: datetime.timedelta,
    sbs_task_spec_p: spec.PreparedTaskSpec,
    sbs_config_and_params: Tuple[pricing.PoolPricingConfig, classification_loop.Params],
):
    client.define_task(sbs_task_spec_p, toloka_client)
    pricing_config, params = sbs_config_and_params
    prj = client.check_project(sbs_task_spec_p, toloka_client)
    control_objects = datasource.read_tasks_from_json_file(
        'control-tasks.json', sbs_task_spec_p.task_mapping, has_solutions=True
    )
    solved_tasks = datasource.read_tasks_from_json_file(
        'bots-tasks.json', sbs_task_spec_p.task_mapping, has_solutions=True
    )
    input_objects = datasource.read_tasks_from_json_file('tasks.json', sbs_task_spec_p.task_mapping)
    assert not list(
        toloka_client.get_pools(project_id=prj.id, status='OPEN')
    ), 'Unexpected pools found before sbs_launch'
    launch_thread = bots.ThreadWithReturnValue(
        target=client.launch_sbs,
        args=(
            sbs_task_spec_p,
            client.ClassificationLaunchParams(
                launch_params=client.LaunchParams(pricing_config=pricing_config, task_duration_hint=task_duration_hint),
                params=params,
            ),
            input_objects,
            control_objects,
            toloka_client,
        ),
    )

    launch_thread.start()

    worker_types = [
        (
            bots.SbSWorkerConfig(
                speed=bots.WorkerSpeed.SLOW, quality=0.95, left_bias=0.0, treat_bias_as_original_a=True
            ),
            10,
        ),
        (
            bots.SbSWorkerConfig(
                speed=bots.WorkerSpeed.MEDIUM, quality=0.9, left_bias=0.0, treat_bias_as_original_a=True
            ),
            10,
        ),
        (
            bots.SbSWorkerConfig(
                speed=bots.WorkerSpeed.FAST, quality=0.8, left_bias=0.0, treat_bias_as_original_a=True
            ),
            10,
        ),
        (
            bots.SbSWorkerConfig(
                speed=bots.WorkerSpeed.POOR, quality=0.5, left_bias=0.0, treat_bias_as_original_a=True
            ),
            10,
        ),
        (
            bots.SbSWorkerConfig(
                speed=bots.WorkerSpeed.RAND, quality=1 / 3, left_bias=0.0, treat_bias_as_original_a=True
            ),
            10,
        ),
    ]

    solutions = bots.create_tasks_info_dict(sbs_task_spec_p, solved_tasks)

    while not list(toloka_client.get_pools(project_id=prj.id, status='OPEN')):
        sleep(10)

    pools = list(toloka_client.get_pools(project_id=prj.id, status='OPEN'))

    assert len(pools) == 1, 'More than one pool created in sbs_launch'

    pool = pools[0]

    wg = bots.WorkerGroup(
        pool.id, sbs_task_spec_p, task_duration_hint, worker_types, solutions, worker_cls=bots.SbSWorker
    )
    wg.start()

    raw_results, worker_weights = launch_thread.join()
    wg.stop()

    results = client.ClassificationResults(input_objects, raw_results, sbs_task_spec_p, worker_weights)

    assert (results.predict()['result'] == 'b').all(), 'Not all results are "b"'

    util.check_worker_swaps(wg.workers)
