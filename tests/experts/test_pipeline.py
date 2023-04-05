import datetime
from itertools import chain
from typing import List, Union, Dict

import toloka.client as toloka
import pytest

from crowdom import base, experts, pool as pool_config, project as project_config, worker
from crowdom.objects import Audio, Image, Text

from .. import lib


class TolokaClientStub(lib.TolokaClientIntegrationStub):
    id_to_assignment: Dict[str, toloka.Assignment]

    def __init__(self, assignments: List[toloka.Assignment], project: toloka.Project):
        self.assignments = assignments
        super(TolokaClientStub, self).__init__(assignments, [project])

    def get_assignments(
        self,
        status: Union[toloka.Assignment.Status, List[toloka.Assignment.Status]],
        pool_id: str,
    ) -> List[toloka.Assignment]:
        return self.assignments


class TestExpertsPipeline:

    dog, cat, crow = lib.dog, lib.cat, lib.crow
    ok, bad = lib.ok, lib.bad
    images = [Image(url=f'https://storage.net/{i}.jpg') for i in range(12)]
    audios = [Audio(url=f'https://storage.net/{i}.jpg') for i in range(12)]

    classification_solutions = [
        [
            (images[0], cat, ok, Text('')),
            (images[1], cat, ok, Text('ok')),
            (images[2], crow, ok, Text('unclear')),
            (images[3], dog, bad, Text('may be cat')),
        ],
        [
            (images[4], dog, bad, Text('')),
            (images[5], cat, ok, Text('persian cat')),
            (images[6], dog, bad, Text('not sure')),
            (images[7], dog, ok, Text('dog')),
        ],
        [
            (images[8], crow, ok, Text('may be pigeon')),
            (images[9], dog, bad, Text('')),
            (images[10], cat, ok, Text('')),
            (images[11], crow, ok, Text('')),
        ],
    ]
    annotation_solutions = [
        [
            (audios[0], Text('0'), ok, ok, Text('')),
            (audios[1], Text('1'), ok, ok, Text('ok')),
            (audios[2], Text('2'), ok, bad, Text('unclear')),
            (audios[3], Text('3'), bad, bad, Text('music')),
        ],
        [
            (audios[4], Text('4'), bad, bad, Text('noisy')),
            (audios[5], Text('5'), ok, ok, Text('')),
            (audios[6], Text('6'), bad, ok, Text('very quiet')),
            (audios[7], Text('7'), ok, ok, Text('')),
        ],
        [
            (audios[8], Text('8'), ok, ok, Text('')),
            (audios[9], Text('9'), bad, bad, Text('silence')),
            (audios[10], Text('10'), bad, bad, Text('')),
            (audios[11], Text('11'), ok, bad, Text('background music')),
        ],
    ]

    def test_experts_classification_pipeline_wrong_objects(self):
        stub = TolokaClientStub([], toloka.Project())
        pool_input_objects = [(image,) for image in self.images]
        flat_solutions = list(chain(*self.classification_solutions))
        pool_solution_objects = [((image,), (cls,)) for image, cls, _, _ in flat_solutions]

        for task_mapping, scenario, wrong_objects, expected_objects in [
            (
                lib.image_classification_expert_task_mapping,
                project_config.Scenario.EXPERT_LABELING_OF_TASKS,
                pool_solution_objects,
                pool_input_objects,
            ),
            (
                lib.image_classification_expert_solution_mapping,
                project_config.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS,
                pool_input_objects,
                pool_solution_objects,
            ),
        ]:

            loop = experts.ExpertPipeline(
                client=stub,  # noqa
                task_mapping=task_mapping,
                task_function=base.ClassificationFunction(inputs=(Image,), cls=lib.ImageClass),
                lang='RU',
                scenario=scenario,
            )

            with pytest.raises(AssertionError):
                loop.add_input_objects('', wrong_objects)

            loop.add_input_objects('', expected_objects)

    def test_experts_annotation_task_pipeline_wrong_objects(self):
        stub = TolokaClientStub([], toloka.Project())
        pool_input_objects = [(audio,) for audio in self.audios]
        flat_solutions = list(chain(*self.annotation_solutions))
        pool_solution_objects = [((audio,), (text,)) for audio, text, *_ in flat_solutions]

        for task_mapping, wrong_objects, expected_objects in [
            (
                lib.audio_transcription_expert_task_mapping,
                pool_solution_objects,
                pool_input_objects,
            ),
            (
                lib.audio_transcription_expert_solution_mapping,
                pool_input_objects,
                pool_solution_objects,
            ),
        ]:

            loop = experts.ExpertPipeline(
                client=stub,  # noqa
                task_mapping=task_mapping,
                task_function=base.AnnotationFunction(inputs=(Audio,), outputs=(Text,)),
                lang='RU',
                scenario=project_config.Scenario.EXPERT_LABELING_OF_TASKS,
            )

            with pytest.raises(AssertionError):
                loop.add_input_objects('', wrong_objects)

            loop.add_input_objects('', expected_objects)

    def test_experts_annotation_solution_pipeline_wrong_objects(self):
        stub = TolokaClientStub([], toloka.Project())
        pool_input_objects = [(audio,) for audio in self.audios]

        loop = experts.ExpertPipeline(
            client=stub,  # noqa
            task_mapping=lib.audio_transcription_expert_solution_mapping,
            task_function=base.AnnotationFunction(inputs=(Audio,), outputs=(Text,)),
            lang='RU',
            scenario=project_config.Scenario.EXPERT_LABELING_OF_TASKS,
        )

        flat_solutions = list(chain(*self.annotation_solutions))
        pool_solution_objects = [((audio,), (text,)) for audio, text, *_ in flat_solutions]

        with pytest.raises(AssertionError):
            loop.add_input_objects('', pool_input_objects)

        loop.add_input_objects('', pool_solution_objects)

    def test_experts_classification_task_pipeline_e2e(self):
        project = toloka.Project(
            id='project',
            task_spec=toloka.project.TaskSpec(
                input_spec=lib.image_classification_expert_task_mapping.to_toloka_input_spec(),
                output_spec=lib.image_classification_expert_task_mapping.to_toloka_output_spec(),
            ),
        )

        pool_id = 'fake pool'
        pool_cfg = pool_config.ExpertConfig(
            project_id=project.id,
            private_name=pool_id,
            reward_per_assignment=0.01,
            task_duration_hint=datetime.timedelta(seconds=10),
            real_tasks_count=4,
            worker_filter=worker.ExpertFilter([toloka.Skill(id='expert'), toloka.Skill(id='expert_RU')]),
        )

        assignments = [
            lib.create_expert_classification_assignment(expert_solutions, user_id=user_id, pool_id=pool_id)[0]
            for expert_solutions, user_id in zip(self.classification_solutions, ['bob', 'mary', 'john'])
        ]
        pool_input_objects = [(image,) for image in self.images]
        stub = TolokaClientStub(assignments, project)

        loop = experts.ExpertPipeline(
            client=stub,  # noqa
            task_mapping=lib.image_classification_expert_task_mapping,
            task_function=None,  # noqa
            lang='RU',
            scenario=project_config.Scenario.EXPERT_LABELING_OF_TASKS,
        )

        pool = loop.create_pool(pool_cfg=pool_cfg)
        loop.add_input_objects(pool.id, pool_input_objects)
        loop.loop(pool.id)
        results = loop.get_results(pool.id, pool_input_objects)
        assert stub.calls[1:] == [
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'image_url': f'https://storage.net/{index}.jpg',
                                'id': f"Image(url='https://storage.net/{index}.jpg')",
                            },
                            id=f'task {index}',
                            pool_id=pool_id,
                        )
                        for index in range(len(self.images))
                    ],
                ),
            ),
            ('open_pool', ('fake pool',)),
        ]
        flat_solutions = chain(*self.classification_solutions)
        assert results == [
            ((self.images[i],), ((self.images[i],), [((cls, ok, comment), assignments[i // 4])]))
            for i, (_, cls, ok, comment) in enumerate(flat_solutions)
        ]

    def test_experts_classification_solution_pipeline_e2e(self):
        project = toloka.Project(
            id='project',
            task_spec=toloka.project.TaskSpec(
                input_spec=lib.image_classification_expert_solution_mapping.to_toloka_input_spec(),
                output_spec=lib.image_classification_expert_solution_mapping.to_toloka_output_spec(),
            ),
        )

        pool_id = 'fake pool'
        pool_cfg = pool_config.ExpertConfig(
            project_id=project.id,
            private_name=pool_id,
            reward_per_assignment=0.01,
            task_duration_hint=datetime.timedelta(seconds=10),
            real_tasks_count=4,
            worker_filter=worker.ExpertFilter([toloka.Skill(id='expert'), toloka.Skill(id='expert_RU')]),
        )

        flat_solutions = list(chain(*self.classification_solutions))
        assignments = [
            lib.create_expert_classification_assignment(
                expert_solutions, user_id=user_id, pool_id=pool_id, task_annotation=False
            )[0]
            for expert_solutions, user_id in zip(self.classification_solutions, ['bob', 'mary', 'john'])
        ]

        # List[mapping.TaskSolution]
        pool_solution_objects = [((image,), (cls,)) for image, cls, _, _ in flat_solutions]
        stub = TolokaClientStub(assignments, project)

        loop = experts.ExpertPipeline(
            client=stub,  # noqa
            task_mapping=lib.image_classification_expert_solution_mapping,
            task_function=None,  # noqa
            lang='RU',
            scenario=project_config.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS,
        )

        pool = loop.create_pool(pool_cfg=pool_cfg)
        loop.add_input_objects(pool.id, pool_solution_objects)
        loop.loop(pool.id)
        results = loop.get_results(pool.id, pool_solution_objects)
        assert stub.calls[1:] == [
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'image_url': f'https://storage.net/{index}.jpg',
                                'choice': cls.value,
                                'id': f"Image(url='https://storage.net/{index}.jpg') {repr(cls)}",
                            },
                            id=f'task {index}',
                            pool_id=pool_id,
                        )
                        for index, (_, cls, _, _) in enumerate(flat_solutions)
                    ],
                ),
            ),
            ('open_pool', ('fake pool',)),
        ]
        assert results == [
            ((self.images[i], cls), ((self.images[i], cls), [((ok, comment), assignments[i // 4])]))
            for i, (_, cls, ok, comment) in enumerate(flat_solutions)
        ]

    def test_experts_annotation_task_pipeline_e2e(self):
        project = toloka.Project(
            id='project',
            task_spec=toloka.project.TaskSpec(
                input_spec=lib.audio_transcription_expert_task_mapping.to_toloka_input_spec(),
                output_spec=lib.audio_transcription_expert_task_mapping.to_toloka_output_spec(),
            ),
        )

        pool_id = 'fake pool'
        pool_cfg = pool_config.ExpertConfig(
            project_id=project.id,
            private_name=pool_id,
            reward_per_assignment=0.01,
            task_duration_hint=datetime.timedelta(seconds=10),
            real_tasks_count=4,
            worker_filter=worker.ExpertFilter([toloka.Skill(id='expert'), toloka.Skill(id='expert_RU')]),
        )

        assignments = [
            lib.create_expert_annotation_assignment(expert_solutions, user_id=user_id, pool_id=pool_id)[0]
            for expert_solutions, user_id in zip(self.annotation_solutions, ['bob', 'mary', 'john'])
        ]
        pool_input_objects = [(audio,) for audio in self.audios]
        stub = TolokaClientStub(assignments, project)

        loop = experts.ExpertPipeline(
            client=stub,  # noqa
            task_mapping=lib.audio_transcription_expert_task_mapping,
            task_function=base.AnnotationFunction(inputs=(Audio,), outputs=(Text,)),
            lang='RU',
            scenario=project_config.Scenario.EXPERT_LABELING_OF_TASKS,
        )

        pool = loop.create_pool(pool_cfg=pool_cfg)
        loop.add_input_objects(pool.id, pool_input_objects)
        loop.loop(pool.id)
        results = loop.get_results(pool.id, pool_input_objects)
        assert stub.calls[1:] == [
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{index}.jpg',
                                'id': f"Audio(url='https://storage.net/{index}.jpg')",
                            },
                            id=f'task {index}',
                            pool_id=pool_id,
                        )
                        for index in range(len(self.images))
                    ],
                ),
            ),
            ('open_pool', ('fake pool',)),
        ]
        flat_solutions = chain(*self.annotation_solutions)
        assert results == [
            ((self.audios[i],), ((self.audios[i],), [((text, eval, ok, comment), assignments[i // 4])]))
            for i, (_, text, eval, ok, comment) in enumerate(flat_solutions)
        ]

    def test_experts_annotation_solution_pipeline_e2e(self):
        project = toloka.Project(
            id='project',
            task_spec=toloka.project.TaskSpec(
                input_spec=lib.audio_transcription_expert_solution_mapping.to_toloka_input_spec(),
                output_spec=lib.audio_transcription_expert_solution_mapping.to_toloka_output_spec(),
            ),
        )

        pool_id = 'fake pool'
        pool_cfg = pool_config.ExpertConfig(
            project_id=project.id,
            private_name=pool_id,
            reward_per_assignment=0.01,
            task_duration_hint=datetime.timedelta(seconds=10),
            real_tasks_count=4,
            worker_filter=worker.ExpertFilter([toloka.Skill(id='expert'), toloka.Skill(id='expert_RU')]),
        )

        flat_solutions = list(chain(*self.annotation_solutions))
        assignments = [
            lib.create_expert_annotation_assignment(
                expert_solutions, user_id=user_id, pool_id=pool_id, task_annotation=False
            )[0]
            for expert_solutions, user_id in zip(self.annotation_solutions, ['bob', 'mary', 'john'])
        ]

        # List[mapping.TaskSolution]
        pool_solution_objects = [((image,), (text,)) for image, text, *_ in flat_solutions]
        stub = TolokaClientStub(assignments, project)

        loop = experts.ExpertPipeline(
            client=stub,  # noqa
            task_mapping=lib.audio_transcription_expert_solution_mapping,
            task_function=base.AnnotationFunction(inputs=(Audio,), outputs=(Text,)),
            lang='RU',
            scenario=project_config.Scenario.EXPERT_LABELING_OF_TASKS,
        )

        pool = loop.create_pool(pool_cfg=pool_cfg)
        loop.add_input_objects(pool.id, pool_solution_objects)
        loop.loop(pool.id)
        results = loop.get_results(pool.id, pool_solution_objects)
        assert stub.calls[1:] == [
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{index}.jpg',
                                'output': text.text,
                                'id': f"Audio(url='https://storage.net/{index}.jpg') Text(text='{text.text}')",
                            },
                            id=f'task {index}',
                            pool_id=pool_id,
                        )
                        for index, (_, text, _, _, _) in enumerate(flat_solutions)
                    ],
                ),
            ),
            ('open_pool', ('fake pool',)),
        ]
        assert results == [
            ((self.audios[i], text), ((self.audios[i], text), [((eval, ok, comment), assignments[i // 4])]))
            for i, (_, text, eval, ok, comment) in enumerate(flat_solutions)
        ]
