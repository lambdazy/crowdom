from datetime import timedelta
from mock import patch
from pytest import approx, fixture
from toloka.client.assignment import Assignment
from toloka.client.user_restriction import UserRestriction
from typing import List

from crowdom import (
    base,
    classification,
    classification_loop,
    control,
    pricing,
    params,
    objects,
    task_spec as spec,
    worker,
)
from crowdom.control import (
    AssignmentAccuracyPredicate,
    SetAssignmentStatus,
    BlockUser,
    PredicateExpression,
    ComparisonType,
    Rule,
    BooleanOperator,
    AssignmentDurationPredicate,
)

from . import lib


class TestGetValues:
    def test_assignment_price(self):
        assert params.AssignmentPrice.get_values(
            task_duration_hint=timedelta(seconds=5),
            task_count=1,
            control_task_count=0,
        ) == (0.005, [0.005, 0.208], [0.005, 0.005])

        assert params.AssignmentPrice.get_values(
            task_duration_hint=timedelta(seconds=30),
            task_count=30,
            control_task_count=30,
        ) == (0.3, [0.005, 1.25], [0.15, 0.45])

    def test_annotation_assignment_price(self):
        assert params.AnnotationAssignmentPrice.get_values(
            task_duration_hint=timedelta(seconds=5),
            task_count=1,
        ) == (0.005, [0.005, 0.104], [0.005, 0.005])

        assert params.AnnotationAssignmentPrice.get_values(
            task_duration_hint=timedelta(seconds=30),
            task_count=30,
        ) == (0.15, [0.005, 0.625], [0.075, 0.225])

    def test_control_task_count(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.NO_CONTROL, (0, [0, 10], [1, 4], True)),
            (params.QualityPresetType.MILD, (2, [0, 10], [1, 4], True)),
            (params.QualityPresetType.MODERATE, (3, [0, 10], [1, 4], True)),
            (params.QualityPresetType.STRICT, (6, [0, 10], [1, 4], True)),
        ]:
            assert (
                params.ControlTaskCount.get_values(
                    task_count=15,
                    quality_preset=quality_preset.value,
                )
                == params.ControlTaskCount.get_values(
                    task_count=15,
                    quality_preset=quality_preset.value,
                    control_task_count=5,
                )
                == expected_values
            )

        assert params.ControlTaskCount.get_values(
            task_count=15,
            quality_preset=params.QualityPresetType.CUSTOM.value,
            control_task_count=5,
        ) == (5, [0, 15], [1, 4], False)

    def test_control_tasks_for_accept(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.NO_CONTROL, (0, True, [0, 12], [3, 8])),
            (params.QualityPresetType.MILD, (5, True, [0, 12], [3, 8])),
            (params.QualityPresetType.MODERATE, (6, True, [0, 12], [3, 8])),
            (params.QualityPresetType.STRICT, (7, True, [0, 12], [3, 8])),
        ]:
            assert (
                params.ControlTasksForAccept.get_values(
                    num_classes=3,
                    quality_preset=quality_preset.value,
                    control_task_count=12,
                )
                == params.ControlTasksForAccept.get_values(
                    num_classes=3,
                    quality_preset=quality_preset.value,
                    control_task_count=12,
                    control_tasks_for_accept=10,
                )
                == expected_values
            )

        assert params.ControlTasksForAccept.get_values(
            num_classes=3,
            quality_preset=params.QualityPresetType.CUSTOM.value,
            control_task_count=12,
            control_tasks_for_accept=10,
        ) == (10, False, [0, 12], [3, 8])

    def test_checked_tasks_for_accept(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.MILD, (8, True, [0, 12], [3, 8])),
            (params.QualityPresetType.MODERATE, (9, True, [0, 12], [3, 8])),
            (params.QualityPresetType.STRICT, (11, True, [0, 12], [3, 8])),
        ]:
            assert (
                params.CheckedTasksForAccept.get_values(
                    num_classes=3,
                    quality_preset=quality_preset.value,
                    control_task_count=12,
                )
                == params.CheckedTasksForAccept.get_values(
                    num_classes=3,
                    quality_preset=quality_preset.value,
                    control_task_count=12,
                    control_tasks_for_accept=10,
                )
                == expected_values
            )

        assert params.CheckedTasksForAccept.get_values(
            num_classes=3,
            quality_preset=params.QualityPresetType.CUSTOM.value,
            control_task_count=12,
            control_tasks_for_accept=10,
        ) == (10, False, [0, 12], [3, 8])

    def test_control_tasks_for_block(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.NO_CONTROL, (0, True, [0, 12], [0, 4])),
            (params.QualityPresetType.MILD, (2, True, [0, 12], [0, 4])),
            (params.QualityPresetType.MODERATE, (4, True, [0, 12], [0, 4])),
            (params.QualityPresetType.STRICT, (6, True, [0, 12], [0, 4])),
        ]:
            assert (
                params.ControlTasksForBlock.get_values(
                    quality_preset=quality_preset.value,
                    control_task_count=12,
                )
                == params.ControlTasksForBlock.get_values(
                    quality_preset=quality_preset.value,
                    control_task_count=12,
                    control_tasks_for_block=10,
                )
                == expected_values
            )

        assert params.ControlTasksForBlock.get_values(
            quality_preset=params.QualityPresetType.CUSTOM.value,
            control_task_count=12,
            control_tasks_for_block=10,
        ) == (10, False, [0, 12], [0, 4])

    def test_overlap(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.NO_CONTROL, ('1', True)),
            (params.QualityPresetType.MILD, ('2-3', True)),
            (params.QualityPresetType.MODERATE, ('3', True)),
            (params.QualityPresetType.STRICT, ('3-5', True)),
        ]:
            assert (
                params.Overlap.get_values(
                    quality_preset=quality_preset.value,
                )
                == params.Overlap.get_values(
                    quality_preset=quality_preset.value,
                    overlap='1-5',
                )
                == expected_values
            )

        assert params.Overlap.get_values(
            quality_preset=params.QualityPresetType.CUSTOM.value,
            overlap='1-5',
        ) == ('1-5', False)

    def test_max_attempts(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.MILD, ('2', True)),
            (params.QualityPresetType.MODERATE, ('3', True)),
            (params.QualityPresetType.STRICT, ('5', True)),
        ]:
            assert (
                params.MaxAttempts.get_values(
                    quality_preset=quality_preset.value,
                )
                == params.MaxAttempts.get_values(
                    quality_preset=quality_preset.value,
                    max_attempts='5',
                )
                == expected_values
            )

        assert params.MaxAttempts.get_values(
            quality_preset=params.QualityPresetType.CUSTOM.value,
            max_attempts='5',
        ) == ('5', False)

    def test_speed_control(self):
        for quality_preset, expected_values in [
            (params.QualityPresetType.NO_CONTROL, ([], True)),
            (
                params.QualityPresetType.MILD,
                ([params.BlockTimePicker(0.01, '1d', True), params.BlockTimePicker(0.05, '2h', False)], True),
            ),
            (
                params.QualityPresetType.MODERATE,
                ([params.BlockTimePicker(0.1, '1d', True), params.BlockTimePicker(0.3, '2h', False)], True),
            ),
            (
                params.QualityPresetType.STRICT,
                ([params.BlockTimePicker(0.3, '1d', True), params.BlockTimePicker(0.5, '2h', False)], True),
            ),
        ]:
            assert (
                params.SpeedControlList.get_values(
                    quality_preset=quality_preset.value,
                )
                == params.SpeedControlList.get_values(
                    quality_preset=quality_preset.value,
                    items=[params.BlockTimePicker()],
                )
                == expected_values
            )

        items = [params.BlockTimePicker(0.5, '1d', False), params.BlockTimePicker(0.35, '2d', True)]
        assert params.SpeedControlList.get_values(
            quality_preset=params.QualityPresetType.CUSTOM.value,
            items=items,
        ) == (items, False)

    def test_check_sample(self):
        for quality_preset in [
            params.QualityPresetType.MILD,
            params.QualityPresetType.MODERATE,
            params.QualityPresetType.STRICT,
        ]:
            assert (
                params.CheckSample.get_values(
                    quality_preset=quality_preset.value,
                )
                == params.CheckSample.get_values(
                    quality_preset=quality_preset.value,
                    check_sample=False,
                )
                == (False, True)
            )

        assert params.CheckSample.get_values(
            quality_preset=params.QualityPresetType.CUSTOM.value,
            check_sample=True,
        ) == (True, False)

    def test_max_tasks_to_check(self):
        for quality_preset in [
            params.QualityPresetType.MILD,
            params.QualityPresetType.MODERATE,
            params.QualityPresetType.STRICT,
        ]:
            assert (
                params.MaxTasksToCheck.get_values(
                    task_count=15,
                    quality_preset=quality_preset.value,
                    check_sample=True,
                )
                == params.MaxTasksToCheck.get_values(
                    task_count=15,
                    quality_preset=quality_preset.value,
                    check_sample=True,
                    max_tasks_to_check=10,
                )
                == (15, True, [1, 15], [15])
            )

        assert params.MaxTasksToCheck.get_values(
            task_count=15,
            quality_preset=params.QualityPresetType.CUSTOM.value,
            check_sample=True,
            max_tasks_to_check=5,
        ) == (5, False, [1, 15], [15])

    def test_accuracy_thresold(self):
        for quality_preset in [
            params.QualityPresetType.MILD,
            params.QualityPresetType.MODERATE,
            params.QualityPresetType.STRICT,
        ]:
            assert params.AccuracyThreshold.get_values(
                task_count=15,
                quality_preset=quality_preset.value,
                check_sample=True,
                max_tasks_to_check=10,
            ) == (10, True, [1, 10], [8, 10])

        assert params.AccuracyThreshold.get_values(
            task_count=15,
            quality_preset=params.QualityPresetType.CUSTOM.value,
            check_sample=True,
            max_tasks_to_check=10,
            accuracy_threshold=5,
        ) == (5, False, [1, 10], [8, 10])


