import pytest
from typing import List, Dict, Tuple

from datetime import timedelta

from crowdom import base, bots, classification_loop, client, mapping, objects, pricing, task_spec as spec


@pytest.fixture(scope='module')
def register() -> bots.NDARegisterClient:
    return bots.NDARegisterClient()


@pytest.fixture(scope='module')
def admin_client(register: bots.NDARegisterClient) -> bots.CallRecorderClient:
    admin = register.create_admin()
    return bots.CallRecorderClient(token=admin['oauth'])


@pytest.fixture
def toloka_client(register: bots.NDARegisterClient, admin_client: bots.CallRecorderClient) -> bots.CallRecorderClient:
    requester = register.create_user('requester')
    tlk_client = bots.CallRecorderClient(requester['oauth'])
    assert admin_client.change_credit(requester['id'], 10_000)['success'], 'Balance was not added'
    return tlk_client


class Animal(base.Class):
    DOG = 'dog'
    CAT = 'cat'
    OTHER = 'other'

    @classmethod
    def labels(cls) -> Dict['Animal', Dict[str, str]]:
        return {
            cls.DOG: {'EN': 'dog', 'RU': 'собака'},
            cls.CAT: {'EN': 'cat', 'RU': 'кошка'},
            cls.OTHER: {'EN': 'other', 'RU': 'другое'},
        }


@pytest.fixture
def function() -> base.ClassificationFunction:
    return base.ClassificationFunction(inputs=(objects.Image,), cls=Animal)


@pytest.fixture
def sbs_function() -> base.SbSFunction:
    return base.SbSFunction(inputs=(objects.Text, objects.Audio), hints=(objects.Audio,))


@pytest.fixture
def instruction() -> base.LocalizedString:
    return base.LocalizedString(
        {'EN': 'Identify the animal in the photo', 'RU': 'Определите, какое животное на фотографии'}
    )


@pytest.fixture
def sbs_instruction() -> base.LocalizedString:
    return base.LocalizedString({'RU': 'Выберите лучший вариант'})


@pytest.fixture
def task_spec(
    function: base.ClassificationFunction,
    instruction: base.LocalizedString,
) -> base.TaskSpec:
    return base.TaskSpec(
        id='dogs-and-cats',
        function=function,
        name=base.LocalizedString({'EN': 'Cat or dog', 'RU': 'Кошка или собака'}),
        description=base.LocalizedString(
            {'EN': 'Identification of animals in photos', 'RU': 'Определение животных на изображениях'}
        ),
        instruction=instruction,
    )


@pytest.fixture
def sbs_task_spec(
    sbs_function: base.ClassificationFunction,
    sbs_instruction: base.LocalizedString,
) -> base.TaskSpec:
    return base.TaskSpec(
        id='text-audio-sbs',
        function=sbs_function,
        name=base.LocalizedString({'EN': 'Audio transcripts comparison', 'RU': 'Сравнение расшифровок аудиозаписей'}),
        description=base.LocalizedString(
            {
                'EN': 'From the two transcripts, choose the more suitable for given audio recording',
                'RU': 'Из двух расшифровок выберите более подходящую аудиозаписи',
            }
        ),
        instruction=sbs_instruction,
    )


@pytest.fixture
def task_spec_p(task_spec: base.TaskSpec) -> spec.PreparedTaskSpec:
    lang = 'RU'
    return spec.PreparedTaskSpec(task_spec, lang)


@pytest.fixture
def sbs_task_spec_p(sbs_task_spec: base.TaskSpec) -> spec.PreparedTaskSpec:
    lang = 'RU'
    return spec.PreparedTaskSpec(sbs_task_spec, lang)


@pytest.fixture
def task_duration_hint() -> timedelta:
    return timedelta(seconds=10)


@pytest.fixture
def config_and_params(
    task_spec_p: spec.PreparedTaskSpec,
    task_duration_hint: timedelta,
) -> Tuple[pricing.PoolPricingConfig, classification_loop.Params]:
    return client.ClassificationLaunchParams.default_pricing_and_quality_params(
        task_duration_hint, task_spec_p, plot_pricing_options=False
    )


@pytest.fixture
def sbs_config_and_params(
    sbs_task_spec_p: spec.PreparedTaskSpec,
    task_duration_hint: timedelta,
) -> Tuple[pricing.PoolPricingConfig, classification_loop.Params]:
    return client.ClassificationLaunchParams.default_pricing_and_quality_params(
        task_duration_hint, sbs_task_spec_p, plot_pricing_options=False
    )


@pytest.fixture
def solved_tasks() -> List[mapping.TaskSingleSolution]:
    return [((objects.Image(url=f'image-{i}.jpg'),), (Animal.CAT if i % 2 else Animal.DOG,)) for i in range(1000)]


@pytest.fixture
def control_objects(solved_tasks) -> List[mapping.TaskSingleSolution]:
    return solved_tasks[:100]


@pytest.fixture
def input_objects(solved_tasks) -> List[mapping.Objects]:
    return [task for (task, solution) in solved_tasks[100:]]
