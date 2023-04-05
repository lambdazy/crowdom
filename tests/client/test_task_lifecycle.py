import datetime
import mock
import pytest
from typing import List, Optional

import toloka.client as toloka

from crowdom import base, client, objects, project, task_spec as spec
from .. import lib


@pytest.fixture
def lang() -> str:
    return 'RU'


@pytest.fixture
def instruction_current() -> str:
    return """
<p>Выберите из двух предложенных аудиозаписей лучшую по следующим критериям:<p>
<ul>
<li>Благозвучность</li><li>Отсутствие помех</li><li>Отсутствие нецензурной лексики</li>
</ul>"""


@pytest.fixture
def instruction_existing() -> str:
    return """
<p>Выберите из аудиозаписей лучшую по следующим критериям:<p><ul><li>Благозвучность</li>
<li>Отсутствие нецензурной лексики</li><li>Общее восприятие</li></ul>"""


@pytest.fixture
def instruction_annotation() -> str:
    return '<p>Transcribe given audio, not punctuation marks needed<p>'


@pytest.fixture
def task_spec_current(lang: str, instruction_current: str) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(
        task_spec=base.TaskSpec(
            function=base.SbSFunction(inputs=(objects.Audio,), hints=(objects.Text,)),
            id='my-sbs-task',
            name=base.LocalizedString({lang: 'Сравнение аудио', base.DEFAULT_LANG: 'Audio comparison'}),
            description=base.LocalizedString({lang: 'Выберите более благозвучную из двух аудиозаписей'}),
            instruction=base.LocalizedString({lang: instruction_current}),
        ),
        lang=lang,
    )


@pytest.fixture
def task_spec_compatible(lang: str, instruction_existing: str) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(
        task_spec=base.TaskSpec(
            function=base.SbSFunction(inputs=(objects.Audio,), hints=(objects.Text,)),
            id='my-sbs-task',
            name=base.LocalizedString({lang: 'Сравнение аудиодорожки', base.DEFAULT_LANG: 'Audio records comparison'}),
            description=base.LocalizedString({lang: 'Выберите наиболее благозвучную из аудиозаписей'}),
            instruction=base.LocalizedString({lang: instruction_existing}),
        ),
        lang=lang,
    )


@pytest.fixture
def task_spec_incompatible(lang: str, instruction_existing: str) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(
        task_spec=base.TaskSpec(
            function=base.SbSFunction(inputs=(objects.Audio,)),
            id='my-sbs-task',
            name=base.LocalizedString({lang: 'Сравнение аудиодорожки', base.DEFAULT_LANG: 'Audio records comparison'}),
            description=base.LocalizedString({lang: 'Выберите наиболее благозвучную из аудиозаписей'}),
            instruction=base.LocalizedString({lang: instruction_existing}),
        ),
        lang=lang,
    )


@pytest.fixture
def task_spec_annotation(instruction_annotation: str) -> spec.AnnotationTaskSpec:
    return spec.AnnotationTaskSpec(
        task_spec=base.TaskSpec(
            function=base.AnnotationFunction(inputs=(objects.Audio,), outputs=(objects.Text,)),
            id='transcript',
            name=base.LocalizedString({base.DEFAULT_LANG: 'Audio transcript'}),
            description=base.LocalizedString({base.DEFAULT_LANG: 'Transcribe audio'}),
            instruction=base.LocalizedString({base.DEFAULT_LANG: instruction_annotation}),
        ),
        lang=base.DEFAULT_LANG,
    )


def generate_project(
    task_spec: spec.PreparedTaskSpec,
    project_id: Optional[str],
) -> toloka.Project:
    return toloka.Project(
        id=project_id,
        private_comment=f'{task_spec.id}_{task_spec.lang}',
        public_name=task_spec.name[task_spec.lang],
        public_description=task_spec.description[task_spec.lang],
        public_instructions=client.get_instruction(task_spec),
        task_spec=toloka.project.task_spec.TaskSpec(
            input_spec=task_spec.task_mapping.to_toloka_input_spec(),
            output_spec=task_spec.task_mapping.to_toloka_output_spec(),
            view_spec=task_spec.view,
        ),
    )


