import datetime
from typing import List, Optional

import toloka.client as toloka

from crowdom import experts, mapping, objects, pricing

from .. import lib


def test_training_is_suitable():
    config = pricing.TrainingConfig(
        max_assignment_duration=datetime.timedelta(seconds=600),
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
    )
    training = toloka.Training(
        assignment_max_duration_seconds=600,
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
        status=toloka.Training.Status.OPEN,
    )
    assert experts.training_is_suitable(training, config.get_task_duration_hint())


def test_training_is_not_suitable():
    config = pricing.TrainingConfig(
        max_assignment_duration=datetime.timedelta(seconds=600),
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
    )

    for training in (
        toloka.Training(
            assignment_max_duration_seconds=60,
            training_tasks_in_task_suite_count=10,
            task_suites_required_to_pass=1,
            status=toloka.Training.Status.OPEN,
        ),
        toloka.Training(
            assignment_max_duration_seconds=6000,
            training_tasks_in_task_suite_count=10,
            task_suites_required_to_pass=1,
            status=toloka.Training.Status.OPEN,
        ),
        toloka.Training(
            assignment_max_duration_seconds=600,
            training_tasks_in_task_suite_count=10,
            task_suites_required_to_pass=1,
            status=toloka.Training.Status.CLOSED,
        ),
    ):
        assert not experts.training_is_suitable(training, config.get_task_duration_hint())


class TolokaClientTrainingStub(lib.TolokaClientCallRecorderStub):
    def __init__(self, trainings: List[toloka.Training]):
        super(TolokaClientTrainingStub, self).__init__()
        self.trainings = trainings

    def find_trainings(
        self,
        project_id: str,
        status: toloka.Training.Status,
        sort: toloka.search_requests.TrainingSortItems,
        limit: Optional[int],
    ) -> toloka.search_results.TrainingSearchResult:
        super(TolokaClientTrainingStub, self).find_trainings(project_id, status, sort, limit)
        return toloka.search_results.TrainingSearchResult(items=[t for t in self.trainings if t.status == status])


def test_find_training():
    trainings = [
        toloka.Training(status=toloka.Training.Status.OPEN, created=datetime.datetime(year=2021, month=12, day=29)),
        toloka.Training(status=toloka.Training.Status.CLOSED, created=datetime.datetime(year=2021, month=12, day=30)),
        toloka.Training(status=toloka.Training.Status.OPEN, created=datetime.datetime(year=2021, month=12, day=28)),
    ]
    stub = TolokaClientTrainingStub(trainings)
    assert experts.find_training('fake', stub) == trainings[1]


def test_find_training_not_exists():
    stub = TolokaClientTrainingStub([])
    assert experts.find_training('fake', stub) is None


def test_create_training():
    config = pricing.TrainingConfig(
        max_assignment_duration=datetime.timedelta(seconds=600),
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
    )
    stub = TolokaClientTrainingStub([])

    training = experts.create_training('fake', 'fake training', config, stub)  # noqa
    expected_training = toloka.Training(
        project_id='fake',
        private_name='fake training',
        may_contain_adult_content=True,
        assignment_max_duration_seconds=600,
        mix_tasks_in_creation_order=True,
        shuffle_tasks_in_task_suite=True,
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
        retry_training_after_days=30,
        inherited_instructions=True,
    )
    assert training == expected_training

    assert stub.calls == [('create_training', (expected_training,))]


def test_add_training_tasks():
    solutions = [
        ((objects.Image(url='1.jpg'),), (lib.ImageClass(lib.cat),)),
        ((objects.Image(url='2.jpg'),), (lib.ImageClass(lib.dog),)),
    ]
    comments = [objects.Text(text='a cat'), objects.Text(text='a dog')]
    stub = TolokaClientTrainingStub([])
    experts.add_training_tasks(
        training_id='fake',
        task_mapping=lib.image_classification_mapping,
        solutions=solutions,
        comments=comments,
        client=stub,
    )  # noqa
    assert stub.calls == [
        (
            'create_tasks',
            (
                [
                    toloka.Task(
                        pool_id='fake',
                        input_values={'image_url': '1.jpg', 'id': mapping.TaskID(solutions[0][0]).id},
                        known_solutions=[toloka.task.BaseTask.KnownSolution(output_values={'choice': 'cat'})],
                        message_on_unknown_solution='a cat',
                    ),
                    toloka.Task(
                        pool_id='fake',
                        input_values={'image_url': '2.jpg', 'id': mapping.TaskID(solutions[1][0]).id},
                        known_solutions=[toloka.task.BaseTask.KnownSolution(output_values={'choice': 'dog'})],
                        message_on_unknown_solution='a dog',
                    ),
                ],
            ),
        )
    ]
