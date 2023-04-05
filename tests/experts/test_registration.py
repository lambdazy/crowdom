import datetime
from mock import patch
from pytest import fixture
from typing import List, Optional

import toloka.client as toloka
import toloka.client.project.template_builder as tb

from crowdom import experts
from .. import lib


def test_generate_code():
    assert len(experts.generate_code()) == 10


def test_generate_codes():
    codes = experts.generate_codes(list('abcdef'))
    assert len(codes) == 6
    assert len(set(codes.values())) == 6


class TestGetSkillNames:
    def test_get_skill_names_id_lang(self):
        codes = experts.get_skill_names('dogs-and-cats', 'RU')
        assert set(codes) == {'expert', 'expert_RU', 'expert_dogs-and-cats', 'expert_dogs-and-cats_RU'}

    def test_get_skill_names_lang(self):
        codes = experts.get_skill_names(None, 'RU')
        assert set(codes) == {'expert', 'expert_RU'}

    def test_get_skill_names_id(self):
        codes = experts.get_skill_names('dogs-and-cats', None)
        assert set(codes) == {'expert', 'expert_dogs-and-cats'}

    def test_get_skill_names(self):
        codes = experts.get_skill_names(None, None)
        assert set(codes) == {'expert'}


class TolokaClientExpertsStub(lib.TolokaClientCallRecorderStub):
    def __init__(
        self, project_id: Optional[str] = None, pool_id: Optional[str] = None, skill_name: Optional[str] = None
    ):
        super(TolokaClientExpertsStub, self).__init__()
        if pool_id is not None:
            assert skill_name is not None
        self.project_id = project_id
        self.pool_id = pool_id
        self.skill = toloka.skill.Skill(id='fake', name=skill_name) if skill_name else None

    def get_projects(self, status: str):
        super(TolokaClientExpertsStub, self).get_projects(status)
        yield toloka.Project(id=self.project_id, private_comment=experts.PROJECT_PRIVATE_COMMENT)

    def get_requester(self):
        super(TolokaClientExpertsStub, self).get_requester()
        return toloka.requester.Requester(public_name={'EN': 'CROWDOM'})

    def create_project(self, project: toloka.Project):
        super(TolokaClientExpertsStub, self).create_project(project)
        assert self.project_id is None
        self.project_id = 'fake'
        project.id = self.project_id
        return project

    def get_skills(self, name: str):
        super(TolokaClientExpertsStub, self).get_skills(name)
        yield self.skill

    def create_skill(self, name: str, hidden: bool):
        super(TolokaClientExpertsStub, self).create_skill(name, hidden)
        assert self.skill is None
        self.skill = toloka.skill.Skill(id='fake', name=name)
        return self.skill

    def get_pools(self, project_id: str, status: str):
        super(TolokaClientExpertsStub, self).get_pools(project_id, status)
        assert self.project_id is not None
        assert project_id == self.project_id
        assert self.skill is not None
        if self.pool_id is not None:
            yield toloka.Pool(id=self.pool_id, private_comment=self.skill.name)

    def create_pool(self, pool: toloka.Pool):
        assert self.pool_id is None
        self.pool_id = 'fake'
        pool.id = self.pool_id
        super(TolokaClientExpertsStub, self).create_pool(pool)
        return pool

    def create_task(self, task: toloka.Task):
        super(TolokaClientExpertsStub, self).create_task(task)
        assert self.pool_id is not None
        assert task.pool_id == self.pool_id

    def open_pool(self, pool_id: str):
        assert self.pool_id is not None
        assert pool_id == self.pool_id
        super(TolokaClientExpertsStub, self).open_pool(pool_id)


class TolokaClientApproveStub(lib.TolokaClientCallRecorderStub):
    def __init__(self, assignments: List[toloka.Assignment]):
        super(TolokaClientApproveStub, self).__init__()
        self.assignments = assignments

    def get_assignments(self, pool_id: str, status: List[toloka.Assignment.Status]):
        super(TolokaClientApproveStub, self).get_assignments(pool_id, status)
        yield from self.assignments


@fixture
def expected_pool() -> toloka.Pool:
    pool = toloka.Pool(
        project_id='fake',
        id='fake',
        private_name='Pool for expert promotion',
        may_contain_adult_content=False,
        reward_per_assignment=0.0,
        assignment_max_duration_seconds=120,
        will_expire=datetime.datetime(2021, 11, 5),
        public_description=experts.EXPERT_SKILL,
        private_comment=experts.EXPERT_SKILL,
        auto_accept_solutions=False,
    )
    pool.set_defaults(default_overlap_for_new_task_suites=1)
    pool.set_mixer_config(golden_tasks_count=1)
    pool.set_filter(
        toloka.filter.FilterAnd(
            and_=[
                toloka.filter.Skill(key='fake') == None,  # noqa
                toloka.filter.DateOfBirth < int(datetime.datetime(year=1405, month=5, day=16).timestamp()),
                toloka.filter.DateOfBirth > int(datetime.datetime(year=1405, month=5, day=12).timestamp()),
            ]
        )
    )
    pool.quality_control.add_action(
        collector=toloka.collectors.AnswerCount(),
        conditions=[toloka.conditions.AssignmentsAcceptedCount > 0],
        action=toloka.actions.SetSkill(skill_id='fake', skill_value=1),
    )
    return pool


