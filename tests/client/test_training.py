from copy import copy, deepcopy
from datetime import timedelta
import logging
import pytest
from typing import List, Optional, Callable

import toloka.client as toloka

from crowdom import base, client, mapping, objects, pricing, task_spec as spec
from .. import lib

compatible_training_id = 'compatible-training-id'
incompatible_training_id = 'incompatible-training-id'
new_training_id = 'new-training-id'


@pytest.fixture
def lang() -> str:
    return 'RU'


@pytest.fixture
def new_solutions() -> List[mapping.TaskSingleSolution]:
    return [
        ((objects.Image(url='1.jpg'),), (lib.ImageClass(lib.cat),)),
        ((objects.Image(url='2.jpg'),), (lib.ImageClass(lib.dog),)),
    ]


@pytest.fixture
def new_comments() -> List[objects.Text]:
    return [objects.Text(text='a cat'), objects.Text(text='a dog')]


@pytest.fixture
def existing_solutions() -> List[mapping.TaskSingleSolution]:
    return [
        ((objects.Image(url='3.jpg'),), (lib.ImageClass(lib.crow),)),
        ((objects.Image(url='4.jpg'),), (lib.ImageClass(lib.cat),)),
        ((objects.Image(url='5.jpg'),), (lib.ImageClass(lib.dog),)),
        ((objects.Image(url='6.jpg'),), (lib.ImageClass(lib.cat),)),
        ((objects.Image(url='7.jpg'),), (lib.ImageClass(lib.dog),)),
    ]


@pytest.fixture
def existing_comments() -> List[objects.Text]:
    return [
        objects.Text(text='a crow'),
        objects.Text(text='a cat'),
        objects.Text(text='a dog'),
        objects.Text(text='a cat'),
        objects.Text(text='a crow'),
    ]


@pytest.fixture
def task_spec(lang: str) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(
        task_spec=base.TaskSpec(
            function=base.ClassificationFunction(
                inputs=(objects.Image,),
                cls=lib.ImageClass,
            ),
            id='cats-and-dogs',
            name=base.LocalizedString({lang: 'Определите животное', base.DEFAULT_LANG: 'Identify the animal'}),
            description=base.LocalizedString({lang: 'Определите, какое животное на картинке'}),
            instruction=base.LocalizedString({lang: 'Выберите, какое животное на картинке'}),
        ),
        lang=lang,
    )


@pytest.fixture
def training_config() -> pricing.TrainingConfig:
    return pricing.TrainingConfig(
        max_assignment_duration=timedelta(seconds=600),
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
    )


@pytest.fixture
def compatible_training() -> toloka.Training:
    return toloka.Training(
        id=compatible_training_id,
        project_id='fake',
        private_name='Training for cats-and-dogs and language RU',
        status=toloka.Training.Status.OPEN,
        may_contain_adult_content=True,
        assignment_max_duration_seconds=600,
        mix_tasks_in_creation_order=True,
        shuffle_tasks_in_task_suite=True,
        training_tasks_in_task_suite_count=10,
        task_suites_required_to_pass=1,
        retry_training_after_days=30,
        inherited_instructions=True,
    )


@pytest.fixture
def incompatible_training(compatible_training: toloka.Training) -> toloka.Training:
    training = copy(compatible_training)
    training.id = incompatible_training_id
    training.assignment_max_duration_seconds = 60
    training.task_suites_required_to_pass = 5
    return training


@pytest.fixture
def closed_training(compatible_training: toloka.Training) -> toloka.Training:
    training = copy(compatible_training)
    training.id = incompatible_training_id
    training.status = toloka.Training.Status.CLOSED
    return training


def generate_tasks(
    task_spec: spec.PreparedTaskSpec,
    solutions: List[mapping.TaskSingleSolution],
    comments: List[objects.Text],
    pool_id: Optional[str] = None,
) -> List[toloka.Task]:
    return [
        toloka.Task(
            pool_id=pool_id,
            input_values=task_spec.task_mapping.toloka_values(inputs, output=False),
            known_solutions=[
                toloka.task.BaseTask.KnownSolution(
                    output_values=task_spec.task_mapping.toloka_values(outputs, output=True)
                )
            ],
            message_on_unknown_solution=comment.text,
        )
        for (inputs, outputs), comment in zip(solutions, comments)
    ]