@pytest.fixture
def project_created(task_spec_current: spec.PreparedTaskSpec) -> toloka.Project:
    return generate_project(task_spec_current, None)


@pytest.fixture
def project_updated(task_spec_current: spec.PreparedTaskSpec) -> toloka.Project:
    return generate_project(task_spec_current, 'prj-id-compatible')


@pytest.fixture
def project_compatible(task_spec_compatible: spec.PreparedTaskSpec) -> toloka.Project:
    return generate_project(task_spec_compatible, 'prj-id-compatible')


@pytest.fixture
def project_incompatible(task_spec_incompatible: spec.PreparedTaskSpec) -> toloka.Project:
    return generate_project(task_spec_incompatible, 'prj-id-incompatible')


@pytest.fixture
def project_annotation(task_spec_annotation: spec.AnnotationTaskSpec) -> toloka.Project:
    return generate_project(task_spec_annotation, None)


@pytest.fixture
def project_check(task_spec_annotation: spec.AnnotationTaskSpec) -> toloka.Project:
    return generate_project(task_spec_annotation.check, None)


@pytest.fixture
def expected_diff_compatible() -> str:
    return """name changed:

---
+++
@@ -1 +1 @@
-Сравнение аудиодорожки
+Сравнение аудио


description changed:

---
+++
@@ -1 +1 @@
-Выберите наиболее благозвучную из аудиозаписей
+Выберите более благозвучную из двух аудиозаписей


instruction changed:

---
+++
@@ -81,17 +81,17 @@
 </style>
 <div>
  <p>
-  Выберите из аудиозаписей лучшую по следующим критериям:
+  Выберите из двух предложенных аудиозаписей лучшую по следующим критериям:
   <p>
    <ul>
     <li>
      Благозвучность
     </li>
     <li>
-     Отсутствие нецензурной лексики
+     Отсутствие помех
     </li>
     <li>
-     Общее восприятие
+     Отсутствие нецензурной лексики
     </li>
    </ul>
   </p>

"""


@pytest.fixture
def expected_diff_incompatible() -> str:
    return """name changed:

---
+++
@@ -1 +1 @@
-Сравнение аудиодорожки
+Сравнение аудио


description changed:

---
+++
@@ -1 +1 @@
-Выберите наиболее благозвучную из аудиозаписей
+Выберите более благозвучную из двух аудиозаписей


instruction changed:

---
+++
@@ -81,17 +81,17 @@
 </style>
 <div>
  <p>
-  Выберите из аудиозаписей лучшую по следующим критериям:
+  Выберите из двух предложенных аудиозаписей лучшую по следующим критериям:
   <p>
    <ul>
     <li>
      Благозвучность
     </li>
     <li>
-     Отсутствие нецензурной лексики
+     Отсутствие помех
     </li>
     <li>
-     Общее восприятие
+     Отсутствие нецензурной лексики
     </li>
    </ul>
   </p>


view changed:

---
+++
@@ -49,6 +49,14 @@
     ],
     "view": {
         "items": [
+            {
+                "content": {
+                    "path": "text_hint",
+                    "type": "data.input"
+                },
+                "type": "view.text",
+                "version": "1.0.0"
+            },
             {
                 "commonControls": {
                     "items": [

"""


