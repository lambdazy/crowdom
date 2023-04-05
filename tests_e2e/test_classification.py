import datetime
from random import shuffle
from time import sleep
from typing import List, Tuple

import toloka.client as toloka

from crowdom import base, bots, classification_loop, client, mapping, pricing, task_spec as spec


def test_classification(
    toloka_client: toloka.TolokaClient,
    task_duration_hint: datetime.timedelta,
    task_spec_p: spec.PreparedTaskSpec,
    config_and_params: Tuple[pricing.PoolPricingConfig, classification_loop.Params],
    input_objects: List[mapping.Objects],
    control_objects: List[mapping.TaskSingleSolution],
    solved_tasks: List[mapping.TaskSingleSolution],
):
    initial_balance = toloka_client.get_requester().balance
    client.define_task(task_spec_p, toloka_client)
    pricing_config, params = config_and_params
    params.overlap.max_overlap = 4
    prj = client.check_project(task_spec_p, toloka_client)
    assert not list(toloka_client.get_pools(project_id=prj.id, status='OPEN')), 'Unexpected pools found before launch'
    launch_thread = bots.ThreadWithReturnValue(
        target=client.launch,
        args=(
            task_spec_p,
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
    animal = task_spec_p.function.cls
    worker_types = [
        (bots.WorkerConfig(bots.WorkerSpeed.SLOW, 0.95, obj_cls=animal), 8),
        (bots.WorkerConfig(bots.WorkerSpeed.MEDIUM, 0.9, obj_cls=animal), 10),
        (bots.WorkerConfig(bots.WorkerSpeed.FAST, 0.8, obj_cls=animal), 5),
        (bots.WorkerConfig(bots.WorkerSpeed.POOR, 0.5, obj_cls=animal), 4),
        (bots.WorkerConfig(bots.WorkerSpeed.RAND, 1 / 3, obj_cls=animal), 7),
    ]

    shuffle(solved_tasks)
    task_count = len(solved_tasks)
    complexity = {
        bots.TaskComplexity.EASY: 3 * task_count // 8,
        bots.TaskComplexity.OK: task_count // 2,
        bots.TaskComplexity.HARD: task_count // 8,
    }
    solutions = bots.create_tasks_info_dict(task_spec_p, solved_tasks, tasks_complexity=complexity)

    while not list(toloka_client.get_pools(project_id=prj.id, status='OPEN')):
        sleep(10)

    pools = list(toloka_client.get_pools(project_id=prj.id, status='OPEN'))

    assert len(pools) == 1, 'More than one pool created in launch'

    pool = pools[0]

    wg = bots.WorkerGroup(pool.id, task_spec_p, task_duration_hint, worker_types, solutions)
    wg.start()

    raw_results, worker_weights = launch_thread.join()
    wg.stop()

    results = client.ClassificationResults(input_objects, raw_results, task_spec_p, worker_weights)

    id_to_worker = {worker.id: worker for worker in wg.workers}

    input_task_ids = [task_spec_p.task_mapping.task_id(task).id for task in input_objects]

    df = results.df

    df['task_id'] = df.apply(lambda row: bots.get_task_id(task_spec_p, row), axis=1)
    df['speed'] = df[client.ClassificationResults.WORKER_FIELD].apply(
        lambda worker_id: id_to_worker[worker_id].config.speed.value
    )
    df['quality'] = df[client.ClassificationResults.WORKER_FIELD].apply(
        lambda worker_id: id_to_worker[worker_id].config.quality
    )
    df['complexity'] = df['task_id'].apply(lambda task_id: solutions[task_id].complexity)
    df['golden'] = df['task_id'].apply(lambda task_id: solutions[task_id].solution[base.CLASS_TASK_FIELD])

    unique_tasks = df.drop_duplicates('task_id')
    assert set(df['task_id'].unique()) == set(input_task_ids), 'Some tasks are missing in the results'

    easy, ok, hard = [
        df[df['complexity'] == complexity_level.value].drop_duplicates('task_id')
        for complexity_level in [bots.TaskComplexity.EASY, bots.TaskComplexity.OK, bots.TaskComplexity.HARD]
    ]

    assert (
        easy[client.ClassificationResults.CONFIDENCE_FIELD].mean()
        >= ok[client.ClassificationResults.CONFIDENCE_FIELD].mean()
        >= hard[client.ClassificationResults.CONFIDENCE_FIELD].mean()
    ), 'Mean confidence levels are not sorted according to task complexity'

    assert (
        easy[client.ClassificationResults.OVERLAP_FIELD].mean()
        <= ok[client.ClassificationResults.OVERLAP_FIELD].mean()
        <= hard[client.ClassificationResults.OVERLAP_FIELD].mean()
    ), 'Mean overlap levels are not sorted according to task complexity'

    assert (
        df[df[client.ClassificationResults.OVERLAP_FIELD] < params.overlap.max_overlap][
            client.ClassificationResults.CONFIDENCE_FIELD
        ]
        >= params.overlap.confidence
    ).all(), 'Expected confidence not reached, but overlap is not max'

    assert (
        unique_tasks[client.ClassificationResults.RESULT_FIELD] == unique_tasks['golden']
    ).mean() >= 0.75, 'Poor result quality'

    assert (
        (easy[client.ClassificationResults.RESULT_FIELD] == easy['golden']).mean()
        >= (ok[client.ClassificationResults.RESULT_FIELD] == ok['golden']).mean()
        >= (hard[client.ClassificationResults.RESULT_FIELD] == hard['golden']).mean()
    ), 'Mean accuracy levels are not sorted according to task complexity'

    assert not (df['speed'] == bots.WorkerSpeed.RAND.value).any(), 'Some RAND frauders got into results'

    quality_levels = sorted(df['quality'].unique())
    weight_for_level = [
        df[df['quality'] == q]
        .drop_duplicates(client.ClassificationResults.WORKER_FIELD)[client.ClassificationResults.WORKER_WEIGHT_FIELD]
        .mean()
        for q in quality_levels
    ]

    assert len(quality_levels) >= 2, 'Not enough different quality levels'
    assert sorted(weight_for_level) == weight_for_level, 'Mean worker weights not increasing with quality increase'
    formula = pricing.PoolPriceFormula(len(input_objects), pricing_config, params.overlap)
    spent = initial_balance - toloka_client.get_requester().balance
    assert formula.min_total_price_precise <= spent <= formula.max_total_price_precise, 'Inaccurate price estimate'