@pytest.fixture
def new_tasks(
    task_spec: spec.PreparedTaskSpec,
    new_solutions: List[mapping.TaskSingleSolution],
    new_comments: List[objects.Text],
) -> List[toloka.Task]:
    return generate_tasks(task_spec, new_solutions, new_comments)


@pytest.fixture
def existing_tasks(
    task_spec: spec.PreparedTaskSpec,
    existing_solutions: List[mapping.TaskSingleSolution],
    existing_comments: List[objects.Text],
) -> List[toloka.Task]:
    return generate_tasks(task_spec, existing_solutions, existing_comments, incompatible_training_id)


class TolokaClientExpertsStub(lib.TolokaClientCallRecorderStub):
    def __init__(self, trainings: List[toloka.Training], tasks: Optional[List[toloka.Task]] = None):
        super(TolokaClientExpertsStub, self).__init__()
        self.trainings = trainings
        self.project = None
        self.tasks = tasks

    def get_projects(self, status: str) -> List[toloka.Project]:
        super(TolokaClientExpertsStub, self).get_projects(status)
        if self.project is None:
            return []
        return [self.project]

    def find_trainings(
        self,
        project_id: str,
        status: toloka.Training.Status,
        sort: toloka.search_requests.TrainingSortItems,
        limit: Optional[int],
    ) -> toloka.search_results.TrainingSearchResult:
        super(TolokaClientExpertsStub, self).find_trainings(project_id, status, sort, limit)
        assert self.project is not None
        assert project_id == self.project.id
        return toloka.search_results.TrainingSearchResult(items=[t for t in self.trainings if t.status == status])

    def create_training(self, training: toloka.Training) -> toloka.Training:
        training = copy(super(TolokaClientExpertsStub, self).create_training(training))
        training.id = new_training_id
        return training

    def get_tasks(self, pool_id: str) -> List[toloka.Task]:
        return deepcopy(self.tasks)

    def create_project(self, project: toloka.Project) -> toloka.Project:
        super(TolokaClientExpertsStub, self).create_project(project)
        assert self.project is None
        project.id = 'fake'
        self.project = project
        return self.project


@pytest.fixture
def create_stub(existing_tasks: List[toloka.Task]):
    return lambda trainings: TolokaClientExpertsStub(trainings, existing_tasks)


@pytest.fixture
def create_stub_with_insufficient_tasks(existing_tasks: List[toloka.Task]):
    return lambda trainings: TolokaClientExpertsStub(trainings, existing_tasks[:1])


def assign_tasks_to_training(
    tasks: List[toloka.Task],
    old_training_id: Optional[str],
    new_training_id: str,
) -> List[toloka.Task]:
    result = deepcopy(tasks)
    for task in result:
        assert task.pool_id == old_training_id
        task.pool_id = new_training_id
    return result