@fixture
def task_duration_hint() -> timedelta:
    return timedelta(seconds=10)


@fixture
def initial_rules(task_duration_hint: timedelta) -> List[control.Rule]:
    return [
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=1.0,
                comparison=ComparisonType('>='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.ACCEPTED),
        ),
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=1.0,
                comparison=ComparisonType('<'),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.1,
                comparison=ComparisonType('<='),
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, <= 0.1',
                duration=timedelta(days=1),
            ),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.1,
                comparison=ComparisonType('<='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.1,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, 0.1 < time <= 0.3',
                duration=timedelta(hours=2),
            ),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentAccuracyPredicate(
                        threshold=0.0,
                        comparison=ComparisonType('>='),
                    ),
                    AssignmentAccuracyPredicate(
                        threshold=0.5,
                        comparison=ComparisonType('<'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Control tasks: [0, 1) done correctly',
                duration=timedelta(hours=1),
            ),
        ),
    ]


@fixture
def initial_annotation_rules(task_duration_hint: timedelta) -> List[control.Rule]:
    return [
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=7 / 9,
                comparison=ComparisonType('>='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.ACCEPTED),
        ),
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=7 / 9,
                comparison=ComparisonType('<'),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.1,
                comparison=ComparisonType('<='),
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, <= 0.1',
                duration=timedelta(days=1),
            ),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.1,
                comparison=ComparisonType('<='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.1,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, 0.1 < time <= 0.3',
                duration=timedelta(hours=2),
            ),
        ),
    ]


