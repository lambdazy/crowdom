import datetime
import decimal
from itertools import chain
from mock import patch

import toloka.client as toloka

from crowdom import (
    base,
    classification,
    classification_loop,
    evaluation,
    feedback_loop,
    pool as pool_config,
    worker,
)
from crowdom.objects import Text
from crowdom.control import Control, RuleBuilder
from crowdom.duration import get_const_task_duration_function

from .stub import TolokaClientStub
from .data import (
    markup_task_mapping,
    check_task_mapping,
    pool_input_objects,
    markup_assignments_by_iterations,
    check_assignments_by_iterations,
    speed_markup_assignments_by_iterations,
    speed_check_assignments_by_iterations,
    markup_pool_id,
    check_pool_id,
    control_audios,
    markup_project,
    check_project,
)

false, true = base.BinaryEvaluation(ok=False), base.BinaryEvaluation(ok=True)

"""
Перечислим случаи, которые надо проверить.

Виды решений:
- Верное решение получено на первой итерации
- Верное решение получено на второй итерации
- Верное решение получено на третьей (последней) итерации
- Финализация объекта без явной проверки на качественной странице заданий
- Верное решение не получено из-за достижения критериев останова
- Вердикт для решения неизвестен (неполная проверка страниц заданий)
- Решение на ранней итерации не было проверено, но оно же было проверено на поздней
  итерации, что отразилось на оценке страницы заданий разметки с ранней итерации.

Общая механика:
- Корректность агрегации оценок и вычисления confidence
- Игнорирование оценок отклоненных страниц заданий пула проверки
- Поступление решения, которое было проверено ранее.
  Если решение неверное, оно все равно увеличивает object_markup_attempts.
- Верные решения из отклоненных страниц заданий разметки учитываются.
- Динамическая оплата страниц заданий разметки

Настройки:
- Страница заданий пула разметки
  - 6 заданий на странице, из них 4 проверяется
  - Для приемки выполнить правильно 2 задание из 4
- Агрегация: простое перекрытие оценок, 2 ОК из 3 для приемки решения
- Критерий останова: максимальное число попыток разметки объекта = 3
"""


