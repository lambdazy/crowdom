from datetime import timedelta
from mock import patch
from pytest import approx, raises

from crowdom import base, classification_loop, evaluation, mapping, objects, pricing
from . import lib

stub_mapping = task_mapping = mapping.TaskMapping(
    input_mapping=(),
    output_mapping=(
        mapping.ObjectMapping(obj_meta=base.ObjectMeta(lib.ImageClass), obj_task_fields=(('value', 'choice'),)),
    ),
)

annotation_stub_mapping = mapping.TaskMapping(
    input_mapping=(
        mapping.ObjectMapping(obj_meta=base.ObjectMeta(objects.Audio), obj_task_fields=(('url', 'audio'),)),
    ),
    output_mapping=(
        mapping.ObjectMapping(obj_meta=base.ObjectMeta(objects.Text), obj_task_fields=(('text', 'transcript'),)),
    ),
)


class TestClassification:
    def test_pricing(self):
        options = pricing.get_pricing_options(
            task_duration_hint=timedelta(seconds=9),
            pricing_strategy=pricing.StaticPricingStrategy(),
            lang='RU',
            task_mapping=stub_mapping,
        )

        assert options[0] == pricing.PoolPricingConfigWithCalculatedProperties(
            config=pricing.PoolPricingConfig(assignment_price=0.006, real_tasks_count=3, control_tasks_count=1),
            price_per_hour=0.006 * (60 * 60 / ((3 + 1) * 9)),
            robustness=1 - 1 / 3,
            control_tasks_ratio=1 / (3 + 1),
            assignment_duration=timedelta(seconds=9 * (3 + 1)),
        )

        assert pricing.choose_default_option(options) == pricing.PoolPricingConfigWithCalculatedProperties(
            config=pricing.PoolPricingConfig(assignment_price=0.024, real_tasks_count=14, control_tasks_count=2),
            price_per_hour=0.024 * (60 * 60 / ((14 + 2) * 9)),
            robustness=1 - (1 / 3) ** 2,
            control_tasks_ratio=2 / (14 + 2),
            assignment_duration=timedelta(seconds=9 * (14 + 2)),
        )

        assert options[-1] == pricing.PoolPricingConfigWithCalculatedProperties(
            config=pricing.PoolPricingConfig(assignment_price=0.043, real_tasks_count=19, control_tasks_count=10),
            price_per_hour=0.043 * (60 * 60 / ((19 + 10) * 9)),
            robustness=1 - (1 / 3) ** 10,
            control_tasks_ratio=10 / (19 + 10),
            assignment_duration=timedelta(seconds=9 * (19 + 10)),
        )

    def test_pricing_with_adjustment(self):
        options = pricing.get_pricing_options(
            task_duration_hint=timedelta(seconds=9),
            pricing_strategy=pricing.StaticPricingStrategy(),
            lang='RU',
            task_mapping=stub_mapping,
            correct_control_task_ratio_for_acceptance=0.8,
        )

        assert options[0] == pricing.PoolPricingConfigWithCalculatedProperties(
            config=pricing.PoolPricingConfig(assignment_price=0.006, real_tasks_count=3, control_tasks_count=1),
            price_per_hour=0.006 * (60 * 60 / ((3 + 1) * 9)),
            robustness=1 - 1 / 3,
            control_tasks_ratio=1 / (3 + 1),
            assignment_duration=timedelta(seconds=9 * (3 + 1)),
        )

        assert (
            pricing.choose_default_option(options)
            == pricing.PoolPricingConfigWithCalculatedProperties(
                config=pricing.PoolPricingConfig(assignment_price=0.024, real_tasks_count=14, control_tasks_count=2),
                price_per_hour=0.024 * (60 * 60 / ((14 + 2) * 9)),
                robustness=1 - ((1 / 3) ** 2 * (1 - 1 / 3) ** 0),
                control_tasks_ratio=2 / (14 + 2),
                assignment_duration=timedelta(seconds=9 * (14 + 2)),
            )
            == pricing.calculate_properties_for_pricing_config(
                config=pricing.PoolPricingConfig(assignment_price=0.024, real_tasks_count=14, control_tasks_count=2),
                task_duration_hint=timedelta(seconds=9),
                correct_control_task_ratio_for_acceptance=0.8,
                task_mapping=stub_mapping,
            )
        )

        assert options[-1] == pricing.PoolPricingConfigWithCalculatedProperties(
            config=pricing.PoolPricingConfig(assignment_price=0.043, real_tasks_count=19, control_tasks_count=10),
            price_per_hour=0.043 * (60 * 60 / ((19 + 10) * 9)),
            robustness=1
            - (
                ((1 / 3) ** 8 * (1 - 1 / 3) ** 2) * 5 * 9
                + ((1 / 3) ** 9 * (1 - 1 / 3) ** 1) * 10  # C_10_8 = 10! / (8! * 2!)
                + ((1 / 3) ** 10 * (1 - 1 / 3) ** 0) * 1
            ),
            control_tasks_ratio=10 / (19 + 10),
            assignment_duration=timedelta(seconds=9 * (19 + 10)),
        )