@fixture
def initial_params(task_duration_hint: timedelta, initial_rules: List[control.Rule]) -> params.Params:
    return params.Params(
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN', verified=True)},
                    regions={worker.RegionCodes.UNITED_STATES, worker.RegionCodes.UNITED_KINGDOM},
                )
            ],
            training_score=None,
        ),
        task_duration_hint=task_duration_hint,
        pricing_config=pricing.PoolPricingConfig(
            assignment_price=0.018,
            real_tasks_count=9,
            control_tasks_count=2,
        ),
        overlap=classification_loop.StaticOverlap(3),
        control=control.Control(
            rules=initial_rules,
        ),
        aggregation_algorithm=classification.AggregationAlgorithm.DAWID_SKENE,
    )


@fixture
def initial_annotation_params(
    task_duration_hint: timedelta, initial_annotation_rules: List[control.Rule]
) -> params.AnnotationParams:
    return params.AnnotationParams(
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN', verified=True)},
                    regions={worker.RegionCodes.UNITED_STATES, worker.RegionCodes.UNITED_KINGDOM},
                )
            ],
            training_score=None,
        ),
        task_duration_hint=task_duration_hint,
        pricing_config=pricing.PoolPricingConfig(
            assignment_price=0.014,
            real_tasks_count=9,
            control_tasks_count=0,
        ),
        overlap=classification_loop.DynamicOverlap(1, 3, 0.85),
        control=control.Control(
            rules=initial_annotation_rules,
        ),
        aggregation_algorithm=None,
    )