@patch('crowdom.experts.registration.datetime', wraps=datetime)
def test_create_pool_with_pool_and_project_and_skill_creation(mock_datetime, expected_pool: toloka.Pool):
    now = datetime.datetime(2020, 11, 5)
    mock_datetime.datetime.utcnow.return_value = now
    stub_client = TolokaClientExpertsStub()
    pool = experts.create_registration_pool(stub_client)  # noqa
    assert pool == expected_pool
    assert stub_client.calls == [
        ('get_projects', ('ACTIVE',)),
        ('get_requester', ()),
        (
            'create_project',
            (
                toloka.Project(
                    public_name='Welcome to CROWDOM!',
                    public_description='Welcome! You will need to enter a code',
                    task_spec=toloka.project.task_spec.TaskSpec(
                        input_spec={'unused': toloka.project.field_spec.StringSpec(required=False, hidden=True)},
                        output_spec={
                            'code': toloka.project.field_spec.StringSpec(
                                required=True, hidden=False, min_length=10, max_length=10
                            )
                        },
                        view_spec=toloka.project.TemplateBuilderViewSpec(
                            view=tb.ListViewV1(
                                items=[
                                    tb.TextViewV1(content='Enter code:'),
                                    tb.TextFieldV1(
                                        data=tb.OutputData(path='code'),
                                        validation=tb.SchemaConditionV1(
                                            schema={
                                                'type': 'string',
                                                'pattern': '[a-zA-Z0-9]{10}',
                                                'minLength': 10,
                                                'maxLength': 10,
                                            },
                                            hint='Code length should be 10, you can use only latin alphabet and digits',
                                        ),
                                    ),
                                ]
                            )
                        ),
                    ),
                    id='fake',
                    public_instructions='Enter supplied code',
                    private_comment='expert-registration',
                ),
            ),
        ),
        ('get_skills', ('expert',)),
        ('create_skill', ('expert', True)),
        ('get_pools', ('fake', 'OPEN')),
        ('create_pool', (expected_pool,)),
        (
            'create_task',
            (
                toloka.Task(
                    input_values={'unused': ''},
                    known_solutions=[toloka.task.BaseTask.KnownSolution(output_values={'code': 'AAAAAAAAAA'})],
                    infinite_overlap=True,
                    pool_id='fake',
                ),
            ),
        ),
        ('open_pool', ('fake',)),
    ]


@patch('crowdom.experts.registration.datetime', wraps=datetime)
def test_create_pool_with_pool_and_skill_creation(mock_datetime, expected_pool: toloka.Pool):
    now = datetime.datetime(2020, 11, 5)
    mock_datetime.datetime.utcnow.return_value = now
    stub_client = TolokaClientExpertsStub(project_id='fake')
    pool = experts.create_registration_pool(stub_client)  # noqa
    assert pool == expected_pool
    assert stub_client.calls == [
        ('get_projects', ('ACTIVE',)),
        ('get_skills', ('expert',)),
        ('create_skill', ('expert', True)),
        ('get_pools', ('fake', 'OPEN')),
        ('create_pool', (expected_pool,)),
        (
            'create_task',
            (
                toloka.Task(
                    input_values={'unused': ''},
                    known_solutions=[toloka.task.BaseTask.KnownSolution(output_values={'code': 'AAAAAAAAAA'})],
                    infinite_overlap=True,
                    pool_id='fake',
                ),
            ),
        ),
        ('open_pool', ('fake',)),
    ]


def test_create_pool():
    stub_client = TolokaClientExpertsStub(project_id='fake', pool_id='fake', skill_name='expert')
    pool = experts.create_registration_pool(stub_client)  # noqa
    assert pool.private_comment == experts.EXPERT_SKILL
    assert stub_client.calls == [
        ('get_projects', ('ACTIVE',)),
        ('get_skills', ('expert',)),
        ('get_pools', ('fake', 'OPEN')),
    ]


def test_approve_experts(capsys):
    assignments = [
        toloka.Assignment(
            id=f'worker_{i}',
            user_id=f'worker_{i}',
            solutions=[toloka.solution.Solution(output_values={'code': symbol * 10})],
        )
        for i, symbol in enumerate('abccz')
    ]
    stub_client = TolokaClientApproveStub(assignments)
    results = experts.approve_expected_codes(
        stub_client, 'fake', {'@alice': 'a' * 10, '@bob': 'b' * 10, '@cara': 'c' * 10, 'dylan': 'd' * 10}  # noqa
    )
    assert results == {'@alice': 'worker_0', '@bob': 'worker_1'}
    assert stub_client.calls == [
        ('get_assignments', ('fake', [toloka.Assignment.SUBMITTED])),
        ('accept_assignment', ('worker_0', '')),
        ('accept_assignment', ('worker_1', '')),
        ('reject_assignment', ('worker_2', 'Duplicated code')),
        ('reject_assignment', ('worker_3', 'Duplicated code')),
        ('reject_assignment', ('worker_4', 'Unexpected code')),
    ]

    captured = capsys.readouterr()
    assert (
        captured.out == f"More than one answer for code {'c' * 10}, this one from worker_2\n"
        f"More than one answer for code {'c' * 10}, this one from worker_3\n"
        f"Unexpected code {'z' * 10} from worker worker_4\n"
    )