class TestCreateTraining:
    def test_not_reusing_trainings(
        self,
        task_spec: spec.PreparedTaskSpec,
        training_config: pricing.TrainingConfig,
        compatible_training: toloka.Training,
        new_solutions: List[mapping.TaskSingleSolution],
        new_comments: List[objects.Text],
        new_tasks: List[toloka.Task],
    ):
        created_tasks = assign_tasks_to_training(new_tasks, None, new_training_id)
        for append_to_existing, trainings in [(True, []), (False, []), (False, [compatible_training])]:
            stub = TolokaClientExpertsStub(trainings)
            client.define_task(task_spec, stub)  # noqa
            client.create_training(
                task_spec,
                new_solutions,
                new_comments,
                stub,  # noqa
                training_config,
                append_to_existing=append_to_existing,
            )
            assert stub.calls == [
                ('get_projects', ('ACTIVE',)),
                ('create_project', (stub.project,)),
                ('get_projects', ('ACTIVE',)),
                (
                    'find_trainings',
                    (
                        'fake',
                        toloka.Training.Status.OPEN,
                        toloka.search_requests.TrainingSortItems(
                            items=[
                                toloka.search_requests.TrainingSortItems.SortItem(
                                    field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                    order=toloka.search_requests.SortOrder.DESCENDING,
                                )
                            ]
                        ),
                        1,
                    ),
                ),
                (
                    'find_trainings',
                    (
                        'fake',
                        toloka.Training.Status.CLOSED,
                        toloka.search_requests.TrainingSortItems(
                            items=[
                                toloka.search_requests.TrainingSortItems.SortItem(
                                    field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                    order=toloka.search_requests.SortOrder.DESCENDING,
                                )
                            ]
                        ),
                        1,
                    ),
                ),
                (
                    'create_training',
                    (
                        toloka.Training(
                            project_id='fake',
                            private_name='Training for task "cats-and-dogs" in RU',
                            may_contain_adult_content=True,
                            assignment_max_duration_seconds=600,
                            mix_tasks_in_creation_order=True,
                            shuffle_tasks_in_task_suite=True,
                            training_tasks_in_task_suite_count=10,
                            task_suites_required_to_pass=1,
                            retry_training_after_days=30,
                            inherited_instructions=True,
                        ),
                    ),
                ),
                ('create_tasks', (created_tasks,)),
                ('open_training', (new_training_id,)),
            ]

    def test_reusing_compatible_training(
        self,
        task_spec: spec.PreparedTaskSpec,
        training_config: pricing.TrainingConfig,
        compatible_training: toloka.Training,
        new_solutions: List[mapping.TaskSingleSolution],
        new_comments: List[objects.Text],
        new_tasks: List[toloka.Task],
    ):
        created_tasks = assign_tasks_to_training(new_tasks, None, compatible_training_id)
        stub = TolokaClientExpertsStub([compatible_training])
        client.define_task(task_spec, stub)  # noqa
        client.create_training(
            task_spec, new_solutions, new_comments, stub, training_config, append_to_existing=True  # noqa
        )
        assert stub.calls == [
            ('get_projects', ('ACTIVE',)),
            ('create_project', (stub.project,)),
            ('get_projects', ('ACTIVE',)),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            ('create_tasks', (created_tasks,)),
            ('open_training', (compatible_training_id,)),
        ]

    def test_reusing_tasks_from_incompatible_training(
        self,
        task_spec: spec.PreparedTaskSpec,
        training_config: pricing.TrainingConfig,
        incompatible_training: toloka.Training,
        closed_training: toloka.Training,
        new_solutions: List[mapping.TaskSingleSolution],
        new_comments: List[objects.Text],
        new_tasks: List[toloka.Task],
        existing_tasks: List[toloka.Task],
        create_stub: Callable,
    ):
        for training in (incompatible_training, closed_training):
            old_tasks = assign_tasks_to_training(existing_tasks, training.id, new_training_id)
            created_tasks = assign_tasks_to_training(new_tasks, None, new_training_id)
            stub = create_stub([training])
            client.define_task(task_spec, stub)  # noqa
            client.create_training(
                task_spec, new_solutions, new_comments, stub, training_config, append_to_existing=True  # noqa
            )
            assert stub.calls == [
                ('get_projects', ('ACTIVE',)),
                ('create_project', (stub.project,)),
                ('get_projects', ('ACTIVE',)),
                (
                    'find_trainings',
                    (
                        'fake',
                        toloka.Training.Status.OPEN,
                        toloka.search_requests.TrainingSortItems(
                            items=[
                                toloka.search_requests.TrainingSortItems.SortItem(
                                    field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                    order=toloka.search_requests.SortOrder.DESCENDING,
                                )
                            ]
                        ),
                        1,
                    ),
                ),
                (
                    'find_trainings',
                    (
                        'fake',
                        toloka.Training.Status.CLOSED,
                        toloka.search_requests.TrainingSortItems(
                            items=[
                                toloka.search_requests.TrainingSortItems.SortItem(
                                    field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                    order=toloka.search_requests.SortOrder.DESCENDING,
                                )
                            ]
                        ),
                        1,
                    ),
                ),
                (
                    'create_training',
                    (
                        toloka.Training(
                            project_id='fake',
                            private_name='Training for task "cats-and-dogs" in RU',
                            may_contain_adult_content=True,
                            assignment_max_duration_seconds=600,
                            mix_tasks_in_creation_order=True,
                            shuffle_tasks_in_task_suite=True,
                            training_tasks_in_task_suite_count=10,
                            task_suites_required_to_pass=1,
                            retry_training_after_days=30,
                            inherited_instructions=True,
                        ),
                    ),
                ),
                ('create_tasks', (old_tasks,)),
                ('create_tasks', (created_tasks,)),
                ('open_training', (new_training_id,)),
            ]


