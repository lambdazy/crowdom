import datetime
from mock import patch, Mock
import pytest
from typing import List

import toloka.client as toloka

from crowdom import mapping, worker
from crowdom.worker import human
from crowdom.objects import Image
from . import lib


class TestModelWorkspace:
    def test_get_solutions(self):
        def func(pool_input_objects: List[mapping.Objects]) -> List[mapping.Objects]:
            results = []
            for (image,) in pool_input_objects:
                index = int(image.url[-5])
                cls = lib.ImageClass.CAT if index % 2 == 0 else lib.ImageClass.DOG
                results.append((cls,))
            return results

        model_ws = worker.ModelWorkspace(
            model=worker.Model(name='my-model', func=func),
            task_mapping=lib.image_classification_mapping,
        )

        assert model_ws.get_solutions(
            [
                (Image(url='https://0.jpg'),),
                (Image(url='https://1.jpg'),),
            ]
        ) == toloka.Assignment(
            id='',
            tasks=[
                toloka.Task(input_values={'image_url': 'https://0.jpg', 'id': 'Image(url=\'https://0.jpg\')'}),
                toloka.Task(input_values={'image_url': 'https://1.jpg', 'id': 'Image(url=\'https://1.jpg\')'}),
            ],
            solutions=[
                toloka.solution.Solution(output_values={'choice': 'cat'}),
                toloka.solution.Solution(output_values={'choice': 'dog'}),
            ],
            user_id='my-model',
            status=toloka.Assignment.SUBMITTED,
        )

        assert model_ws.solutions_cache == {
            mapping.TaskID((Image(url='https://0.jpg'),)): (lib.ImageClass.CAT,),
            mapping.TaskID((Image(url='https://1.jpg'),)): (lib.ImageClass.DOG,),
        }

        # new task added somewhere in between of previous list, check caching and correctness of solutions order

        assert model_ws.get_solutions(
            [
                (Image(url='https://0.jpg'),),
                (Image(url='https://2.jpg'),),
                (Image(url='https://1.jpg'),),
            ]
        ) == toloka.Assignment(
            id='',
            tasks=[
                toloka.Task(input_values={'image_url': 'https://0.jpg', 'id': 'Image(url=\'https://0.jpg\')'}),
                toloka.Task(input_values={'image_url': 'https://2.jpg', 'id': 'Image(url=\'https://2.jpg\')'}),
                toloka.Task(input_values={'image_url': 'https://1.jpg', 'id': 'Image(url=\'https://1.jpg\')'}),
            ],
            solutions=[
                toloka.solution.Solution(output_values={'choice': 'cat'}),
                toloka.solution.Solution(output_values={'choice': 'cat'}),
                toloka.solution.Solution(output_values={'choice': 'dog'}),
            ],
            user_id='my-model',
            status=toloka.Assignment.SUBMITTED,
        )

        assert model_ws.solutions_cache == {
            mapping.TaskID((Image(url='https://0.jpg'),)): (lib.ImageClass.CAT,),
            mapping.TaskID((Image(url='https://1.jpg'),)): (lib.ImageClass.DOG,),
            mapping.TaskID((Image(url='https://2.jpg'),)): (lib.ImageClass.CAT,),
        }

    def test_invalid_func(self):
        def func1(pool_input_objects: List[mapping.Objects]):
            return [(lib.ImageClass.CAT,)] * (len(pool_input_objects) + 1)

        def func2(pool_input_objects: List[mapping.Objects]):
            return [lib.ImageClass.CAT] * len(pool_input_objects)

        def func3(pool_input_objects: List[mapping.Objects]):
            return [(lib.ImageClass.CAT, lib.ImageClass.DOG)] * len(pool_input_objects)

        def func4(pool_input_objects: List[mapping.Objects]):
            return [(lib.AudioClass.SPEECH,)] * len(pool_input_objects)

        for func, err_msg in (
            (func1, 'invalid model func: output list length is not equal to input'),
            (func2, 'invalid model func: output objects are not tuple'),
            (func3, 'invalid model func: output objects count do not match task function'),
            (
                func4,
                'invalid model func: object type mismatch, expected <enum \'ImageClass\'>, actual <enum \'AudioClass\'>',
            ),
        ):
            model_ws = worker.ModelWorkspace(
                model=worker.Model(name='my-model', func=func),
                task_mapping=lib.image_classification_mapping,
            )
            with pytest.raises(AssertionError) as e:
                model_ws.get_solutions(
                    [
                        (Image(url='https://0.jpg'),),
                        (Image(url='https://1.jpg'),),
                    ]
                )
            assert str(e.value) == err_msg


class TestHumanFilters:
    def test_expert_filter(self):
        assert worker.ExpertFilter(
            skills=[toloka.Skill(id='expert'), toloka.Skill(id='expert_my-task_EN')]
        ).to_toloka_filter() == (toloka.filter.Skill('expert') > 0) | (toloka.filter.Skill('expert_my-task_EN') > 0)

    @patch.object(human, 'datetime', Mock(wraps=datetime))
    def test_worker_filter(self):
        human.datetime.datetime.today.return_value = datetime.datetime(2020, 11, 5)

        assert worker.WorkerFilter(
            training_score=50,
            filters=[
                worker.WorkerFilter.Params(
                    langs=set(),
                    age_range=(None, 80),
                    client_types={toloka.filter.ClientType.ClientType.BROWSER},
                ),
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN', verified=True)},
                    regions={worker.RegionCodes.TURKEY, worker.RegionCodes.SPAIN},
                    age_range=(24, 40),
                ),
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN'), worker.LanguageRequirement(lang='DE', verified=True)},
                    regions={worker.RegionCodes.ITALY},
                    client_types={
                        toloka.filter.ClientType.ClientType.TOLOKA_APP,
                        toloka.filter.ClientType.ClientType.BROWSER,
                    },
                ),
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='DE')},
                    age_range=(24, None),
                ),
            ],
        ).to_toloka_filter() == (
            (toloka.filter.DateOfBirth > int(datetime.datetime(1940, 11, 5).timestamp()))
            & (toloka.filter.ClientType == toloka.filter.ClientType.ClientType.BROWSER)
        ) | (
            toloka.filter.Languages.in_('EN', verified=True)
            & (toloka.filter.RegionByPhone.in_(204) | toloka.filter.RegionByPhone.in_(983))
            & (toloka.filter.DateOfBirth < int(datetime.datetime(1996, 11, 5).timestamp()))
            & (toloka.filter.DateOfBirth > int(datetime.datetime(1980, 11, 5).timestamp()))
        ) | (
            toloka.filter.Languages.in_('DE', verified=True)
            & toloka.filter.Languages.in_('EN')
            & toloka.filter.RegionByPhone.in_(205)
            & (toloka.filter.DateOfBirth < int(datetime.datetime(2002, 11, 5).timestamp()))
            & (
                (toloka.filter.ClientType == toloka.filter.ClientType.ClientType.BROWSER)
                | (toloka.filter.ClientType == toloka.filter.ClientType.ClientType.TOLOKA_APP)
            )
        ) | (
            toloka.filter.Languages.in_('DE')
            & (toloka.filter.DateOfBirth < int(datetime.datetime(1996, 11, 5).timestamp()))
        )

        assert worker.WorkerFilter(training_score=None, filters=[]).to_toloka_filter() is None

    def test_invalid_training_score(self):
        with pytest.raises(AssertionError):
            worker.WorkerFilter(training_score=101, filters=[])
