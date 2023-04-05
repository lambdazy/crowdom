from datetime import timedelta
import pytest

from toloka.client.assignment import Assignment
from toloka.client.user_restriction import UserRestriction

from crowdom import control


class TestPredicate:
    def test_different_types_in_expression(self):
        with pytest.raises(AssertionError) as e:
            control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('>')),
                    control.AssignmentDurationPredicate(threshold=0.2, comparison=control.ComparisonType('>')),
                ],
            )

        assert (
            str(e.value) == f'All predicates should be of same type. Expected {control.AssignmentAccuracyPredicate}, '
            f'got {control.AssignmentDurationPredicate}'
        )

    def test_empty_list(self):
        with pytest.raises(AssertionError) as e:
            control.PredicateExpression(boolean_operator=control.BooleanOperator.AND, predicates=[])
        assert str(e.value) == 'List of predicates should be non-empty'

    def test_nested_expression(self):
        with pytest.raises(AssertionError) as e:
            control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.PredicateExpression(
                        boolean_operator=control.BooleanOperator.AND,
                        predicates=[
                            control.AssignmentDurationPredicate(
                                threshold=0.5,
                                comparison=control.ComparisonType('<='),
                            ),
                            control.AssignmentDurationPredicate(
                                threshold=0.2,
                                comparison=control.ComparisonType('>'),
                            ),
                        ],
                    ),
                    control.PredicateExpression(
                        boolean_operator=control.BooleanOperator.AND,
                        predicates=[
                            control.AssignmentDurationPredicate(
                                threshold=0.5,
                                comparison=control.ComparisonType('<='),
                            ),
                            control.AssignmentDurationPredicate(
                                threshold=0.2,
                                comparison=control.ComparisonType('>'),
                            ),
                        ],
                    ),
                ],
            )

        assert str(e.value) == 'Nested expressions are not allowed'