@patch('crowdom.control.rule.datetime', wraps=datetime)
@patch('crowdom.evaluation.shuffle')
def test_integration(shuffle, mock_datetime):  # noqa
    stub = TolokaClientStub(
        markup_assignments_by_iterations, check_assignments_by_iterations, markup_project, check_project
    )
    tasks_to_check = 4
    assignment_start = datetime.datetime(year=2020, month=10, day=5, hour=13, minute=15)
    mock_datetime.datetime.now.return_value = assignment_start
    fb_loop = feedback_loop.FeedbackLoop(
        pool_input_objects=pool_input_objects,
        markup_task_mapping=markup_task_mapping,
        check_task_mapping=check_task_mapping,
        check_params=classification_loop.Params(
            aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
            control=feedback_loop.Control(rules=RuleBuilder().add_static_reward(threshold=0.5).build()),
            overlap=classification_loop.StaticOverlap(overlap=3),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        markup_params=feedback_loop.Params(
            control=Control(
                rules=RuleBuilder()
                .add_dynamic_reward(
                    min_bonus_amount_usd=0.01,
                    max_bonus_amount_usd=0.02,
                    min_accuracy_for_accept=0.5,
                    min_accuracy_for_bonus=0.6,
                    bonus_granularity_num=2,
                )
                .add_control_task_control(tasks_to_check, 1, 2)
                .build()
            ),
            assignment_check_sample=evaluation.AssignmentCheckSample(
                max_tasks_to_check=tasks_to_check, assignment_accuracy_finalization_threshold=0.5
            ),
            overlap=classification_loop.DynamicOverlap(min_overlap=1, max_overlap=3, confidence=0.6),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        client=stub,  # noqa
        lang='EN',
    )

    markup_pool_config = pool_config.MarkupConfig(
        project_id=markup_project.id,
        private_name=markup_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=20),
        real_tasks_count=6,
        control_params=fb_loop.markup_params.control,
    )
    check_pool_config = pool_config.ClassificationConfig(
        project_id=check_project.id,
        private_name=check_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=20),
        real_tasks_count=12,
        control_tasks_count=1,
        overlap=3,
        control_params=fb_loop.check_params.control,
    )

    markup_pool, check_pool = fb_loop.create_pools(control_audios, markup_pool_config, check_pool_config)

    assert markup_pool.id == markup_pool_id
    assert check_pool.id == check_pool_id

    fb_loop.loop(markup_pool.id, check_pool.id)

    object_results, worker_weights = fb_loop.get_results(markup_pool.id, check_pool.id)

    markup_assignment_0_accuracy = 1 / 5
    markup_assignment_0_evaluation_recall = 5 / 6

    markup_assignment_1_accuracy = 0 / 4
    markup_assignment_1_evaluation_recall = 4 / 6

    markup_assignment_2_accuracy = 2 / 4
    markup_assignment_2_evaluation_recall = 4 / 6

    markup_assignment_3_accuracy = 1 / 4
    markup_assignment_3_evaluation_recall = 4 / 4

    markup_assignment_4_accuracy = 3 / 4
    markup_assignment_4_evaluation_recall = 4 / 6

    markup_assignment_5_accuracy = 1 / 5
    markup_assignment_5_evaluation_recall = 5 / 6

    markup_assignment_6_accuracy = 0 / 4
    markup_assignment_6_evaluation_recall = 4 / 4

    markup_assignment_7_accuracy = 1 / 5
    markup_assignment_7_evaluation_recall = 5 / 6

    markup_assignment_8_accuracy = 2 / 4
    markup_assignment_8_evaluation_recall = 4 / 4

    check_workers = [worker.Human(assignment=assignment) for assignment in chain(*check_assignments_by_iterations)]
    markup_workers = [worker.Human(assignment=assignment) for assignment in chain(*markup_assignments_by_iterations)]

    expected_results = [
        [
            feedback_loop.Solution(
                solution=(Text(text='семнадцать'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[4],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[5]), (true, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_4_accuracy,
                assignment_evaluation_recall=markup_assignment_4_evaluation_recall,
            ),
            feedback_loop.Solution(
                # The solution was not checked at first, but was checked on the next iteration and was substituted
                # automatically.
                solution=(Text(text='семнадцать'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[5]), (true, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='? семнадцать'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(true, check_workers[8]), (false, check_workers[9]), (false, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='а нет не надо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[4],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(true, check_workers[5]), (false, check_workers[6]), (true, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_4_accuracy,
                assignment_evaluation_recall=markup_assignment_4_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='нет надо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[0]), (true, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='хорошо до свидания'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(true, check_workers[0]), (true, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='нет'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[4],
                evaluation=None,
                assignment_accuracy=markup_assignment_4_accuracy,
                assignment_evaluation_recall=markup_assignment_4_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='не'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[0]), (false, check_workers[2]), (false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='абонент не'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[4],
                evaluation=None,
                assignment_accuracy=markup_assignment_4_accuracy,
                assignment_evaluation_recall=markup_assignment_4_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='абонент'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[0],
                evaluation=None,
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='я уже оплатил'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[4],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(false, check_workers[5]), (true, check_workers[6]), (true, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_4_accuracy,
                assignment_evaluation_recall=markup_assignment_4_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='я оплатил'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[0]), (false, check_workers[2]), (true, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='где'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[4],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(true, check_workers[5]), (true, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_4_accuracy,
                assignment_evaluation_recall=markup_assignment_4_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='?'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[0]), (false, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=markup_assignment_1_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='а где посмотреть на мой счет'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=3 / 3,
                    worker_labels=[(true, check_workers[8]), (true, check_workers[9]), (true, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='а где посмотреть мой счет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[5]), (false, check_workers[6]), (true, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='где посмотреть какой счет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(true, check_workers[0]), (false, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=markup_assignment_1_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='два три пять восемь'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(true, check_workers[5]), (true, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='два три пять'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[1],
                evaluation=None,
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=markup_assignment_1_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='спасибо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[0]), (true, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='не спасибо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[8]), (false, check_workers[9]), (true, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='спасибо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[0]), (true, check_workers[1]), (false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=markup_assignment_1_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='улица гончарова'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[7],
                evaluation=None,
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='улица ?'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(true, check_workers[5]), (false, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='улица горчакова'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[1],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[0]), (false, check_workers[1]), (true, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=markup_assignment_1_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='перезвоните познее'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[5],
                evaluation=None,
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='перезвоните позднее'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[1],
                evaluation=None,
                assignment_accuracy=markup_assignment_1_accuracy,
                assignment_evaluation_recall=markup_assignment_1_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='перезвните позднее'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[
                        (false, check_workers[8]),
                        (false, check_workers[9]),
                        (false, check_workers[10]),
                    ],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='восемь четыре'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[2],
                evaluation=None,
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='алло'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=3 / 3,
                    worker_labels=[(true, check_workers[0]), (true, check_workers[1]), (true, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='абонент временно недоступен'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[2],
                evaluation=None,
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='?'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[0]), (false, check_workers[1]), (false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='ха'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[5]), (false, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='?'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[0]), (false, check_workers[1]), (false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='я смотрю сейчас на свой счет'),),
                worker=markup_workers[8],
                verdict=feedback_loop.SolutionVerdict.OK,
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(false, check_workers[8]), (true, check_workers[9]), (true, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_8_accuracy,
                assignment_evaluation_recall=markup_assignment_8_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='я смотрю сейчас насчет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(true, check_workers[0]), (false, check_workers[1]), (false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='я смотрю сейчас счет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[6],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[5]), (false, check_workers[6]), (true, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_6_accuracy,
                assignment_evaluation_recall=markup_assignment_6_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='да'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(true, check_workers[0]), (false, check_workers[1]), (true, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='? да'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[8],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[8]), (true, check_workers[9]), (false, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_8_accuracy,
                assignment_evaluation_recall=markup_assignment_8_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='суббот'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[1]), (false, check_workers[2]), (false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='?'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[6],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[5]), (false, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_6_accuracy,
                assignment_evaluation_recall=markup_assignment_6_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='нет не нужно'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[8],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(true, check_workers[8]), (false, check_workers[9]), (true, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_8_accuracy,
                assignment_evaluation_recall=markup_assignment_8_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='не нужно'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(true, check_workers[1]), (false, check_workers[2]), (false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='ни нужно'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[6],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0 / 3,
                    worker_labels=[(false, check_workers[5]), (false, check_workers[6]), (false, check_workers[7])],
                ),
                assignment_accuracy=markup_assignment_6_accuracy,
                assignment_evaluation_recall=markup_assignment_6_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='да хорошо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=2 / 3,
                    worker_labels=[(false, check_workers[2]), (true, check_workers[3]), (true, check_workers[4])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='один четыре восемь'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[8],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[8]), (true, check_workers[9]), (false, check_workers[10])],
                ),
                assignment_accuracy=markup_assignment_8_accuracy,
                assignment_evaluation_recall=markup_assignment_8_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='четыре четыре шесть восемь'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[2]), (true, check_workers[3]), (false, check_workers[4])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='четыре четыре шесть восемь'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[6],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=1 / 3,
                    worker_labels=[(false, check_workers[2]), (true, check_workers[3]), (false, check_workers[4])],
                ),
                assignment_accuracy=markup_assignment_6_accuracy,
                assignment_evaluation_recall=markup_assignment_6_evaluation_recall,
            ),
        ],
    ]
    assert object_results == expected_results

    expected_calls = (
        [
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav')",
                            },
                            id=f'task {audio_index}',
                            pool_id='markup pool',
                        )
                        for audio_index in range(22)
                    ],
                ),
            ),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': 'https://storage.net/82.wav',
                                'output': 'алло',
                                'id': "Audio(url='https://storage.net/82.wav') Text(text='алло')",
                            },
                            known_solutions=[
                                toloka.Task.KnownSolution(output_values={'ok': True}, correctness_weight=1)
                            ],
                            id='task 22',
                            infinite_overlap=True,
                            pool_id='check pool',
                        ),
                    ],
                ),
            ),
            ('open_pool', ('markup pool',)),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {23 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (1, 'нет надо', 0),
                                (2, 'хорошо до свидания', 0),
                                (3, 'не', 0),
                                (5, 'я оплатил', 0),
                                (6, '?', 1),
                                (7, 'где посмотреть какой счет', 1),
                                (9, 'спасибо', 1),
                                (10, 'улица горчакова', 1),
                                (13, 'алло', 2),
                                (15, '?', 2),
                                (16, 'я смотрю сейчас насчет', 2),
                                (17, 'да', 2),
                                (18, 'суббот', 3),
                                (19, 'не нужно', 3),
                                (20, 'да хорошо', 3),
                                (21, 'четыре четыре шесть восемь', 3),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 0',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 1',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 2',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 3',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 4',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Control tasks: [1, 2) done correctly',
                        pool_id='markup pool',
                        user_id='markup-0',
                        will_expire=assignment_start + datetime.timedelta(minutes=1) + datetime.timedelta(hours=1),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 0',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 3, 4. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Control tasks: [0, 1) done correctly',
                        pool_id='markup pool',
                        user_id='markup-1',
                        will_expire=assignment_start + datetime.timedelta(minutes=1) + datetime.timedelta(hours=8),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 1',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 2, 3, 4. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 2',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Control tasks: [1, 2) done correctly',
                        pool_id='markup pool',
                        user_id='markup-3',
                        will_expire=assignment_start + datetime.timedelta(minutes=1) + datetime.timedelta(hours=1),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 3',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 2, 4. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
        ]
        + [
            ('patch_task_overlap_or_min', (f'task {task}', toloka.task.TaskOverlapPatch(overlap=2)))
            for task in [1, 3, 5, 0, 4, 6, 7, 9, 10, 8, 11, 15, 16, 18, 19, 21]
        ]
        + [
            ('open_pool', ('markup pool',)),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {39 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (0, 'семнадцать', 4),
                                (1, 'а нет не надо', 4),
                                (5, 'я уже оплатил', 4),
                                (6, 'где', 4),
                                (7, 'а где посмотреть мой счет', 5),
                                (8, 'два три пять восемь', 5),
                                (10, 'улица ?', 5),
                                (15, 'ха', 5),
                                (16, 'я смотрю сейчас счет', 6),
                                (18, '?', 6),
                                (19, 'ни нужно', 6),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 5',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 6',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 7',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 4',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Control tasks: [0, 1) done correctly',
                        pool_id='markup pool',
                        user_id='markup-5',
                        will_expire=assignment_start + datetime.timedelta(minutes=1) + datetime.timedelta(hours=8),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 5',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 2, 4, 5. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Control tasks: [0, 1) done correctly',
                        pool_id='markup pool',
                        user_id='markup-6',
                        will_expire=assignment_start + datetime.timedelta(minutes=1) + datetime.timedelta(hours=8),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 6',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 2, 3, 4. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
        ]
        + [
            ('patch_task_overlap_or_min', (f'task {task}', toloka.task.TaskOverlapPatch(overlap=3)))
            for task in [0, 7, 9, 10, 11, 15, 16, 18, 19, 21]
        ]
        + [
            ('open_pool', ('markup pool',)),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {50 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (0, '? семнадцать', 7),
                                (7, 'а где посмотреть на мой счет', 7),
                                (9, 'не спасибо', 7),
                                (11, 'перезвните позднее', 7),
                                (16, 'я смотрю сейчас на свой счет', 8),
                                (18, '? да', 8),
                                (19, 'нет не нужно', 8),
                                (21, 'один четыре восемь', 8),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 8',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 9',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'check assignment 10',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Control tasks: [0, 1) done correctly',
                        pool_id='markup pool',
                        user_id='markup-7',
                        will_expire=assignment_start + datetime.timedelta(minutes=1) + datetime.timedelta(hours=8),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 7',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 3, 4, 5. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 8',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'create_user_bonuses_async',
                (
                    [
                        toloka.user_bonus.UserBonus(
                            assignment_id='markup assignment 4',
                            user_id='markup-4',
                            amount=decimal.Decimal(0.01),
                            without_message=True,
                        ),
                    ],
                ),
            ),
            (
                'wait_operation',
                (toloka.operations.UserBonusCreateBatchOperation(status=toloka.operations.Operation.Status.SUCCESS),),
            ),
        ]
    )
    assert stub.calls[1:2] + stub.calls[3:] == expected_calls  # skip pools creation

    assert worker_weights is None  # MAJORITY_VOTE static overlap


@patch('crowdom.control.rule.datetime', wraps=datetime)
@patch('crowdom.evaluation.shuffle')
def test_integration_speed_control(shuffle, mock_datetime):  # noqa
    stub = TolokaClientStub(
        speed_markup_assignments_by_iterations, speed_check_assignments_by_iterations, markup_project, check_project
    )
    tasks_to_check = 3
    assignment_start = datetime.datetime(year=2020, month=10, day=5, hour=13, minute=15)
    mock_datetime.datetime.now.return_value = assignment_start

    fb_loop = feedback_loop.FeedbackLoop(
        pool_input_objects=pool_input_objects[:9],
        markup_task_mapping=markup_task_mapping,
        check_task_mapping=check_task_mapping,
        check_params=classification_loop.Params(
            aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
            control=feedback_loop.Control(rules=RuleBuilder().add_static_reward(threshold=0.5).build()),
            overlap=classification_loop.StaticOverlap(overlap=1),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        markup_params=feedback_loop.Params(
            control=Control(
                rules=RuleBuilder()
                .add_static_reward(0.5)
                .add_control_task_control(tasks_to_check, 0, 1)
                .add_speed_control(ratio_rand=0.1, ratio_poor=0.5)
                .build()
            ),
            assignment_check_sample=evaluation.AssignmentCheckSample(
                max_tasks_to_check=tasks_to_check, assignment_accuracy_finalization_threshold=1.0
            ),
            overlap=classification_loop.DynamicOverlap(min_overlap=1, max_overlap=2, confidence=0.6),
            task_duration_function=get_const_task_duration_function(datetime.timedelta(seconds=20)),
        ),
        client=stub,  # noqa
        lang='EN',
    )
    markup_pool_config = pool_config.MarkupConfig(
        project_id=markup_project.id,
        private_name=markup_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=20),
        real_tasks_count=4,
        control_params=fb_loop.markup_params.control,
    )
    check_pool_config = pool_config.ClassificationConfig(
        project_id=check_project.id,
        private_name=check_pool_id,
        reward_per_assignment=0.03,
        task_duration_hint=datetime.timedelta(seconds=20),
        real_tasks_count=6,
        control_tasks_count=1,
        overlap=1,
        control_params=fb_loop.check_params.control,
    )

    markup_pool, check_pool = fb_loop.create_pools(control_audios, markup_pool_config, check_pool_config)

    assert markup_pool.id == markup_pool_id
    assert check_pool.id == check_pool_id

    fb_loop.loop(markup_pool.id, check_pool.id)
    object_results, worker_weights = fb_loop.get_results(markup_pool.id, check_pool.id)

    markup_assignment_0_accuracy = 1 / 3
    markup_assignment_0_evaluation_recall = 3 / 4

    # markup assignment 1 rejected by prior filter, too fast
    markup_assignment_2_accuracy = 1 / 1
    markup_assignment_2_evaluation_recall = 1 / 1

    markup_assignment_3_accuracy = 2 / 3
    markup_assignment_3_evaluation_recall = 3 / 4

    # markup assignment 4 rejected by prior filter, too fast
    markup_assignment_5_accuracy = 3 / 4
    markup_assignment_5_evaluation_recall = 1 / 1

    markup_assignment_6_accuracy = 1 / 1
    markup_assignment_6_evaluation_recall = 1 / 1

    markup_assignment_7_accuracy = 1 / 2
    markup_assignment_7_evaluation_recall = 2 / 2

    check_workers = [worker.Human(assignment=assignment) for assignment in chain(*check_assignments_by_iterations)]
    markup_workers = [worker.Human(assignment=assignment) for assignment in chain(*markup_assignments_by_iterations)]

    expected_results = [
        [
            feedback_loop.Solution(
                solution=(Text(text='семнадцать'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[0])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='не надо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='нет надо'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0.0,
                    worker_labels=[(false, check_workers[0])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='хорошо да до свидания'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[6],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_6_accuracy,
                assignment_evaluation_recall=markup_assignment_6_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='хорошо до свидания'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[0],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0.0,
                    worker_labels=[(false, check_workers[0])],
                ),
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='не спасибо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='не спасибо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='нет спа'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[0],
                evaluation=None,
                assignment_accuracy=markup_assignment_0_accuracy,
                assignment_evaluation_recall=markup_assignment_0_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='спасибо'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[1])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='улица горчакова'),),
                verdict=feedback_loop.SolutionVerdict.UNKNOWN,
                worker=markup_workers[3],
                evaluation=None,
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='на улице горчакова'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0.0,
                    worker_labels=[(false, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='на уличке горчакова'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[7],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0.0,
                    worker_labels=[(false, check_workers[3])],
                ),
                assignment_accuracy=markup_assignment_7_accuracy,
                assignment_evaluation_recall=markup_assignment_7_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='да конечно'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[1])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='а где посмотреть на мой счет'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[5],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[2])],
                ),
                assignment_accuracy=markup_assignment_5_accuracy,
                assignment_evaluation_recall=markup_assignment_5_evaluation_recall,
            ),
            feedback_loop.Solution(
                solution=(Text(text='где посмотреть какой счет'),),
                verdict=feedback_loop.SolutionVerdict.BAD,
                worker=markup_workers[3],
                evaluation=evaluation.SolutionEvaluation(
                    ok=False,
                    confidence=0.0,
                    worker_labels=[(false, check_workers[1])],
                ),
                assignment_accuracy=markup_assignment_3_accuracy,
                assignment_evaluation_recall=markup_assignment_3_evaluation_recall,
            ),
        ],
        [
            feedback_loop.Solution(
                solution=(Text(text='алло'),),
                verdict=feedback_loop.SolutionVerdict.OK,
                worker=markup_workers[2],
                evaluation=evaluation.SolutionEvaluation(
                    ok=True,
                    confidence=1.0,
                    worker_labels=[(true, check_workers[0])],
                ),
                assignment_accuracy=markup_assignment_2_accuracy,
                assignment_evaluation_recall=markup_assignment_2_evaluation_recall,
            ),
        ],
    ]
    assert object_results == expected_results

    expected_calls = (
        [
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav')",
                            },
                            id=f'task {audio_index}',
                            pool_id='markup pool',
                        )
                        for audio_index in range(9)
                    ],
                ),
            ),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': 'https://storage.net/82.wav',
                                'output': 'алло',
                                'id': "Audio(url='https://storage.net/82.wav') Text(text='алло')",
                            },
                            known_solutions=[
                                toloka.Task.KnownSolution(output_values={'ok': True}, correctness_weight=1)
                            ],
                            id='task 9',
                            infinite_overlap=True,
                            pool_id='check pool',
                        ),
                    ],
                ),
            ),
            ('open_pool', ('markup pool',)),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Fast submits, <= 0.1',
                        pool_id='markup pool',
                        user_id='markup-1',
                        will_expire=assignment_start + datetime.timedelta(seconds=3) + datetime.timedelta(days=1),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 1',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Too few correct solutions',
                    ),
                ),
            ),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {10 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (1, 'нет надо', 0),
                                (2, 'хорошо до свидания', 0),
                                (0, 'семнадцать', 0),
                                (8, 'алло', 2),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 0',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 0',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Check the tasks with numbers: 1, 2. Learn more about tasks acceptance and filing '
                        'appeals in the project instructions.',
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 2',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
        ]
        + [
            ('patch_task_overlap_or_min', (f'task {task}', toloka.task.TaskOverlapPatch(overlap=2)))
            for task in [1, 2, 3, 6, 7, 4, 5]
        ]
        + [
            ('open_pool', ('markup pool',)),
            (
                'set_user_restriction',
                (
                    toloka.user_restriction.PoolUserRestriction(
                        private_comment='Fast submits, <= 0.1',
                        pool_id='markup pool',
                        user_id='markup-4',
                        will_expire=assignment_start + datetime.timedelta(seconds=3) + datetime.timedelta(days=1),
                    ),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 4',
                    toloka.assignment.AssignmentPatch(
                        status=toloka.Assignment.REJECTED,
                        public_comment='Too few correct solutions',
                    ),
                ),
            ),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {14 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (6, 'да конечно', 3),
                                (4, 'спасибо', 3),
                                (7, 'где посмотреть какой счет', 3),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 1',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 3',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
        ]
        + [
            ('patch_task_overlap_or_min', (f'task {task}', toloka.task.TaskOverlapPatch(overlap=3)))
            for task in [1, 2, 3, 7, 5]
        ]
        + [
            ('open_pool', ('markup pool',)),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {17 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (1, 'не надо', 5),
                                (7, 'а где посмотреть на мой счет', 5),
                                (5, 'на улице горчакова', 5),
                                (2, 'хорошо да до свидания', 6),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 2',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 5',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 6',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'create_tasks',
                (
                    [
                        toloka.Task(
                            input_values={
                                'audio_link': f'https://storage.net/{audio_index:02d}.wav',
                                'output': f'{text}',
                                'id': f"Audio(url='https://storage.net/{audio_index:02d}.wav') " f"Text(text='{text}')",
                            },
                            id=f'task {21 + i}',
                            pool_id='check pool',
                            unavailable_for=[f'markup-{user_id}'],
                        )
                        for i, (audio_index, text, user_id) in enumerate(
                            [
                                (5, 'на уличке горчакова', 7),
                                (3, 'не спасибо', 7),
                            ]
                        )
                    ],
                ),
            ),
            ('open_pool', ('check pool',)),
            (
                'patch_assignment',
                (
                    'check assignment 3',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
            (
                'patch_assignment',
                (
                    'markup assignment 7',
                    toloka.assignment.AssignmentPatch(status=toloka.Assignment.ACCEPTED, public_comment=''),
                ),
            ),
        ]
    )
    assert stub.calls[1:2] + stub.calls[3:] == expected_calls  # skip pools creation

    assert worker_weights is None  # MAJORITY_VOTE static overlap