class TestExperts:
    def test_pricing_inhouse(self):
        options = pricing.get_expert_pricing_options(task_duration_hint=timedelta(seconds=9), task_mapping=stub_mapping)

        assert options[0] == pricing.PoolPricingConfig(
            assignment_price=0.005, real_tasks_count=4, control_tasks_count=0
        )
        assert pricing.choose_default_expert_option(options, None) == pricing.PoolPricingConfig(
            assignment_price=0.005, real_tasks_count=29, control_tasks_count=0
        )
        assert options[-1] == pricing.PoolPricingConfig(
            assignment_price=0.005, real_tasks_count=29, control_tasks_count=0
        )

    def test_pricing_external(self):
        options = pricing.get_expert_pricing_options(
            task_duration_hint=timedelta(seconds=9), task_mapping=stub_mapping, avg_price_per_hour=2.5
        )

        assert options[0] == pricing.PoolPricingConfig(
            assignment_price=0.025, real_tasks_count=4, control_tasks_count=0
        )
        assert pricing.choose_default_expert_option(options, 2.5) == pricing.PoolPricingConfig(
            assignment_price=0.025, real_tasks_count=4, control_tasks_count=0
        )
        assert options[-1] == pricing.PoolPricingConfig(
            assignment_price=0.181, real_tasks_count=29, control_tasks_count=0
        )


class TestTraining:
    def test_get_options_not_enough_tasks(self):
        with raises(AssertionError) as e:
            pricing.get_training_options(task_duration_hint=timedelta(seconds=10), available_task_count=1)
        assert (
            str(e.value)
            == 'You do not have enough tasks for this training. Expected at least 18 tasks for this parameters, got 1'
        )

    def test_get_options_wrong_duration(self):
        with raises(AssertionError) as e:
            pricing.get_training_options(
                task_duration_hint=timedelta(seconds=10), available_task_count=1000, training_time=timedelta(hours=3)
            )
        assert (
            str(e.value)
            == 'You are trying to create either too short or too long training. Expected from 2 to 30 tasks, got 1080'
        )

        with raises(AssertionError) as e:
            pricing.get_training_options(
                task_duration_hint=timedelta(seconds=10), available_task_count=1000, training_time=timedelta(seconds=10)
            )
        assert (
            str(e.value)
            == 'You are trying to create either too short or too long training. Expected from 2 to 30 tasks, got 1'
        )

    def test_get_options(self):
        assert pricing.get_training_options(task_duration_hint=timedelta(seconds=10), available_task_count=1000) == [
            pricing.TrainingConfig(18, 1, timedelta(seconds=1800)),
            pricing.TrainingConfig(9, 2, timedelta(seconds=900)),
            pricing.TrainingConfig(6, 3, timedelta(seconds=600)),
            pricing.TrainingConfig(5, 4, timedelta(seconds=500)),
            pricing.TrainingConfig(4, 5, timedelta(seconds=400)),
        ]

    def test_choose_default_option(self):
        options = [
            pricing.TrainingConfig(20, 1, timedelta(seconds=600)),
            pricing.TrainingConfig(10, 2, timedelta(seconds=300)),
            pricing.TrainingConfig(5, 4, timedelta(seconds=150)),
        ]
        assert pricing.choose_default_training_option(options) == options[1]
        assert pricing.choose_default_training_option(options[:2]) == options[1]

    def test_choose_default_option_empty(self):
        with raises(AssertionError) as e:
            pricing.choose_default_training_option([])

        assert str(e.value) == 'No available options'