class TestRuleBuilder:
    def test_static_reward(self):
        expected_rules = [
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('>=')),
                action=control.SetAssignmentStatus(status=Assignment.ACCEPTED),
            ),
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('<')),
                action=control.SetAssignmentStatus(status=Assignment.REJECTED),
            ),
        ]

        rules = control.RuleBuilder().add_static_reward(threshold=0.7).build()

        assert rules == expected_rules

    def test_dynamic_reward_single_split(self):
        expected_rules = [
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.1, comparison=control.ComparisonType('>=')),
                action=control.SetAssignmentStatus(status=Assignment.ACCEPTED),
            ),
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.1, comparison=control.ComparisonType('<')),
                action=control.SetAssignmentStatus(status=Assignment.REJECTED),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('>='))
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.03),
            ),
        ]

        rules = (
            control.RuleBuilder()
            .add_dynamic_reward(
                min_accuracy_for_accept=0.1,
                min_accuracy_for_bonus=0.7,
                min_bonus_amount_usd=0.03,
                max_bonus_amount_usd=0.03,
                bonus_granularity_num=1,
            )
            .build()
        )

        assert rules == expected_rules

    def test_dynamic_reward_default_min_bonus_accuracy(self):
        expected_rules = [
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.0, comparison=control.ComparisonType('>=')),
                action=control.SetAssignmentStatus(status=Assignment.ACCEPTED),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.0, comparison=control.ComparisonType('>=')),
                        control.AssignmentAccuracyPredicate(threshold=0.25, comparison=control.ComparisonType('<')),
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.03),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.25, comparison=control.ComparisonType('>=')),
                        control.AssignmentAccuracyPredicate(threshold=0.5, comparison=control.ComparisonType('<')),
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.04),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.5, comparison=control.ComparisonType('>=')),
                        control.AssignmentAccuracyPredicate(threshold=0.75, comparison=control.ComparisonType('<')),
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.05),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.75, comparison=control.ComparisonType('>='))
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.06),
            ),
        ]

        rules = (
            control.RuleBuilder()
            .add_dynamic_reward(
                min_bonus_amount_usd=0.03,
                max_bonus_amount_usd=0.06,
                bonus_granularity_num=4,
            )
            .build()
        )

        assert rules == expected_rules

    def test_dynamic_reward_granular(self):
        expected_rules = [
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.0, comparison=control.ComparisonType('>=')),
                action=control.SetAssignmentStatus(status=Assignment.ACCEPTED),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.6, comparison=control.ComparisonType('>=')),
                        control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('<')),
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.03),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('>=')),
                        control.AssignmentAccuracyPredicate(threshold=0.8, comparison=control.ComparisonType('<')),
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.04),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.8, comparison=control.ComparisonType('>=')),
                        control.AssignmentAccuracyPredicate(threshold=0.9, comparison=control.ComparisonType('<')),
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.05),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator('and'),
                    predicates=[
                        control.AssignmentAccuracyPredicate(threshold=0.9, comparison=control.ComparisonType('>='))
                    ],
                ),
                action=control.GiveBonusToUser(amount_usd=0.06),
            ),
        ]

        rules = (
            control.RuleBuilder()
            .add_dynamic_reward(
                min_accuracy_for_bonus=0.6,
                min_bonus_amount_usd=0.03,
                max_bonus_amount_usd=0.06,
                bonus_granularity_num=4,
            )
            .build()
        )

        assert rules == expected_rules

    def test_only_one_reward_type(self):
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_static_reward(0.5).add_dynamic_reward(
                min_bonus_amount_usd=0.01, max_bonus_amount_usd=0.1
            )
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_dynamic_reward(
                min_bonus_amount_usd=0.01, max_bonus_amount_usd=0.1
            ).add_static_reward(0.5)

    def test_static_reward_incorrect_thresholds(self):
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_static_reward(1.5)
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_static_reward(-1.5)

    def test_dynamic_reward_incorrect_thresholds(self):
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_dynamic_reward(min_bonus_amount_usd=1.0, max_bonus_amount_usd=0)
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_dynamic_reward(
                min_bonus_amount_usd=0.001,
                max_bonus_amount_usd=0.1,
                min_accuracy_for_bonus=0.1,
                min_accuracy_for_accept=1.0,
            )
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_dynamic_reward(
                min_bonus_amount_usd=0.01,
                max_bonus_amount_usd=0.04,
                min_accuracy_for_bonus=0.1,
                min_accuracy_for_accept=1.0,
                bonus_granularity_num=5,
            )
        with pytest.raises(AssertionError):
            control.RuleBuilder().add_dynamic_reward(
                min_bonus_amount_usd=0.0,
                max_bonus_amount_usd=0.0,
                min_accuracy_for_bonus=1.5,
                min_accuracy_for_accept=1.0,
            )

    def test_speed_control(self):
        expected_rules = [
            control.Rule(
                control.AssignmentDurationPredicate(threshold=0.2, comparison=control.ComparisonType('<=')),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL, private_comment='Fast submits, <= 0.2', duration=timedelta(days=1)
                ),
            ),
            control.Rule(
                control.AssignmentDurationPredicate(threshold=0.2, comparison=control.ComparisonType('<=')),
                action=control.SetAssignmentStatus(status=Assignment.REJECTED),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator.AND,
                    predicates=[
                        control.AssignmentDurationPredicate(
                            threshold=0.5,
                            comparison=control.ComparisonType('<='),
                        ),
                        control.AssignmentDurationPredicate(
                            threshold=0.2,
                            comparison=control.ComparisonType('>'),
                        ),
                    ],
                ),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL,
                    private_comment='Fast submits, 0.2 < time <= 0.5',
                    duration=timedelta(hours=8),
                ),
            ),
        ]

        rules = control.RuleBuilder().add_speed_control(ratio_rand=0.2, ratio_poor=0.5).rules

        assert rules == expected_rules

    def test_complex_speed_control_no_blocks(self):
        rules = control.RuleBuilder().add_complex_speed_control(speed_blocks=[]).rules
        assert rules == []

    def test_complex_speed_control_one_block(self):
        expected_rules = [
            control.Rule(
                control.AssignmentDurationPredicate(threshold=0.2, comparison=control.ComparisonType('<=')),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL, private_comment='Fast submits, <= 0.2', duration=timedelta(days=1)
                ),
            ),
        ]

        rules = (
            control.RuleBuilder()
            .add_complex_speed_control(speed_blocks=[control.BlockTimePicker(0.2, '1d', False)])
            .rules
        )

        assert rules == expected_rules

    def test_complex_speed_control_unordered_block(self):
        expected_rules = [
            control.Rule(
                control.AssignmentDurationPredicate(threshold=0.1, comparison=control.ComparisonType('<=')),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL, private_comment='Fast submits, <= 0.1', duration=timedelta(days=2)
                ),
            ),
            control.Rule(
                control.AssignmentDurationPredicate(threshold=0.1, comparison=control.ComparisonType('<=')),
                action=control.SetAssignmentStatus(status=Assignment.REJECTED),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator.AND,
                    predicates=[
                        control.AssignmentDurationPredicate(
                            threshold=0.2,
                            comparison=control.ComparisonType('<='),
                        ),
                        control.AssignmentDurationPredicate(
                            threshold=0.1,
                            comparison=control.ComparisonType('>'),
                        ),
                    ],
                ),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL,
                    private_comment='Fast submits, 0.1 < time <= 0.2',
                    duration=timedelta(days=1),
                ),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator.AND,
                    predicates=[
                        control.AssignmentDurationPredicate(
                            threshold=0.5,
                            comparison=control.ComparisonType('<='),
                        ),
                        control.AssignmentDurationPredicate(
                            threshold=0.2,
                            comparison=control.ComparisonType('>'),
                        ),
                    ],
                ),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL,
                    private_comment='Fast submits, 0.2 < time <= 0.5',
                    duration=timedelta(minutes=30),
                ),
            ),
        ]

        rules = (
            control.RuleBuilder()
            .add_complex_speed_control(
                speed_blocks=[
                    control.BlockTimePicker(0.2, '1d', False),
                    control.BlockTimePicker(0.1, '2d', True),
                    control.BlockTimePicker(0.5, '30m', False),
                ],
            )
            .rules
        )

        assert rules == expected_rules

    def test_control_task_control_no_hard_block(self):
        rules = (
            control.RuleBuilder()
            .add_control_task_control(
                control_task_count=10,
                control_task_correct_count_for_hard_block=0,
                control_task_correct_count_for_soft_block=2,
            )
            .rules
        )
        expected_rules = [
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator.AND,
                    predicates=[
                        control.AssignmentAccuracyPredicate(
                            threshold=0.0, comparison=control.ComparisonType.GREATER_OR_EQUAL
                        ),
                        control.AssignmentAccuracyPredicate(threshold=0.2, comparison=control.ComparisonType.LESS),
                    ],
                ),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL,
                    private_comment='Control tasks: [0, 2) done correctly',
                    duration=timedelta(hours=1),
                ),
            ),
        ]
        assert rules == expected_rules

    def test_control_task_control_with_hard_block(self):
        rules = (
            control.RuleBuilder()
            .add_control_task_control(
                control_task_count=10,
                control_task_correct_count_for_hard_block=2,
                control_task_correct_count_for_soft_block=5,
            )
            .rules
        )
        expected_rules = [
            control.Rule(
                predicate=control.AssignmentAccuracyPredicate(threshold=0.2, comparison=control.ComparisonType.LESS),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL,
                    private_comment='Control tasks: [0, 2) done correctly',
                    duration=timedelta(hours=8),
                ),
            ),
            control.Rule(
                predicate=control.PredicateExpression(
                    boolean_operator=control.BooleanOperator.AND,
                    predicates=[
                        control.AssignmentAccuracyPredicate(
                            threshold=0.2, comparison=control.ComparisonType.GREATER_OR_EQUAL
                        ),
                        control.AssignmentAccuracyPredicate(threshold=0.5, comparison=control.ComparisonType.LESS),
                    ],
                ),
                action=control.BlockUser(
                    scope=UserRestriction.Scope.POOL,
                    private_comment='Control tasks: [2, 5) done correctly',
                    duration=timedelta(hours=1),
                ),
            ),
        ]
        assert rules == expected_rules


