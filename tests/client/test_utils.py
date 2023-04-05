from datetime import timedelta
from mock import patch
import pytest
from typing import List

from crowdom import objects, client, mapping, pricing


@pytest.fixture
def input_objects() -> List[mapping.Objects]:
    return [(objects.Image(url='https://storage.net/1.jpg'),)] * 10


@pytest.fixture
def control_objects(input_objects: List[mapping.Objects]) -> List[mapping.TaskSingleSolution]:
    return [(obj, (objects.Text(text='hi'),)) for obj in input_objects]


@pytest.fixture
def task_duration_hint() -> timedelta:
    return timedelta(seconds=5)


@pytest.fixture
def task_duration_hint_long() -> timedelta:
    return timedelta(minutes=1)


@pytest.fixture
def pricing_config() -> pricing.PoolPricingConfig:
    return pricing.PoolPricingConfig(assignment_price=0.01, real_tasks_count=4, control_tasks_count=2)


@patch('crowdom.client.utils.OBJECTS_COUNT_VALID_RANGE', (1, 5))
@patch('crowdom.client.utils.OBJECTS_COUNT_RECOMMENDED_RANGE', (1, 4))
class TestValidateObjectsVolume:
    def test_valid_count_range(self, input_objects, control_objects, task_duration_hint, pricing_config):
        with pytest.raises(AssertionError) as e:
            client.validate_objects_volume(input_objects, control_objects, task_duration_hint, pricing_config)
        assert str(e.value) == 'Objects count must be in range [1, 5], you have 10'

        with pytest.raises(AssertionError) as e:
            client.validate_objects_volume(input_objects[:3], control_objects[:1], task_duration_hint, pricing_config)
        assert str(e.value) == 'Control objects count must be in range [2, 5], you have 1'

    @patch('crowdom.client.utils.ask')
    def test_recommended_count_range_input_objects(
        self,
        ask,
        input_objects: List[mapping.Objects],
        control_objects: List[mapping.TaskSingleSolution],
        task_duration_hint: timedelta,
        pricing_config: pricing.PoolPricingConfig,
    ):
        ask.return_value = False
        client.validate_objects_volume(
            input_objects[:5], control_objects, task_duration_hint, pricing_config, interactive=True
        )
        ask.assert_called_with(
            'Objects count recommended range is [1, 4], you have 5. Too small objects '
            'volume is inefficient in terms of speed, too big may cause problems in crowd-sourcing '
            'platform API or can be risky if launch is misconfigured. Do you wish to continue?'
        )

    @patch('crowdom.client.utils.ask')
    def test_recommended_duration_range_input_objects(
        self,
        ask,
        input_objects: List[mapping.Objects],
        control_objects: List[mapping.TaskSingleSolution],
        task_duration_hint: timedelta,
        pricing_config: pricing.PoolPricingConfig,
    ):
        ask.return_value = False
        client.validate_objects_volume(
            input_objects[:4], control_objects[:5], task_duration_hint, pricing_config, interactive=True
        )
        ask.assert_called_with(
            'Objects duration recommended range is [0:01:00 - 2 days, 0:00:00], you have '
            '0:00:20. Too small objects volume is inefficient in terms of speed, too big '
            'may cause problems in crowd-sourcing platform API or can be risky if launch '
            'is misconfigured. Do you wish to continue?'
        )

    @patch('crowdom.client.utils.ask')
    @patch('crowdom.client.utils.CONTROL_OBJECTS_RECOMMENDED_MIN_RATIO', 2.0)
    def test_control_objects_recommended_ratio(
        self,
        ask,
        input_objects: List[mapping.Objects],
        control_objects: List[mapping.TaskSingleSolution],
        task_duration_hint_long: timedelta,
        pricing_config: pricing.PoolPricingConfig,
    ):
        ask.return_value = False
        client.validate_objects_volume(
            input_objects[:4], control_objects[:4], task_duration_hint_long, pricing_config, interactive=True
        )
        ask.assert_called_with(
            'Recommended control objects minimum ratio is 2.0, you have 1.00. A '
            'sufficient control tasks ratio is needed for higher throughput (each worker '
            'will see specific control task only once). Do you wish to continue?'
        )

    def test_no_control_objects(
        self,
        input_objects: List[mapping.Objects],
        task_duration_hint_long: timedelta,
    ):
        # no calls to ask
        pricing_config = pricing.PoolPricingConfig(0.02, 10, 0)

        assert client.validate_objects_volume(
            input_objects[:4], [], task_duration_hint_long, pricing_config, interactive=True
        )