class TestAnnotation:
    def test_get_options(self):
        options = pricing.get_annotation_pricing_options(
            task_duration_hint=timedelta(seconds=10),
            pricing_strategy=pricing.StaticPricingStrategy(),
            lang='EN',
            task_mapping=annotation_stub_mapping,
        )
        assert len(options) == 27

        assert options[0] == pricing.PoolPricingConfig(
            assignment_price=0.008, real_tasks_count=3, control_tasks_count=0
        )
        assert options[-1] == pricing.PoolPricingConfig(
            assignment_price=0.081, real_tasks_count=29, control_tasks_count=0
        )

    def test_choose_default_option(self):
        options = [
            pricing.PoolPricingConfig(20, 1, timedelta(seconds=600)),
            pricing.PoolPricingConfig(10, 2, timedelta(seconds=300)),
            pricing.PoolPricingConfig(5, 4, timedelta(seconds=150)),
        ]
        assert pricing.choose_default_annotation_option(options) == options[1]
        assert pricing.choose_default_annotation_option(options[:2]) == options[1]

    def test_choose_default_option_empty(self):
        with raises(AssertionError) as e:
            pricing.choose_default_annotation_option([])

        assert str(e.value) == 'No available options'


class TestPoolPriceFormula:
    def test_simple(self):
        formula = pricing.PoolPriceFormula(
            input_objects_count=48,
            config=pricing.PoolPricingConfig(assignment_price=0.06, real_tasks_count=12, control_tasks_count=4),
            overlap=classification_loop.StaticOverlap(overlap=3),
        )
        assert formula.min_total_price_clear == formula.max_total_price_clear == approx(0.936)
        assert (
            formula.clear_formula()
            == r'TotalPrice_{clear} = TaskCount * PricePerTask_\$ * Overlap * (1 + TolokaCommission) = '
            r'48 * 0.0050\$ * 3 * 1.3 = 0.94\$.'
        )

        assert formula.min_total_price_precise == formula.max_total_price_clear == approx(0.936)
        assert (
            formula.precise_formula()
            == r'TotalPrice_{precise} = AssignmentCount * PricePerAssignment_\$ * Overlap = \left \lceil '
            r'\frac {TaskCount} {TasksOnAssignment} \right \rceil * (PricePerAssignment_\$ + '
            r'max(PricePerAssignment_\$ * TolokaCommission, MinTolokaCommission_\$) * Overlap = '
            r'\lceil 48 / 12 \rceil * (0.06\$ + max(0.06\$ * 0.3, 0.001\$) * 3 = 4 * 0.078 * 3 = 0.94\$.'
        )

    def test_incomplete_last_assignment(self):
        formula = pricing.PoolPriceFormula(
            input_objects_count=50,
            config=pricing.PoolPricingConfig(assignment_price=0.06, real_tasks_count=12, control_tasks_count=4),
            overlap=classification_loop.StaticOverlap(overlap=3),
        )
        assert formula.min_total_price_clear == formula.max_total_price_clear == approx(0.975)
        assert (
            formula.clear_formula()
            == r'TotalPrice_{clear} = TaskCount * PricePerTask_\$ * Overlap * (1 + TolokaCommission) = '
            r'50 * 0.0050\$ * 3 * 1.3 = 0.98\$.'
        )

        assert formula.min_total_price_precise == formula.max_total_price_precise == approx(1.17)
        assert (
            formula.precise_formula()
            == r'TotalPrice_{precise} = AssignmentCount * PricePerAssignment_\$ * Overlap = \left \lceil '
            r'\frac {TaskCount} {TasksOnAssignment} \right \rceil * (PricePerAssignment_\$ + '
            r'max(PricePerAssignment_\$ * TolokaCommission, MinTolokaCommission_\$) * Overlap = '
            r'\lceil 50 / 12 \rceil * (0.06\$ + max(0.06\$ * 0.3, 0.001\$) * 3 = 5 * 0.078 * 3 = 1.17\$.'
        )

    @patch('crowdom.pricing.min_toloka_commission', 0.005)
    def test_min_commission(self):
        formula = pricing.PoolPriceFormula(
            input_objects_count=48,
            config=pricing.PoolPricingConfig(assignment_price=0.01, real_tasks_count=12, control_tasks_count=4),
            overlap=classification_loop.StaticOverlap(overlap=3),
        )
        assert formula.min_total_price_clear == formula.max_total_price_clear == approx(0.156)
        assert (
            formula.clear_formula()
            == r'TotalPrice_{clear} = TaskCount * PricePerTask_\$ * Overlap * (1 + TolokaCommission) = '
            r'48 * 0.0008\$ * 3 * 1.3 = 0.16\$.'
        )

        assert formula.min_total_price_precise == formula.max_total_price_precise == approx(0.18)
        assert (
            formula.precise_formula()
            == r'TotalPrice_{precise} = AssignmentCount * PricePerAssignment_\$ * Overlap = \left \lceil '
            r'\frac {TaskCount} {TasksOnAssignment} \right \rceil * (PricePerAssignment_\$ + '
            r'max(PricePerAssignment_\$ * TolokaCommission, MinTolokaCommission_\$) * Overlap = '
            r'\lceil 48 / 12 \rceil * (0.01\$ + max(0.01\$ * 0.3, 0.005\$) * 3 = 4 * 0.015 * 3 = 0.18\$.'
        )

    def test_dynamic_overlap(self):
        formula = pricing.PoolPriceFormula(
            input_objects_count=50,
            config=pricing.PoolPricingConfig(assignment_price=0.06, real_tasks_count=12, control_tasks_count=4),
            overlap=classification_loop.DynamicOverlap(min_overlap=2, max_overlap=4, confidence=0.5),
        )

        assert (formula.min_total_price_clear, formula.max_total_price_clear) == (approx(0.65), approx(1.3))
        assert (formula.min_total_price_precise, formula.max_total_price_precise) == (approx(0.78), approx(1.56))

        assert (
            formula.clear_formula()
            == r'TotalPrice_{clear} = TaskCount * PricePerTask_\$ * [MinOverlap \dots MaxOverlap] * '
            r'(1 + TolokaCommission) = 50 * 0.0050\$ * [2 \dots 4] * 1.3 = 0.65\$ \dots 1.30\$.'
        )

        assert (
            formula.precise_formula()
            == r'TotalPrice_{precise} = AssignmentCount * PricePerAssignment_\$ * [MinOverlap \dots MaxOverlap] = '
            r'\left \lceil \frac {TaskCount} {TasksOnAssignment} \right \rceil * (PricePerAssignment_\$ + '
            r'max(PricePerAssignment_\$ * TolokaCommission, MinTolokaCommission_\$) * [MinOverlap \dots MaxOverlap] = '
            r'\lceil 50 / 12 \rceil * (0.06\$ + max(0.06\$ * 0.3, 0.001\$) * [2 \dots 4] = '
            r'5 * 0.078 * [2 \dots 4] = 0.78\$ \dots 1.56\$.'
        )