class TolokaClientStub(lib.TolokaClientCallRecorderStub):
    prj: Optional[toloka.Project]
    training_skill_id: Optional[str]  # indicates the presence of training and the ID of the corresponding skill
    has_registered_experts: bool

    def __init__(
        self,
        prj: Optional[toloka.Project] = None,
        training_skill_id: str = None,
        has_registered_experts: bool = False,
    ):
        self.prj = prj
        self.training_skill_id = training_skill_id
        self.has_registered_experts = has_registered_experts
        super(TolokaClientStub, self).__init__()

    def get_projects(self, status: str) -> List[toloka.Project]:
        result = [toloka.Project(private_comment='fake')]  # to check filter
        if self.prj:
            result.append(self.prj)
        super(TolokaClientStub, self).get_projects(status)
        return result

    def find_trainings(
        self,
        project_id: str,
        status: toloka.Training.Status,
        sort: toloka.search_requests.TrainingSortItems,
        limit: Optional[int],
    ) -> toloka.search_results.TrainingSearchResult:
        items = []
        if self.training_skill_id is not None:
            items.append(
                toloka.Training(
                    id='training-id',
                    created=datetime.datetime(year=1999, month=12, day=31),
                    retry_training_after_days=30,
                )
            )

        super(TolokaClientStub, self).find_trainings(project_id, status, sort, limit)
        return toloka.search_results.TrainingSearchResult(items=items, has_more=False)

    def get_pool(self, pool_id: str) -> toloka.Pool:
        super(TolokaClientStub, self).get_pool(pool_id)
        assert self.training_skill_id is not None
        return toloka.Pool(
            quality_control=toloka.Pool.QualityControl(
                configs=[
                    toloka.Pool.QualityControl.QualityControlConfig(
                        rules=[
                            toloka.Pool.QualityControl.QualityControlConfig.RuleConfig(
                                action=toloka.actions.SetSkillFromOutputField(skill_id=self.training_skill_id)
                            )
                        ]
                    )
                ]
            )
        )

    def get_skills(self, name: str):
        super(TolokaClientStub, self).get_skills(name)
        if self.has_registered_experts:
            yield toloka.Skill(id='skill-id')
        else:
            yield


def test_diff(
    task_spec_current: spec.PreparedTaskSpec,
    project_incompatible: toloka.Project,
    expected_diff_incompatible: str,
):
    # in real situation we can't reach diff calculation because project is incompatible, but we do so to test
    # some changes in view
    assert client.get_project_diff(project_incompatible, task_spec_current) == expected_diff_incompatible


def test_creating(task_spec_current: spec.PreparedTaskSpec, project_created: toloka.Project):
    stub = TolokaClientStub()

    client.define_task(task_spec_current, stub)

    assert stub.calls == [('get_projects', ('ACTIVE',)), ('create_project', (project_created,))]


def test_annotation_creating(
    task_spec_annotation: spec.AnnotationTaskSpec,
    project_check: toloka.Project,
    project_annotation: toloka.Project,
):
    stub = TolokaClientStub(None)

    client.define_task(task_spec_annotation, stub)

    assert stub.calls == [
        ('get_projects', ('ACTIVE',)),
        ('create_project', (project_check,)),
        ('get_projects', ('ACTIVE',)),
        ('create_project', (project_annotation,)),
    ]


@mock.patch('crowdom.client.task.ask')
@mock.patch('crowdom.client.task.input')
def test_updating(
    input,
    ask,
    task_spec_current: spec.PreparedTaskSpec,
    project_compatible: toloka.Project,
    expected_diff_compatible: str,
    project_updated: toloka.Project,
):
    ask.return_value = True
    input.return_value = 'Инструкция обновлена'
    stub = TolokaClientStub(project_compatible)

    client.define_task(task_spec_current, stub)

    assert ask.mock_calls == [
        mock.call(
            'Toloka project is exists for task "my-sbs-task" in RU and differs from current task spec:\n\n'
            f'{expected_diff_compatible}update Toloka project prj-id-compatible according to the changes shown above?'
        ),
        mock.call(
            'notify workers of changes in the task? (all RU workers who have ever performed tasks associated with '
            'your Toloka account will receive a notification)'
        ),
    ]

    input.assert_called_with('specify message for workers (in RU or EN): ')

    assert stub.calls == [
        ('get_projects', ('ACTIVE',)),
        ('update_project', ('prj-id-compatible', project_updated)),
        (
            'find_trainings',
            (
                'prj-id-compatible',
                toloka.Training.Status.OPEN,
                toloka.search_requests.TrainingSortItems(['-created']),
                1,
            ),
        ),
        (
            'find_trainings',
            (
                'prj-id-compatible',
                toloka.Training.Status.CLOSED,
                toloka.search_requests.TrainingSortItems(['-created']),
                1,
            ),
        ),
        (
            'compose_message_thread',
            (
                {'RU': 'Изменения в задании "Сравнение аудио"'},
                {'RU': 'Инструкция обновлена'},
                toloka.message_thread.RecipientsSelectType.FILTER,
                toloka.filter.FilterAnd([toloka.filter.Languages.in_('RU')]),
                False,
            ),
        ),
    ]