class TestControl:
    def test_control_filter_rules_basic(self):
        accept_rule = control.Rule(
            predicate=control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('>=')),
            action=control.SetAssignmentStatus(status=Assignment.ACCEPTED),
        )
        reject_rule = control.Rule(
            predicate=control.AssignmentAccuracyPredicate(threshold=0.7, comparison=control.ComparisonType('<')),
            action=control.SetAssignmentStatus(status=Assignment.REJECTED),
        )
        block_rule = control.Rule(
            predicate=control.AssignmentAccuracyPredicate(threshold=0.3, comparison=control.ComparisonType('<')),
            action=control.BlockUser(private_comment='Bad performance', scope=UserRestriction.PROJECT),
        )
        speed_block_rule = control.Rule(
            predicate=control.AssignmentDurationPredicate(threshold=0.5, comparison=control.ComparisonType('<=')),
            action=control.BlockUser(private_comment='Fast submits', scope=UserRestriction.PROJECT),
        )
        bonus_rule = control.Rule(
            predicate=control.AssignmentAccuracyPredicate(threshold=0.9, comparison=control.ComparisonType('>')),
            action=control.GiveBonusToUser(amount_usd=0.03),
        )

        ctrl = control.Control(rules=[accept_rule, reject_rule, block_rule, speed_block_rule, bonus_rule])

        for predicate_type, action_type, rules in [
            (control.AssignmentAccuracyPredicate, control.SetAssignmentStatus, [accept_rule, reject_rule]),
            (control.AssignmentAccuracyPredicate, control.BlockUser, [block_rule]),
            (control.AssignmentAccuracyPredicate, control.GiveBonusToUser, [bonus_rule]),
        ]:
            assert ctrl.filter_rules(predicate_type=predicate_type, action_type=action_type) == rules

    def test_control_filter_rules_expression(self):
        block_rule = control.Rule(
            predicate=control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.AssignmentAccuracyPredicate(threshold=0.3, comparison=control.ComparisonType('<')),
                    control.AssignmentAccuracyPredicate(threshold=0.1, comparison=control.ComparisonType('>=')),
                ],
            ),
            action=control.BlockUser(private_comment='Bad performance', scope=UserRestriction.PROJECT),
        )
        speed_block_rule = control.Rule(
            predicate=control.AssignmentDurationPredicate(threshold=0.5, comparison=control.ComparisonType('<=')),
            action=control.BlockUser(private_comment='Fast submits', scope=UserRestriction.PROJECT),
        )
        bonus_rule = control.Rule(
            predicate=control.PredicateExpression(
                boolean_operator=control.BooleanOperator.AND,
                predicates=[
                    control.AssignmentAccuracyPredicate(threshold=0.9, comparison=control.ComparisonType('>')),
                    control.AssignmentAccuracyPredicate(threshold=0.95, comparison=control.ComparisonType('<=')),
                ],
            ),
            action=control.GiveBonusToUser(amount_usd=0.03),
        )

        ctrl = control.Control(rules=[block_rule, speed_block_rule, bonus_rule])

        for predicate_type, action_type, rules in [
            (control.AssignmentAccuracyPredicate, control.BlockUser, [block_rule]),
            (control.AssignmentAccuracyPredicate, control.GiveBonusToUser, [bonus_rule]),
        ]:
            assert ctrl.filter_rules(predicate_type=predicate_type, action_type=action_type) == rules