class TestAnnotationPriceFormula:
    def test_simple(self):
        formula = pricing.AnnotationPriceFormula(
            input_objects_count=60,
            markup_config=pricing.PoolPricingConfig(assignment_price=0.06, real_tasks_count=15, control_tasks_count=0),
            check_config=pricing.PoolPricingConfig(assignment_price=0.03, real_tasks_count=20, control_tasks_count=4),
            markup_overlap=classification_loop.DynamicOverlap(min_overlap=3, max_overlap=5, confidence=0.85),
            check_overlap=classification_loop.StaticOverlap(overlap=3),
            assignment_check_sample=None,
        )
        assert (formula.min_total_price_clear, formula.max_total_price_clear) == (approx(1.99, abs=0.01), approx(3.315))

        assert formula.clear_formula() == (
            r'MarkupTolokaComission = max \left( TolokaCommission, \frac {MinTolokaCommission} '
            r'{PricePerMarkupAssignment} \right) = max \left( 0.3, \frac {0.001}{0.06} \right) = 0.3;',
            r'MarkupPrice = MarkupTaskCount * PricePerMarkupTask_\$ * [MinMarkupOverlap \dots MaxMarkupOverlap] * '
            r'(1 + MarkupTolokaComission) = 60 * 0.0040\$ * [3 \dots 5] * 1.3 = 0.94\$ \dots 1.56\$;',
            r'CheckTaskCount = MarkupTaskCount * [MinMarkupOverlap \dots MaxMarkupOverlap] = 60 * [3 \dots 5] = '
            r'[180 \dots 300];',
            r'CheckTolokaComission = max \left( TolokaCommission, \frac {MinTolokaCommission} {PricePerCheckAssignment}'
            r' \right) = max \left( 0.3, \frac {0.001}{0.03} \right) = 0.3;',
            r'CheckPrice = CheckTaskCount * PricePerCheckTask_\$ * CheckOverlap * (1 + CheckTolokaComission) = '
            r'[180 \dots 300] * 0.0015\$ * 3 * 1.3 = 1.05\$ \dots 1.75\$;',
            r'TotalPrice = MarkupPrice + CheckPrice = 0.94\$ \dots 1.56\$ + 1.05\$ \dots 1.75\$ = 1.99\$ \dots 3.31\$.',
        )

    @patch('crowdom.pricing.min_toloka_commission', 0.005)
    def test_complex(self):
        formula = pricing.AnnotationPriceFormula(
            input_objects_count=60,
            markup_config=pricing.PoolPricingConfig(assignment_price=0.01, real_tasks_count=15, control_tasks_count=0),
            check_config=pricing.PoolPricingConfig(assignment_price=0.01, real_tasks_count=20, control_tasks_count=4),
            markup_overlap=classification_loop.DynamicOverlap(min_overlap=3, max_overlap=5, confidence=0.85),
            check_overlap=classification_loop.DynamicOverlap(min_overlap=2, max_overlap=3, confidence=0.85),
            assignment_check_sample=evaluation.AssignmentCheckSample(
                max_tasks_to_check=5, assignment_accuracy_finalization_threshold=0.6
            ),
        )
        assert (formula.min_total_price_clear, formula.max_total_price_clear) == (approx(0.27), approx(0.525))

        assert formula.clear_formula() == (
            r'MarkupTolokaComission = max \left( TolokaCommission, \frac {MinTolokaCommission} '
            r'{PricePerMarkupAssignment} \right) = max \left( 0.3, \frac {0.005}{0.01} \right) = 0.5;',
            r'MarkupPrice = MarkupTaskCount * PricePerMarkupTask_\$ * [MinMarkupOverlap \dots MaxMarkupOverlap] * '
            r'(1 + MarkupTolokaComission) = 60 * 0.0007\$ * [3 \dots 5] * 1.5 = 0.18\$ \dots 0.30\$;',
            r'CheckTaskCount = MarkupTaskCount * \frac {CheckSampleTaskCount} {MarkupTasksPerAssignment} * '
            r'[MinMarkupOverlap \dots MaxMarkupOverlap] = 60 * \frac {5} {15} * [3 \dots 5] = [60 \dots 100];',
            r'CheckTolokaComission = max \left( TolokaCommission, \frac {MinTolokaCommission} {PricePerCheckAssignment}'
            r' \right) = max \left( 0.3, \frac {0.005}{0.01} \right) = 0.5;',
            r'CheckPrice = CheckTaskCount * PricePerCheckTask_\$ * [MinCheckOverlap \dots MaxCheckOverlap] * '
            r'(1 + CheckTolokaComission) = [60 \dots 100] * 0.0005\$ * [2 \dots 3] * 1.5 = 0.09\$ \dots 0.22\$;',
            r'TotalPrice = MarkupPrice + CheckPrice = 0.18\$ \dots 0.30\$ + 0.09\$ \dots 0.22\$ = 0.27\$ \dots 0.52\$.',
        )