class TestFindTraining:
    def test_exists(
        self,
        task_spec: spec.PreparedTaskSpec,
        compatible_training: toloka.Training,
    ):
        stub = TolokaClientExpertsStub([compatible_training])
        client.define_task(task_spec, stub)  # noqa
        params = lib.get_params(seconds=6, training_score=60)
        training_requirement = client.find_training_requirement('fake', task_spec, stub, params)  # noqa
        assert stub.calls == [
            ('get_projects', ('ACTIVE',)),
            ('create_project', (stub.project,)),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
        ]

        assert training_requirement == toloka.pool.QualityControl.TrainingRequirement(
            training_pool_id=compatible_training_id, training_passing_skill_value=60
        )

    def test_no_trainings(
        self,
        task_spec: spec.PreparedTaskSpec,
        compatible_training: toloka.Training,
    ):
        stub = TolokaClientExpertsStub([])
        client.define_task(task_spec, stub)  # noqa
        params = lib.get_params(seconds=6, training_score=60)
        training_requirement = client.find_training_requirement('fake', task_spec, stub, params)  # noqa
        assert stub.calls == [
            ('get_projects', ('ACTIVE',)),
            ('create_project', (stub.project,)),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
        ]

        assert training_requirement is None

    def test_recreate(
        self,
        task_spec: spec.PreparedTaskSpec,
        incompatible_training: toloka.Training,
        create_stub: Callable,
        existing_tasks: List[toloka.Task],
    ):
        stub = create_stub([incompatible_training])
        client.define_task(task_spec, stub)  # noqa
        params = lib.get_params(seconds=6, training_score=60)
        training_requirement = client.find_training_requirement('fake', task_spec, stub, params)  # noqa
        old_tasks = assign_tasks_to_training(existing_tasks, incompatible_training.id, new_training_id)
        assert stub.calls == [
            ('get_projects', ('ACTIVE',)),
            ('create_project', (stub.project,)),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            (
                'create_training',
                (
                    toloka.Training(
                        project_id='fake',
                        private_name='Training for task "cats-and-dogs" in RU',
                        may_contain_adult_content=True,
                        assignment_max_duration_seconds=120,
                        mix_tasks_in_creation_order=True,
                        shuffle_tasks_in_task_suite=True,
                        training_tasks_in_task_suite_count=2,
                        task_suites_required_to_pass=3,
                        retry_training_after_days=30,
                        inherited_instructions=True,
                    ),
                ),
            ),
            ('create_tasks', (old_tasks,)),
            ('open_training', (new_training_id,)),
        ]

        assert training_requirement == toloka.pool.QualityControl.TrainingRequirement(
            training_pool_id=new_training_id, training_passing_skill_value=60
        )

    def test_recreate_failed(
        self,
        task_spec: spec.PreparedTaskSpec,
        incompatible_training: toloka.Training,
        create_stub_with_insufficient_tasks: Callable,
        caplog,
    ):
        stub = create_stub_with_insufficient_tasks([incompatible_training])
        client.define_task(task_spec, stub)  # noqa
        params = lib.get_params(seconds=6, training_score=60)

        with caplog.at_level(logging.WARNING):
            caplog.clear()
            training_requirement = client.find_training_requirement('fake', task_spec, stub, params)  # noqa
            assert caplog.record_tuples == [
                (
                    'crowdom.client.training',
                    logging.WARNING,
                    'Found outdated training incompatible-training-id for task "cats-and-dogs" in RU '
                    'in Toloka project fake. Failed to recreate training due to a change in task duration hint, '
                    'using outdated version. Consider the following problem: "You do not have enough tasks for this '
                    'training. Expected at least 5 tasks for this parameters, got 1".',
                )
            ]

        assert stub.calls == [
            ('get_projects', ('ACTIVE',)),
            ('create_project', (stub.project,)),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'fake',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(
                        items=[
                            toloka.search_requests.TrainingSortItems.SortItem(
                                field=toloka.search_requests.TrainingSortItems.SortItem.SortField.CREATED,
                                order=toloka.search_requests.SortOrder.DESCENDING,
                            )
                        ]
                    ),
                    1,
                ),
            ),
        ]

        assert training_requirement == toloka.pool.QualityControl.TrainingRequirement(
            training_pool_id=incompatible_training_id, training_passing_skill_value=60
        )