def test_incompatible(task_spec_current: spec.PreparedTaskSpec, project_incompatible: toloka.Project):
    stub = TolokaClientStub(project_incompatible)

    with pytest.raises(ValueError) as e:
        client.define_task(task_spec_current, stub)
    assert (
        str(e.value) == 'Toloka project is exists for task "my-sbs-task" in RU, '
        'but function of task is changed in incompatible way. Use different task ID'
    )


class TestWorkersNotification:
    def test_recipients_experts(
        self,
        task_spec_current: spec.PreparedTaskSpec,
        project_compatible: toloka.Project,
    ):
        task_spec_current.scenario = project.Scenario.EXPERT_LABELING_OF_TASKS
        stub = TolokaClientStub(has_registered_experts=True)
        assert client.define_notification_recipients(task_spec_current, project_compatible, stub) == (
            toloka.filter.FilterAnd(
                [
                    # in stub, we have no logic which filter skill by name, so it's just same skill repeated 4 times
                    toloka.filter.Skill(
                        key='skill-id',
                        operator=toloka.primitives.operators.CompareOperator.GTE,
                        value=0.0,
                    )
                ]
                * 4,
            ),
            'all experts who registered for task "my-sbs-task" in RU language will receive a notification',
        )
        assert stub.calls == [
            ('get_skills', ('expert',)),
            ('get_skills', ('expert_RU',)),
            ('get_skills', ('expert_my-sbs-task',)),
            ('get_skills', ('expert_my-sbs-task_RU',)),
        ]

    def test_recipients_workers_all(
        self,
        task_spec_current: spec.PreparedTaskSpec,
        project_compatible: toloka.Project,
    ):
        stub = TolokaClientStub()
        assert client.define_notification_recipients(task_spec_current, project_compatible, stub) == (
            toloka.filter.FilterAnd([toloka.filter.Languages.in_(task_spec_current.lang)]),
            (
                'all RU workers who have ever performed tasks associated with your Toloka account '
                'will receive a notification'
            ),
        )
        assert stub.calls == [
            (
                'find_trainings',
                (
                    'prj-id-compatible',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(['-created']),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'prj-id-compatible',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(['-created']),
                    1,
                ),
            ),
        ]

    def test_recipients_workers_performed_task(
        self,
        task_spec_current: spec.PreparedTaskSpec,
        project_compatible: toloka.Project,
    ):
        stub = TolokaClientStub(training_skill_id='skill-id')
        assert client.define_notification_recipients(task_spec_current, project_compatible, stub) == (
            toloka.filter.FilterAnd(
                [
                    toloka.filter.Languages.in_(task_spec_current.lang),
                    toloka.filter.Skill(
                        key='skill-id', operator=toloka.primitives.operators.CompareOperator.GTE, value=0.0
                    ),
                ]
            ),
            (
                'all workers who have performed the task "my-sbs-task" in RU language within the last 30 days '
                'will receive a notification'
            ),
        )
        assert stub.calls == [
            (
                'find_trainings',
                (
                    'prj-id-compatible',
                    toloka.Training.Status.OPEN,
                    toloka.search_requests.TrainingSortItems(['-created']),
                    1,
                ),
            ),
            (
                'find_trainings',
                (
                    'prj-id-compatible',
                    toloka.Training.Status.CLOSED,
                    toloka.search_requests.TrainingSortItems(['-created']),
                    1,
                ),
            ),
            ('get_pool', ('training-id',)),
        ]

    @mock.patch('crowdom.client.task.ask')
    @mock.patch('crowdom.client.task.input')
    @mock.patch('crowdom.client.task.send_message_to_workers')
    def test_default_lang(
        self,
        send_message_to_workers,
        input,
        ask,
        task_spec_annotation: spec.PreparedTaskSpec,
        project_annotation: toloka.Project,
    ):
        stub = TolokaClientStub()

        ask.return_value = True
        input.return_value = 'Instructions changed'

        client.notify_workers_about_task_change(task_spec_annotation, project_annotation, stub)

        input.assert_called_with('specify message for workers (in EN): ')
        send_message_to_workers.assert_called_with(
            'Changes in task "Audio transcript"',
            'Instructions changed',
            'EN',
            toloka.filter.FilterAnd([toloka.filter.Languages.in_(task_spec_annotation.lang)]),
            stub,
        )