@fixture
def changed_rules(task_duration_hint: timedelta) -> List[control.Rule]:
    return [
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=7 / 12,
                comparison=ComparisonType('>='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.ACCEPTED),
        ),
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=7 / 12,
                comparison=ComparisonType('<'),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.3,
                comparison=ComparisonType('<='),
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, <= 0.3',
                duration=timedelta(days=1),
            ),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.3,
                comparison=ComparisonType('<='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.5,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, 0.3 < time <= 0.5',
                duration=timedelta(hours=2),
            ),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentAccuracyPredicate(
                        threshold=0.0,
                        comparison=ComparisonType('>='),
                    ),
                    AssignmentAccuracyPredicate(
                        threshold=0.5,
                        comparison=ComparisonType('<'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Control tasks: [0, 6) done correctly',
                duration=timedelta(hours=1),
            ),
        ),
    ]


@fixture
def changed_params(task_duration_hint: timedelta, changed_rules: List[control.Rule]) -> params.Params:
    return params.Params(
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN', verified=True)},
                    regions={worker.RegionCodes.UNITED_STATES, worker.RegionCodes.UNITED_KINGDOM},
                )
            ],
            training_score=None,
        ),
        task_duration_hint=task_duration_hint,
        pricing_config=pricing.PoolPricingConfig(
            assignment_price=0.07,
            real_tasks_count=30,
            control_tasks_count=12,
        ),
        overlap=classification_loop.DynamicOverlap(3, 5, 0.85),
        control=control.Control(
            rules=changed_rules,
        ),
        aggregation_algorithm=classification.AggregationAlgorithm.DAWID_SKENE,
    )


@fixture
def changed_annotation_rules(task_duration_hint: timedelta) -> List[control.Rule]:
    return [
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=0.9,
                comparison=ComparisonType('>='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.ACCEPTED),
        ),
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=0.9,
                comparison=ComparisonType('<'),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.3,
                comparison=ComparisonType('<='),
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, <= 0.3',
                duration=timedelta(days=1),
            ),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.3,
                comparison=ComparisonType('<='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.5,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, 0.3 < time <= 0.5',
                duration=timedelta(hours=2),
            ),
        ),
    ]


@fixture
def changed_annotation_params(
    task_duration_hint: timedelta, changed_annotation_rules: List[control.Rule]
) -> params.AnnotationParams:
    return params.AnnotationParams(
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN', verified=True)},
                    regions={worker.RegionCodes.UNITED_STATES, worker.RegionCodes.UNITED_KINGDOM},
                )
            ],
            training_score=None,
        ),
        task_duration_hint=task_duration_hint,
        pricing_config=pricing.PoolPricingConfig(
            assignment_price=0.05,
            real_tasks_count=30,
            control_tasks_count=0,
        ),
        overlap=classification_loop.DynamicOverlap(1, 5, 0.85),
        control=control.Control(
            rules=changed_annotation_rules,
        ),
        aggregation_algorithm=None,
        assignment_check_sample=None,
    )


@fixture
def final_rules(task_duration_hint: timedelta) -> List[control.Rule]:
    return [
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=1.0,
                comparison=ComparisonType('>='),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.ACCEPTED),
        ),
        Rule(
            predicate=AssignmentAccuracyPredicate(
                threshold=1.0,
                comparison=ComparisonType('<'),
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=AssignmentDurationPredicate(
                threshold=0.05,
                comparison=ComparisonType('<='),
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, <= 0.05',
                duration=timedelta(minutes=30),
            ),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.05,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, 0.05 < time <= 0.3',
                duration=timedelta(days=1),
            ),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.05,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=SetAssignmentStatus(status=Assignment.Status.REJECTED),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentDurationPredicate(
                        threshold=0.5,
                        comparison=ComparisonType('<='),
                    ),
                    AssignmentDurationPredicate(
                        threshold=0.3,
                        comparison=ComparisonType('>'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Fast submits, 0.3 < time <= 0.5',
                duration=timedelta(hours=2),
            ),
        ),
        Rule(
            predicate=PredicateExpression(
                boolean_operator=BooleanOperator.AND,
                predicates=[
                    AssignmentAccuracyPredicate(
                        threshold=0.0,
                        comparison=ComparisonType('>='),
                    ),
                    AssignmentAccuracyPredicate(
                        threshold=1.0,
                        comparison=ComparisonType('<'),
                    ),
                ],
            ),
            action=BlockUser(
                scope=UserRestriction.Scope.POOL,
                private_comment='Control tasks: [0, 2) done correctly',
                duration=timedelta(hours=1),
            ),
        ),
    ]


