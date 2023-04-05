from time import sleep
from typing import List

import toloka.client as toloka

from crowdom import bots


def wait_for_loop_iteration(toloka_client: toloka.TolokaClient, pool_id: str, expected_overlap: int):
    # marker for loop iteration finish
    while True:
        tasks = list(toloka_client.get_tasks(pool_id))
        all_tasks_completed = True
        for task in tasks:
            if task.known_solutions is None and task.overlap != expected_overlap:
                all_tasks_completed = False
                break
        if all_tasks_completed:
            break
        else:
            sleep(60)
            continue

    while toloka_client.get_pool(pool_id).status != toloka.pool.Pool.Status.OPEN:
        sleep(10)

    tasks = list(toloka_client.get_tasks(pool_id))

    for task in tasks:
        assert task.known_solutions is not None or task.overlap == expected_overlap, 'Unexpected overlap'


def check_worker_swaps(workers: List[bots.SbSWorker]):
    for worker in workers:
        if worker.stats['not_swapped'] > 0 and worker.stats['swapped'] > 0:
            assert 0.4 <= worker.stats['not_swapped'] / worker.stats['swapped'] <= 2.5, 'Got skewed inputs for worker'
        else:
            assert (
                worker.stats['not_swapped'] + worker.stats['swapped'] <= 30
            ), 'Got too many one-sided inputs for worker'
