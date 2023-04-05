import datetime
from mock import patch, Mock

import toloka.client as toloka

from crowdom import pool as pool_params, control, worker
from crowdom.worker import human


@patch.object(pool_params, 'datetime', Mock(wraps=datetime))
def test_default_markup_pool_builder():
    pool_params.datetime.datetime.utcnow.return_value = datetime.datetime(2020, 11, 5)
    project_id = '0001'
    private_name = 'default markup config'
    public_description = 'dynamic pricing'
    reward_per_assignment = 0.03
    real_tasks_count = 10
    task_duration_hint = datetime.timedelta(seconds=12)
    assignment_duration = real_tasks_count * task_duration_hint
    task_duration_ratio_rand, task_duration_ratio_poor = 0.1, 0.3
    markup_config = pool_params.MarkupConfig(
        project_id=project_id,
        private_name=private_name,
        public_description=public_description,
        reward_per_assignment=reward_per_assignment,
        task_duration_hint=task_duration_hint,
        real_tasks_count=real_tasks_count,
        control_params=control.Control(
            rules=control.RuleBuilder()
            .add_static_reward(0.5)
            .add_speed_control(task_duration_ratio_rand, task_duration_ratio_poor)
            .build()
        ),
    )
    actual_pool = pool_params.create_pool_params(markup_config)
    expected_pool = toloka.Pool(
        project_id=project_id,
        private_name=private_name,
        public_description=public_description,
        may_contain_adult_content=True,
        will_expire=datetime.datetime(2020, 12, 5),
        reward_per_assignment=reward_per_assignment,
        assignment_max_duration_seconds=int(assignment_duration.total_seconds()) * 5,
        auto_accept_solutions=False,
        auto_accept_period_day=14,
        assignments_issuing_config=toloka.Pool.AssignmentsIssuingConfig(issue_task_suites_in_creation_order=False),
        priority=30,
        defaults=toloka.Pool.Defaults(default_overlap_for_new_tasks=1, default_overlap_for_new_task_suites=1),
    )

    expected_pool.set_mixer_config(real_tasks_count=real_tasks_count, golden_tasks_count=0, training_tasks_count=0)

    expected_pool.quality_control.add_action(
        collector=toloka.collectors.SkippedInRowAssignments(),
        conditions=[toloka.conditions.SkippedInRowCount >= 5],
        action=toloka.actions.RestrictionV2(
            private_comment='Skipped assignments',
            duration=8,
            duration_unit=toloka.user_restriction.DurationUnit.HOURS,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AssignmentSubmitTime(
            fast_submit_threshold_seconds=int(
                task_duration_hint.total_seconds() * task_duration_ratio_rand * markup_config.get_tasks_count()
            ),
            history_size=10,
        ),
        conditions=[
            toloka.conditions.TotalSubmittedCount >= 1,
            toloka.conditions.FastSubmittedCount >= 1,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Fast submits, <= 0.1',
            duration=1 * 60 * 24,  # 1 day
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AssignmentSubmitTime(
            fast_submit_threshold_seconds=int(
                task_duration_hint.total_seconds() * task_duration_ratio_poor * markup_config.get_tasks_count()
            ),
            history_size=10,
        ),
        conditions=[
            toloka.conditions.TotalSubmittedCount >= 1,
            toloka.conditions.FastSubmittedCount >= 1,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Fast submits, 0.1 < time <= 0.3',
            duration=8 * 60,  # 8 hours
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AnswerCount(),
        conditions=[
            toloka.conditions.AssignmentsAcceptedCount >= int(datetime.timedelta(hours=1) / assignment_duration)
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Completed many assignments, vacation',
            duration=5,
            duration_unit=toloka.user_restriction.DurationUnit.HOURS,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.set_speed_quality_balance(toloka.pool.speed_quality_balance_config.TopPercentageByQuality(percent=90))
    assert actual_pool == expected_pool


@patch.object(human, 'datetime', Mock(wraps=datetime))
@patch.object(pool_params, 'datetime', Mock(wraps=datetime))
def test_markup_pool_builder():
    human.datetime.datetime.today.return_value = datetime.datetime(2020, 11, 5)
    pool_params.datetime.datetime.utcnow.return_value = datetime.datetime(2020, 11, 5)
    project_id = '0002'
    private_name = 'custom markup config'
    reward_per_assignment = 0.10
    real_tasks_count = 6
    task_duration_hint = datetime.timedelta(seconds=25)
    assignment_duration = real_tasks_count * task_duration_hint
    auto_accept_period_day = 3
    task_duration_ratio_rand, task_duration_ratio_poor = 0.2, 0.5
    training_requirement = toloka.pool.QualityControl.TrainingRequirement(
        training_pool_id='training pool', training_passing_skill_value=70
    )
    priority = 50
    markup_config = pool_params.MarkupConfig(
        project_id='0002',
        private_name=private_name,
        reward_per_assignment=0.10,
        task_duration_hint=task_duration_hint,
        real_tasks_count=6,
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='RU', verified=True)},
                    age_range=(10, 30),
                )
            ],
            training_score=70,
        ),
        training_requirement=training_requirement,
        priority=priority,
        ttl_days=20,
        auto_accept_period_day=auto_accept_period_day,
        may_contain_adult_content=False,
        control_params=control.Control(
            rules=control.RuleBuilder()
            .add_static_reward(0.5)
            .add_speed_control(task_duration_ratio_rand, task_duration_ratio_poor)
            .build()
        ),
    )

    actual_pool = pool_params.create_pool_params(markup_config)

    expected_pool = toloka.Pool(
        project_id=project_id,
        private_name=private_name,
        may_contain_adult_content=False,
        will_expire=datetime.datetime(2020, 11, 25),
        reward_per_assignment=reward_per_assignment,
        assignment_max_duration_seconds=int(assignment_duration.total_seconds()) * 5,
        auto_accept_solutions=False,
        auto_accept_period_day=auto_accept_period_day,
        assignments_issuing_config=toloka.Pool.AssignmentsIssuingConfig(issue_task_suites_in_creation_order=False),
        priority=priority,
        defaults=toloka.Pool.Defaults(default_overlap_for_new_tasks=1, default_overlap_for_new_task_suites=1),
    )

    expected_pool.set_mixer_config(real_tasks_count=real_tasks_count, golden_tasks_count=0, training_tasks_count=0)

    expected_pool.set_filter(
        toloka.filter.Languages.in_('RU', verified=True)
        & (toloka.filter.DateOfBirth < int(datetime.datetime(2010, 11, 5).timestamp()))
        & (toloka.filter.DateOfBirth > int(datetime.datetime(1990, 11, 5).timestamp()))
    )

    expected_pool.set_training_requirement(training_requirement=training_requirement)

    expected_pool.quality_control.add_action(
        collector=toloka.collectors.SkippedInRowAssignments(),
        conditions=[toloka.conditions.SkippedInRowCount >= 5],
        action=toloka.actions.RestrictionV2(
            private_comment='Skipped assignments',
            duration=8,
            duration_unit=toloka.user_restriction.DurationUnit.HOURS,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AssignmentSubmitTime(
            fast_submit_threshold_seconds=int(
                task_duration_hint.total_seconds() * task_duration_ratio_rand * markup_config.get_tasks_count()
            ),
            history_size=10,
        ),
        conditions=[
            toloka.conditions.TotalSubmittedCount >= 1,
            toloka.conditions.FastSubmittedCount >= 1,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Fast submits, <= 0.2',
            duration=1 * 60 * 24,  # 1 day
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AssignmentSubmitTime(
            fast_submit_threshold_seconds=int(
                task_duration_hint.total_seconds() * task_duration_ratio_poor * markup_config.get_tasks_count()
            ),
            history_size=10,
        ),
        conditions=[
            toloka.conditions.TotalSubmittedCount >= 1,
            toloka.conditions.FastSubmittedCount >= 1,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Fast submits, 0.2 < time <= 0.5',
            duration=8 * 60,  # 8 hours
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AnswerCount(),
        conditions=[
            toloka.conditions.AssignmentsAcceptedCount >= int(datetime.timedelta(hours=1) / assignment_duration)
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Completed many assignments, vacation',
            duration=5,
            duration_unit=toloka.user_restriction.DurationUnit.HOURS,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.set_speed_quality_balance(toloka.pool.speed_quality_balance_config.TopPercentageByQuality(percent=90))
    assert actual_pool == expected_pool


@patch.object(human, 'datetime', Mock(wraps=datetime))
@patch.object(pool_params, 'datetime', Mock(wraps=datetime))
def test_check_pool_builder():
    human.datetime.datetime.today.return_value = datetime.datetime(2020, 11, 5)
    pool_params.datetime.datetime.utcnow.return_value = datetime.datetime(2020, 11, 5)
    project_id = '0003'
    private_name = 'custom check config'
    reward_per_assignment = 0.01
    real_tasks_count = 15
    task_duration_hint = datetime.timedelta(seconds=3)
    auto_accept_period_day = 2
    control_tasks_count = 4
    assignment_duration = (control_tasks_count + real_tasks_count) * task_duration_hint
    task_duration_ratio_rand, task_duration_ratio_poor = 0.3, 0.6
    training_requirement = toloka.pool.QualityControl.TrainingRequirement(
        training_pool_id='training pool - check', training_passing_skill_value=65
    )
    priority = 10
    overlap = 5
    check_config = pool_params.ClassificationConfig(
        project_id=project_id,
        private_name=private_name,
        reward_per_assignment=reward_per_assignment,
        task_duration_hint=task_duration_hint,
        real_tasks_count=real_tasks_count,
        worker_filter=worker.WorkerFilter(
            filters=[
                worker.WorkerFilter.Params(
                    langs={worker.LanguageRequirement(lang='EN'), worker.LanguageRequirement(lang='DE', verified=True)},
                    age_range=(None, 80),
                    regions={worker.RegionCodes.ITALY, worker.RegionCodes.NETHERLANDS},
                    client_types={toloka.filter.ClientType.ClientType.TOLOKA_APP},
                )
            ],
            training_score=65,
        ),
        training_requirement=training_requirement,
        priority=priority,
        ttl_days=10,
        auto_accept_period_day=auto_accept_period_day,
        may_contain_adult_content=True,
        control_tasks_count=control_tasks_count,
        overlap=overlap,
        control_params=control.Control(
            rules=control.RuleBuilder()
            .add_static_reward(0.5)
            .add_speed_control(task_duration_ratio_rand, task_duration_ratio_poor)
            .add_control_task_control(control_tasks_count, 2, 3)
            .build()
        ),
        work_duration_before_vacation=datetime.timedelta(hours=10),
    )

    actual_pool = pool_params.create_pool_params(check_config)

    expected_pool = toloka.Pool(
        project_id=project_id,
        private_name=private_name,
        may_contain_adult_content=True,
        will_expire=datetime.datetime(2020, 11, 15),
        reward_per_assignment=reward_per_assignment,
        assignment_max_duration_seconds=int(assignment_duration.total_seconds()) * 5,
        auto_accept_solutions=False,
        auto_accept_period_day=auto_accept_period_day,
        assignments_issuing_config=toloka.Pool.AssignmentsIssuingConfig(issue_task_suites_in_creation_order=False),
        priority=priority,
        defaults=toloka.Pool.Defaults(
            default_overlap_for_new_tasks=overlap, default_overlap_for_new_task_suites=overlap
        ),
    )

    expected_pool.set_mixer_config(
        real_tasks_count=real_tasks_count, golden_tasks_count=control_tasks_count, training_tasks_count=0
    )

    expected_pool.set_filter(
        toloka.filter.Languages.in_('DE', verified=True)
        & toloka.filter.Languages.in_('EN')
        & (toloka.filter.RegionByPhone.in_(118) | toloka.filter.RegionByPhone.in_(205))
        & (toloka.filter.DateOfBirth > int(datetime.datetime(1940, 11, 5).timestamp()))
        & (toloka.filter.ClientType == toloka.filter.ClientType.ClientType.TOLOKA_APP)
    )

    expected_pool.set_training_requirement(training_requirement=training_requirement)

    expected_pool.quality_control.add_action(
        collector=toloka.collectors.SkippedInRowAssignments(),
        conditions=[toloka.conditions.SkippedInRowCount >= 5],
        action=toloka.actions.RestrictionV2(
            private_comment='Skipped assignments',
            duration=8,
            duration_unit=toloka.user_restriction.DurationUnit.HOURS,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AssignmentSubmitTime(
            fast_submit_threshold_seconds=int(
                task_duration_hint.total_seconds() * task_duration_ratio_rand * check_config.get_tasks_count()
            ),
            history_size=10,
        ),
        conditions=[
            toloka.conditions.TotalSubmittedCount >= 1,
            toloka.conditions.FastSubmittedCount >= 1,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Fast submits, <= 0.3',
            duration=1 * 60 * 24,  # 1 day
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AssignmentSubmitTime(
            fast_submit_threshold_seconds=int(
                task_duration_hint.total_seconds() * task_duration_ratio_poor * check_config.get_tasks_count()
            ),
            history_size=10,
        ),
        conditions=[
            toloka.conditions.TotalSubmittedCount >= 1,
            toloka.conditions.FastSubmittedCount >= 1,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Fast submits, 0.3 < time <= 0.6',
            duration=8 * 60,  # 8 hours
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )

    expected_pool.quality_control.add_action(
        collector=toloka.collectors.GoldenSet(history_size=control_tasks_count),
        conditions=[
            toloka.conditions.TotalAnswersCount >= control_tasks_count,
            toloka.conditions.CorrectAnswersRate < 50.0,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Control tasks: [0, 2) done correctly',
            duration=8 * 60,
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.GoldenSet(history_size=control_tasks_count),
        conditions=[
            toloka.conditions.TotalAnswersCount >= control_tasks_count,
            toloka.conditions.CorrectAnswersRate >= 50.0,
            toloka.conditions.CorrectAnswersRate < 75.0,
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Control tasks: [2, 3) done correctly',
            duration=1 * 60,
            duration_unit=toloka.user_restriction.DurationUnit.MINUTES,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.quality_control.add_action(
        collector=toloka.collectors.AnswerCount(),
        conditions=[
            toloka.conditions.AssignmentsAcceptedCount >= int(datetime.timedelta(hours=10) / assignment_duration)
        ],
        action=toloka.actions.RestrictionV2(
            private_comment='Completed many assignments, vacation',
            duration=5,
            duration_unit=toloka.user_restriction.DurationUnit.HOURS,
            scope=toloka.UserRestriction.PROJECT,
        ),
    )
    expected_pool.set_speed_quality_balance(toloka.pool.speed_quality_balance_config.TopPercentageByQuality(percent=90))
    assert actual_pool == expected_pool


@patch.object(pool_params, 'datetime', Mock(wraps=datetime))
def test_expert_pool_builder():
    pool_params.datetime.datetime.today.return_value = datetime.datetime(2020, 11, 5)
    pool_params.datetime.datetime.utcnow.return_value = datetime.datetime(2020, 11, 5)
    project_id = '0004'
    private_name = 'custom expert config'
    public_description = 'test launch'
    reward_per_assignment = 0.01
    real_tasks_count = 15
    task_duration_hint = datetime.timedelta(seconds=10)
    assignment_duration = real_tasks_count * task_duration_hint
    priority = 10
    overlap = 1
    expert_config = pool_params.ExpertConfig(
        project_id=project_id,
        private_name=private_name,
        public_description=public_description,
        reward_per_assignment=reward_per_assignment,
        task_duration_hint=task_duration_hint,
        real_tasks_count=real_tasks_count,
        priority=priority,
        ttl_days=10,
        worker_filter=worker.ExpertFilter(
            skills=[toloka.Skill(id='experts'), toloka.Skill(id='experts-audio'), toloka.Skill(id='experts-image')]
        ),
    )

    actual_pool = pool_params.create_expert_pool_params(expert_config)

    expected_pool = toloka.Pool(
        project_id=project_id,
        private_name=private_name,
        public_description=public_description,
        may_contain_adult_content=True,
        will_expire=datetime.datetime(2020, 11, 15),
        reward_per_assignment=reward_per_assignment,
        assignment_max_duration_seconds=int(assignment_duration.total_seconds()) * 5,
        auto_accept_solutions=True,
        auto_accept_period_day=14,
        assignments_issuing_config=toloka.Pool.AssignmentsIssuingConfig(issue_task_suites_in_creation_order=False),
        priority=priority,
        defaults=toloka.Pool.Defaults(
            default_overlap_for_new_tasks=overlap, default_overlap_for_new_task_suites=overlap
        ),
    )

    expected_pool.set_mixer_config(real_tasks_count=real_tasks_count, golden_tasks_count=0, training_tasks_count=0)

    expected_pool.set_filter(
        (toloka.filter.Skill('experts') > 0)
        | (toloka.filter.Skill('experts-audio') > 0)
        | (toloka.filter.Skill('experts-image') > 0)
    )
    assert actual_pool == expected_pool