@fixture
def final_params(task_duration_hint: timedelta, final_rules: List[control.Rule]) -> params.Params:
    return params.Params(
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN', verified=True)},
                    regions={worker.RegionCodes.UNITED_STATES, worker.RegionCodes.UNITED_KINGDOM},
                )
            ],
            training_score=None,
        ),
        task_duration_hint=task_duration_hint,
        pricing_config=pricing.PoolPricingConfig(
            assignment_price=0.04,
            real_tasks_count=30,
            control_tasks_count=2,
        ),
        overlap=classification_loop.DynamicOverlap(3, 5, 0.85),
        control=control.Control(
            rules=final_rules,
        ),
        aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
    )


@patch('crowdom.params.characteristics.ITERATIONS_COUNT', 200)
class TestEventLoop:
    def test_loop(
        self,
        task_duration_hint: timedelta,
        initial_params: params.Params,
        changed_params: params.Params,
        final_params: params.Params,
    ):
        function = base.ClassificationFunction(inputs=(objects.Image,), cls=lib.ImageClass)
        instruction = {'EN': 'Identify the animal in the photo', 'RU': 'Определите, какое животное на фотографии'}
        task_spec = base.TaskSpec(
            id='dogs-and-cats',
            function=function,
            name={'EN': 'Cat or dog', 'RU': 'Кошка или собака'},
            description={'EN': 'Identification of animals in photos', 'RU': 'Определение животных на изображениях'},
            instruction=instruction,
        )
        task_spec_en = spec.PreparedTaskSpec(task_spec, 'EN')

        toloka_client = lib.TolokaClientCallRecorderStub()
        loop = params.get_loop(
            task_spec_en,
            task_duration_hint,
            toloka_client,  # noqa
        )
        loop.ui_initialized = True

        # generated default
        assert loop.get_params() == initial_params
        assert [p.value for p in loop.stats] == approx([0.87, 0.69, 0.30], abs=0.05)
        assert loop.characteristics.value[:5] == [
            'Robustness: 0.89, recommended range - [0.6, 0.9]',
            'Assignment duration: 0:01:50, recommended range - [30s, 5m]',
            'Assignment commission, usd: 0.005',
            'Expected worker earnings per hour: 0.589\\$',
            'Expected price per 1000 objects: 7.86\\$',
        ]
        # we can't check 'Expected loop iterations: ?'
        assert loop.characteristics.value[-1] == 'Task attractiveness index: 4 / 7'

        loop.start(params.UIEvent(params.ParamName.TASK_COUNT.ui, {params.ParamName.TASK_COUNT: params.Update(30)}))
        loop.start(
            params.UIEvent(
                params.ParamName.QUALITY_PRESET.ui, {params.ParamName.QUALITY_PRESET: params.Update('Strict')}
            )
        )

        # check
        assert loop.get_params() == changed_params
        assert [p.value for p in loop.stats] == approx([0.93, 0.76, 0.58], abs=0.05)
        assert loop.characteristics.value[:5] == [
            'Robustness: 0.93, recommended range - [0.6, 0.9]',
            'Assignment duration: 0:07:00, recommended range - [30s, 5m]',
            'Assignment commission, usd: 0.021',
            'Expected worker earnings per hour: 0.600\\$',
            'Expected price per 1000 objects: 9.28\\$ ... 15.47\\$',
        ]
        # can't check:
        # 'Expected loop iterations: ?',
        # 'Expected average overlap: ?',
        # 'Expected average price per 1000 objects: ?',
        assert loop.characteristics.value[-1] == 'Task attractiveness index: 3 / 7'

        # some more changes
        loop.start(
            params.UIEvent(
                params.ParamName.QUALITY_PRESET.ui, {params.ParamName.QUALITY_PRESET: params.Update('Custom')}
            )
        )
        loop.start(
            params.SpeedControlEvent(
                params.ParamName.SPEED_CONTROL.ui, {params.SpeedControlChangeType.ADD: params.SpeedControlUpdate('')}
            )
        )
        loop.start(
            params.UIEvent(
                params.ParamName.AGGREGATION_ALGORITHM.ui, {params.ParamName.AGGREGATION_ALGORITHM: params.Update('ML')}
            )
        )
        loop.start(
            params.UIEvent(
                params.ParamName.CONTROL_TASK_COUNT.ui, {params.ParamName.CONTROL_TASK_COUNT: params.Update(2)}
            )
        )
        loop.start(
            params.UIEvent(
                params.ParamName.ASSIGNMENT_PRICE.ui, {params.ParamName.ASSIGNMENT_PRICE: params.Update(0.04)}
            )
        )

        # final check
        assert loop.get_params() == final_params
        assert [p.value for p in loop.stats] == approx([0.87, 0.80, 0.21], abs=0.05)
        assert loop.characteristics.value[:5] == [
            'Robustness: 0.89, recommended range - [0.6, 0.9]',
            'Assignment duration: 0:05:20, recommended range - [30s, 5m]',
            'Assignment commission, usd: 0.012',
            'Expected worker earnings per hour: 0.450\\$',
            'Expected price per 1000 objects: 5.30\\$ ... 8.84\\$',
        ]
        # can't check:
        # 'Expected loop iterations: ?',
        # 'Expected average overlap: ?',
        # 'Expected average price per 1000 objects: ?',
        assert loop.characteristics.value[-1] == 'Task attractiveness index: 2 / 7'

    def test_annotation_loop(
        self,
        task_duration_hint: timedelta,
        initial_annotation_params: params.AnnotationParams,
        changed_annotation_params: params.AnnotationParams,
    ):
        function = base.AnnotationFunction(inputs=(objects.Audio,), outputs=(objects.Text,))
        instruction = {'EN': 'Transcribe given audio', 'RU': 'Запишите текст с аудио'}
        task_spec = base.TaskSpec(
            id='dogs-and-cats',
            function=function,
            name={'EN': 'Audio transcription', 'RU': 'Расшифровка речи'},
            description={'EN': 'Transcribe given audio', 'RU': 'Запишите текст с аудио'},
            instruction=instruction,
        )
        task_spec_en = spec.AnnotationTaskSpec(task_spec, 'EN')

        loop = params.get_loop_for_annotation(
            task_spec_en,
            task_duration_hint,
            toloka_client=None,  # noqa
        )

        loop.ui_initialized = True

        # generated default
        assert loop.get_params() == initial_annotation_params

        assert [p.value for p in loop.stats] == approx([0.63, 0.56, 0.40], abs=0.05)
        assert loop.characteristics.value[:3] == [
            'Assignment duration: 0:01:30, recommended range - [30s, 5m]',
            'Assignment commission, usd: 0.004',
            'Expected worker earnings per hour: 0.560\\$',
        ]
        # we can't check 'Expected loop iterations: ?'
        # and 'Expected average overlap: ?'
        assert loop.characteristics.value[-1] == 'Task attractiveness index: 4 / 6'

        loop.start(params.UIEvent(params.ParamName.TASK_COUNT.ui, {params.ParamName.TASK_COUNT: params.Update(30)}))
        loop.start(
            params.UIEvent(
                params.ParamName.QUALITY_PRESET.ui, {params.ParamName.QUALITY_PRESET: params.Update('Strict')}
            )
        )

        # check
        assert loop.get_params() == changed_annotation_params
        assert [p.value for p in loop.stats] == approx([0.89, 0.96, 0.03], abs=0.05)
        assert loop.characteristics.value[:2] == [
            'Assignment duration: 0:05:00, recommended range - [30s, 5m]',
            'Assignment commission, usd: 0.015',
        ]

        assert loop.characteristics.value[-1] == 'Task attractiveness index: 2 / 6'
