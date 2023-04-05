from typing import Dict

import toloka.client.project.template_builder as tb
import toloka.client as toloka

from crowdom import base, project as project_params, objects, task_spec as spec
from crowdom.mapping import TaskMapping, ObjectMapping

from . import lib


class Animal(base.Class):
    DOG = 'dog'
    CAT = 'cat'

    @classmethod
    def labels(cls) -> Dict[base.Class, Dict[str, str]]:
        return {value: {'EN': str(value.name)} for value in cls.possible_instances()}


class ManyOptions(base.Class):
    O1 = '1'
    O2 = '2'
    O3 = '3'
    O4 = '4'
    O5 = '5'
    O6 = '6'

    @classmethod
    def labels(cls) -> Dict[base.Class, Dict[str, str]]:
        return {value: {'EN': f'option {value.value}'} for value in cls.possible_instances()}


def test_label_view():
    for obj_meta, is_output, expected_view in [
        (
            base.ClassMeta(name='cls', type=Animal),
            True,
            tb.RadioGroupFieldV1(
                data=tb.OutputData(path='cls'),
                options=[
                    tb.GroupFieldOption(value='dog', label='DOG'),
                    tb.GroupFieldOption(value='cat', label='CAT'),
                ],
                disabled=False,
            ),
        ),
        (
            base.ClassMeta(name='cls', type=Animal),
            False,
            tb.RadioGroupFieldV1(
                data=tb.OutputData(path='cls'),
                options=[
                    tb.GroupFieldOption(value='dog', label='DOG'),
                    tb.GroupFieldOption(value='cat', label='CAT'),
                ],
                disabled=True,
            ),
        ),
        (
            base.ClassMeta(name='cls', type=ManyOptions),
            True,
            tb.SelectFieldV1(
                data=tb.OutputData(path='cls'),
                options=[
                    tb.SelectFieldV1.Option(label='option 1', value='1'),
                    tb.SelectFieldV1.Option(label='option 2', value='2'),
                    tb.SelectFieldV1.Option(label='option 3', value='3'),
                    tb.SelectFieldV1.Option(label='option 4', value='4'),
                    tb.SelectFieldV1.Option(label='option 5', value='5'),
                    tb.SelectFieldV1.Option(label='option 6', value='6'),
                ],
            ),
        ),
        (
            base.ClassMeta(name='cls', type=ManyOptions),
            False,
            tb.IfHelperV1(
                condition=tb.EqualsConditionV1(
                    data=tb.InputData(path='cls'),
                    to='1',
                ),
                then=tb.TextViewV1(content='option 1'),
                else_=tb.IfHelperV1(
                    condition=tb.EqualsConditionV1(
                        data=tb.InputData(path='cls'),
                        to='2',
                    ),
                    then=tb.TextViewV1(content='option 2'),
                    else_=tb.IfHelperV1(
                        condition=tb.EqualsConditionV1(
                            data=tb.InputData(path='cls'),
                            to='3',
                        ),
                        then=tb.TextViewV1(content='option 3'),
                        else_=tb.IfHelperV1(
                            condition=tb.EqualsConditionV1(
                                data=tb.InputData(path='cls'),
                                to='4',
                            ),
                            then=tb.TextViewV1(content='option 4'),
                            else_=tb.IfHelperV1(
                                condition=tb.EqualsConditionV1(
                                    data=tb.InputData(path='cls'),
                                    to='5',
                                ),
                                then=tb.TextViewV1(content='option 5'),
                                else_=tb.IfHelperV1(
                                    condition=tb.EqualsConditionV1(
                                        data=tb.InputData(path='cls'),
                                        to='6',
                                    ),
                                    then=tb.TextViewV1(content='option 6'),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        (
            base.ClassMeta(
                name='cls',
                type=Animal,
                input_display_type=base.LabelsDisplayType.MONO,
                text_format=base.TextFormat.MARKDOWN,
            ),
            False,
            tb.IfHelperV1(
                condition=tb.EqualsConditionV1(
                    data=tb.InputData(path='cls'),
                    to='dog',
                ),
                then=tb.MarkdownViewV1(content='DOG'),
                else_=tb.IfHelperV1(
                    condition=tb.EqualsConditionV1(
                        data=tb.InputData(path='cls'),
                        to='cat',
                    ),
                    then=tb.MarkdownViewV1(content='CAT'),
                ),
            ),
        ),
        (
            base.ClassMeta(
                name='cls', type=Animal, title=base.Title(text=base.LocalizedString({'EN': 'choose animal'}))
            ),
            True,
            tb.GroupViewV1(
                content=tb.ListViewV1(
                    items=[
                        tb.TextViewV1(content='choose animal'),
                        tb.RadioGroupFieldV1(
                            data=tb.OutputData(path='cls'),
                            options=[
                                tb.GroupFieldOption(value='dog', label='DOG'),
                                tb.GroupFieldOption(value='cat', label='CAT'),
                            ],
                            disabled=False,
                        ),
                    ],
                ),
            ),
        ),
        (
            base.ClassMeta(
                type=ManyOptions,
                name='cls',
                available_labels=base.create_available_labels_if(
                    name='question',
                    value_labels=[
                        ('q1', [ManyOptions.O6]),
                        ('q2', [ManyOptions.O1, ManyOptions.O5]),
                        ('q3', [ManyOptions.O2, ManyOptions.O3]),
                    ],
                ),
            ),
            True,
            tb.IfHelperV1(
                condition=tb.EqualsConditionV1(
                    data=tb.InputData(path='question_f'),
                    to='q1',
                ),
                then=tb.RadioGroupFieldV1(
                    data=tb.OutputData(path='cls'),
                    options=[
                        tb.GroupFieldOption(value='6', label='option 6'),
                    ],
                    disabled=False,
                ),
                else_=tb.IfHelperV1(
                    condition=tb.EqualsConditionV1(
                        data=tb.InputData(path='question_f'),
                        to='q2',
                    ),
                    then=tb.RadioGroupFieldV1(
                        data=tb.OutputData(path='cls'),
                        options=[
                            tb.GroupFieldOption(value='1', label='option 1'),
                            tb.GroupFieldOption(value='5', label='option 5'),
                        ],
                        disabled=False,
                    ),
                    else_=tb.IfHelperV1(
                        condition=tb.EqualsConditionV1(
                            data=tb.InputData(path='question_f'),
                            to='q3',
                        ),
                        then=tb.RadioGroupFieldV1(
                            data=tb.OutputData(path='cls'),
                            options=[
                                tb.GroupFieldOption(value='2', label='option 2'),
                                tb.GroupFieldOption(value='3', label='option 3'),
                            ],
                            disabled=False,
                        ),
                    ),
                ),
            ),
        ),
        (
            base.ClassMeta(
                type=Animal,
                name='cls',
                available_labels=base.create_available_labels_if(
                    name='question',
                    value_labels=[
                        ('q1', [Animal.CAT]),
                        ('q2', [Animal.CAT, Animal.DOG]),
                    ],
                ),
                input_display_type=base.LabelsDisplayType.MONO,
                title=base.Title(text=base.LocalizedString({'EN': 'answer question'})),
            ),
            False,
            tb.IfHelperV1(
                condition=tb.EqualsConditionV1(
                    to='q1',
                    data=tb.InputData(path='question_f'),
                ),
                then=tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='answer question'),
                            tb.IfHelperV1(
                                condition=tb.EqualsConditionV1(
                                    to='dog',
                                    data=tb.InputData(path='cls'),
                                ),
                                then=tb.TextViewV1(content='DOG'),
                                else_=tb.IfHelperV1(
                                    condition=tb.EqualsConditionV1(
                                        to='cat',
                                        data=tb.InputData(path='cls'),
                                    ),
                                    then=tb.TextViewV1(content='CAT'),
                                ),
                            ),
                        ],
                    ),
                ),
                else_=tb.IfHelperV1(
                    condition=tb.EqualsConditionV1(
                        to='q2',
                        data=tb.InputData(path='question_f'),
                    ),
                    then=tb.GroupViewV1(
                        content=tb.ListViewV1(
                            items=[
                                tb.TextViewV1(content='answer question'),
                                tb.IfHelperV1(
                                    condition=tb.EqualsConditionV1(
                                        to='dog',
                                        data=tb.InputData(path='cls'),
                                    ),
                                    then=tb.TextViewV1(content='DOG'),
                                    else_=tb.IfHelperV1(
                                        condition=tb.EqualsConditionV1(
                                            to='cat',
                                            data=tb.InputData(path='cls'),
                                        ),
                                        then=tb.TextViewV1(content='CAT'),
                                    ),
                                ),
                            ],
                        ),
                    ),
                ),
            ),
        ),
    ]:
        actual_view = project_params.gen_label_view(
            data=tb.OutputData(path='cls'),
            is_output=is_output,
            obj_meta=obj_meta,
            condition_context=base.ConditionContext(
                name_to_arg_data={
                    'cls': base.ConditionContext.ArgData(final_name='cls', is_output=is_output),
                    'question': base.ConditionContext.ArgData(final_name='question_f', is_output=False),
                }
            ),
            lang='EN',
        )
        assert actual_view == expected_view


def test_validation_view():
    for validation, placeholder, expected_view in [
        (
            None,
            None,
            tb.TextareaFieldV1(
                data=tb.OutputData(path='text'),
            ),
        ),
        (
            objects.TextValidation(regex={'EN': '^[a-z]+$'}, hint={'EN': 'One lowercase word only'}),
            base.LocalizedString({'EN': 'Placeholder text'}),
            tb.TextareaFieldV1(
                data=tb.OutputData(path='text'),
                placeholder='Placeholder text',
                validation=tb.SchemaConditionV1(
                    schema={'type': 'string', 'pattern': '^[a-z]+$'},
                    hint='One lowercase word only',
                ),
            ),
        ),
    ]:
        actual_view = project_params.gen_text_output_view(
            data=tb.OutputData(path='text'),
            validation=validation,
            placeholder=placeholder,
            lang='EN',
        )
        assert actual_view == expected_view


def test_obj_type_indexes():
    types = (objects.Text, objects.Audio, objects.Image, objects.Text, objects.Image, objects.Text)
    expected_indexes = ['_1', '', '_1', '_2', '_2', '_3']
    assert project_params.get_obj_type_indexes(types) == expected_indexes


# Common cases we need to cover
# [x] Multiple input/output objects
# [x] Localization fallback to EN
# [x] Label as input
# [x] Multiple objects of same type in input/output
# [x] Expert annotation of task
# [x] Expert annotation of solution
# [x] Overlapping types in input and output
# [x] Definition through ObjectMeta
# [x] Titles for Label types
# [ ] Titles for Text type
# [x] Custom Text format
# [x] Text regex validation
# [ ] Display input Class as text
# [x] Conditional options for Class
# [ ] Title along with conditional options
# [x] Condition on input argument
# [ ] Condition on output argument
# [x] Condition on argument moved from output to input
# [x] Conditions transform for SbS function
# [ ] Annotation function expert labeling types
# [ ] Cover all objects types as input and output


def test_sbs_project_compare_layout_multiple_objects():
    # [x] Multiple input/output objects
    # [x] Multiple objects of same type in input/output

    builder = project_params.SbSBuilder(base.SbSFunction(inputs=(objects.Audio, objects.Text, objects.Text)), lang='EN')
    sbs_view, sbs_mapping = builder.get_default_scenario()
    assert sbs_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Audio, name='audio'), (('url', 'audio_a'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_1'), (('text', 'text_1_a'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_2'), (('text', 'text_2_a'),)),
            ObjectMapping(base.ObjectMeta(objects.Audio, name='audio'), (('url', 'audio_b'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_1'), (('text', 'text_1_b'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_2'), (('text', 'text_2_b'),)),
        ),
        output_mapping=(ObjectMapping(base.ObjectMeta(base.SbSChoice, name='choice'), (('value', 'choice'),)),),
    )
    assert sbs_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.CompareLayoutV1(
                    items=[
                        tb.CompareLayoutItem(
                            content=tb.ListViewV1(
                                items=[
                                    tb.AudioViewV1(
                                        url=tb.InputData(path='audio_a'), validation=tb.PlayedFullyConditionV1()
                                    ),
                                    tb.TextViewV1(content=tb.InputData(path='text_1_a')),
                                    tb.TextViewV1(content=tb.InputData(path='text_2_a')),
                                ]
                            )
                        ),
                        tb.CompareLayoutItem(
                            content=tb.ListViewV1(
                                items=[
                                    tb.AudioViewV1(
                                        url=tb.InputData(path='audio_b'), validation=tb.PlayedFullyConditionV1()
                                    ),
                                    tb.TextViewV1(content=tb.InputData(path='text_1_b')),
                                    tb.TextViewV1(content=tb.InputData(path='text_2_b')),
                                ]
                            )
                        ),
                    ],
                    common_controls=tb.ColumnsLayoutV1(
                        items=[
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='choice'),
                                disabled=False,
                                options=[tb.GroupFieldOption(label='Left option', value='a')],
                            ),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='choice'),
                                disabled=False,
                                options=[tb.GroupFieldOption(label='Right option', value='b')],
                            ),
                        ],
                        min_width=10.0,
                        vertical_align='top',
                        validation=tb.RequiredConditionV1(
                            hint='Choose one of the options', data=tb.OutputData(path='choice')
                        ),
                    ),
                    wide_common_controls=True,
                )
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('choice'), payload='a')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('choice'), payload='b')),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )


def test_sbs_project_sbs_layout_with_hint():
    builder = project_params.SbSBuilder(
        base.SbSFunction(inputs=(objects.Video,), hints=(objects.Image, objects.Image)), lang='RU'
    )
    sbs_view, sbs_mapping = builder.get_default_scenario()
    assert sbs_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image_1'), (('url', 'image_1_hint'),)),
            ObjectMapping(base.ObjectMeta(objects.Image, name='image_2'), (('url', 'image_2_hint'),)),
            ObjectMapping(base.ObjectMeta(objects.Video, name='video'), (('url', 'video_a'),)),
            ObjectMapping(base.ObjectMeta(objects.Video, name='video'), (('url', 'video_b'),)),
        ),
        output_mapping=(ObjectMapping(base.ObjectMeta(base.SbSChoice, name='choice'), (('value', 'choice'),)),),
    )
    assert sbs_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.ImageViewV1(url=tb.InputData(path='image_1_hint')),
                tb.ImageViewV1(url=tb.InputData(path='image_2_hint')),
                tb.SideBySideLayoutV1(
                    items=[
                        tb.VideoViewV1(url=tb.InputData(path='video_a')),
                        tb.VideoViewV1(url=tb.InputData(path='video_b')),
                    ],
                    controls=tb.RadioGroupFieldV1(
                        data=tb.OutputData(path='choice'),
                        disabled=False,
                        options=[
                            tb.GroupFieldOption(label='Левый вариант', value='a'),
                            tb.GroupFieldOption(label='Правый вариант', value='b'),
                        ],
                        validation=tb.RequiredConditionV1(
                            hint='Выберите один из вариантов', data=tb.OutputData(path='choice')
                        ),
                    ),
                ),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('choice'), payload='a')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('choice'), payload='b')),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=1200.0),
                notifications=[
                    tb.TextViewV1(content='Перед выполнением проверьте, что все медиа-элементы загрузились.'),
                    tb.TextViewV1(content='Если нет хотя бы одного медиа-элемента, перезагрузите страницу.'),
                ],
            ),
        ],
    )


def test_sbs_project_expert_labeling_of_solution():
    # [x] Expert annotation of solution
    # [x] Overlapping types in input and output

    builder = project_params.SbSBuilder(
        base.SbSFunction(inputs=(objects.Audio, Animal), hints=(objects.Text,)), lang='EN'
    )

    sbs_view, sbs_mapping = builder.get_expert_labeling_of_solved_tasks()
    assert sbs_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Text, name='text'), (('text', 'text_hint'),)),
            ObjectMapping(base.ObjectMeta(objects.Audio, name='audio'), (('url', 'audio_a'),)),
            ObjectMapping(base.ObjectMeta(Animal, name='choice_1'), (('value', 'choice_1_a'),)),
            ObjectMapping(base.ObjectMeta(objects.Audio, name='audio'), (('url', 'audio_b'),)),
            ObjectMapping(base.ObjectMeta(Animal, name='choice_1'), (('value', 'choice_1_b'),)),
            ObjectMapping(base.ObjectMeta(base.SbSChoice, name='choice_2'), (('value', 'choice_2'),)),
        ),
        output_mapping=(
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='_ok',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the task (and the solution, if given) correct?',
                                'RU': 'Корректно ли задание (и решение, при наличии)?',
                            }
                        )
                    ),
                ),
                (('ok', '_ok'),),
            ),
            ObjectMapping(
                base.ObjectMeta(
                    objects.Text,
                    name='_comment',
                    title=base.Title(text=base.LocalizedString(lang_to_text={'EN': 'comment', 'RU': 'комментарий'})),
                    required=False,
                ),
                (('text', '_comment'),),
            ),
        ),
    )
    assert sbs_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text_hint')),
                tb.CompareLayoutV1(
                    items=[
                        tb.CompareLayoutItem(
                            content=tb.ListViewV1(
                                items=[
                                    tb.AudioViewV1(
                                        url=tb.InputData(path='audio_a'), validation=tb.PlayedFullyConditionV1()
                                    ),
                                    tb.RadioGroupFieldV1(
                                        data=tb.InternalData(
                                            path='choice_1_a', default=tb.InputData(path='choice_1_a')
                                        ),
                                        disabled=True,
                                        options=[
                                            tb.GroupFieldOption(value='dog', label='DOG'),
                                            tb.GroupFieldOption(value='cat', label='CAT'),
                                        ],
                                    ),
                                ]
                            )
                        ),
                        tb.CompareLayoutItem(
                            content=tb.ListViewV1(
                                items=[
                                    tb.AudioViewV1(
                                        url=tb.InputData(path='audio_b'), validation=tb.PlayedFullyConditionV1()
                                    ),
                                    tb.RadioGroupFieldV1(
                                        data=tb.InternalData(
                                            path='choice_1_b', default=tb.InputData(path='choice_1_b')
                                        ),
                                        disabled=True,
                                        options=[
                                            tb.GroupFieldOption(value='dog', label='DOG'),
                                            tb.GroupFieldOption(value='cat', label='CAT'),
                                        ],
                                    ),
                                ]
                            )
                        ),
                    ],
                    common_controls=tb.ColumnsLayoutV1(
                        items=[
                            tb.RadioGroupFieldV1(
                                data=tb.InternalData(path='choice_2', default=tb.InputData(path='choice_2')),
                                disabled=True,
                                options=[tb.GroupFieldOption(label='Left option', value='a')],
                            ),
                            tb.RadioGroupFieldV1(
                                data=tb.InternalData(path='choice_2', default=tb.InputData(path='choice_2')),
                                disabled=True,
                                options=[tb.GroupFieldOption(label='Right option', value='b')],
                            ),
                        ],
                        min_width=10.0,
                        vertical_align='top',
                    ),
                    wide_common_controls=True,
                ),
                tb.MarkdownViewV1(content='---'),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Is the task (and the solution, if given) correct?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='_ok'),
                                disabled=False,
                                options=[
                                    tb.GroupFieldOption(value=True, label='Yes'),
                                    tb.GroupFieldOption(value=False, label='No'),
                                ],
                                validation=tb.RequiredConditionV1(
                                    hint='Choose one of the options',
                                    data=tb.OutputData(path='_ok'),
                                ),
                            ),
                        ]
                    )
                ),
                tb.TextareaFieldV1(data=tb.OutputData(path='_comment'), placeholder='comment'),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('_ok'), payload=True)),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('_ok'), payload=False)),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )


def test_classification_project():
    # [x] Localization fallback to EN
    # [x] Multiple objects of same type in input/output
    # [x] Label as input
    # [x] Overlapping types in input and output

    builder = project_params.ClassificationBuilder(
        base.ClassificationFunction(inputs=(objects.Text, objects.Text, Animal), cls=Animal), lang='RU'
    )

    classification_view, classification_mapping = builder.get_default_scenario()

    assert classification_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_1'), (('text', 'text_1'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_2'), (('text', 'text_2'),)),
            ObjectMapping(base.ObjectMeta(Animal, name='choice_1'), (('value', 'choice_1'),)),
        ),
        output_mapping=(ObjectMapping(base.ObjectMeta(Animal, name='choice_2'), (('value', 'choice_2'),)),),
    )
    assert classification_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text_1')),
                tb.TextViewV1(content=tb.InputData(path='text_2')),
                tb.RadioGroupFieldV1(
                    data=tb.InternalData(path='choice_1', default=tb.InputData(path='choice_1')),
                    options=[
                        tb.GroupFieldOption(value='dog', label='DOG'),  # fallback to EN
                        tb.GroupFieldOption(value='cat', label='CAT'),
                    ],  # fallback to EN
                    disabled=True,
                ),
                tb.RadioGroupFieldV1(
                    data=tb.OutputData(path='choice_2'),
                    options=[
                        tb.GroupFieldOption(value='dog', label='DOG'),  # fallback to EN
                        tb.GroupFieldOption(value='cat', label='CAT'),
                    ],  # fallback to EN
                    disabled=False,
                    validation=tb.RequiredConditionV1(
                        hint='Выберите один из вариантов', data=tb.OutputData(path='choice_2')
                    ),
                ),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('choice_2'), payload='dog')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('choice_2'), payload='cat')),
            tb.TolokaPluginV1(layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0)),
        ],
    )


def test_classification_project_expert_labeling_of_tasks():
    # [x] Expert annotation of task
    builder = project_params.ClassificationBuilder(
        base.ClassificationFunction(inputs=(objects.Text,), cls=Animal), lang='EN'
    )

    classification_view, classification_mapping = builder.get_expert_labeling_of_tasks()
    assert classification_mapping == TaskMapping(
        input_mapping=(ObjectMapping(base.ObjectMeta(objects.Text, name='text'), (('text', 'text'),)),),
        output_mapping=(
            ObjectMapping(base.ObjectMeta(Animal, name='choice'), (('value', 'choice'),)),
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='_ok',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the task (and the solution, if given) correct?',
                                'RU': 'Корректно ли задание (и решение, при наличии)?',
                            }
                        )
                    ),
                ),
                (('ok', '_ok'),),
            ),
            ObjectMapping(
                base.ObjectMeta(
                    objects.Text,
                    name='_comment',
                    title=base.Title(text=base.LocalizedString(lang_to_text={'EN': 'comment', 'RU': 'комментарий'})),
                    required=False,
                ),
                (('text', '_comment'),),
            ),
        ),
    )
    assert classification_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text')),
                tb.RadioGroupFieldV1(
                    data=tb.OutputData(path='choice'),
                    options=[
                        tb.GroupFieldOption(value='dog', label='DOG'),
                        tb.GroupFieldOption(value='cat', label='CAT'),
                    ],
                    disabled=False,
                    validation=tb.RequiredConditionV1(
                        hint='Choose one of the options', data=tb.OutputData(path='choice')
                    ),
                ),
                tb.MarkdownViewV1('---'),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Is the task (and the solution, if given) correct?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='_ok'),
                                disabled=False,
                                options=[
                                    tb.GroupFieldOption(value=True, label='Yes'),
                                    tb.GroupFieldOption(value=False, label='No'),
                                ],
                                validation=tb.RequiredConditionV1(
                                    hint='Choose one of the options',
                                    data=tb.OutputData(path='_ok'),
                                ),
                            ),
                        ]
                    )
                ),
                tb.TextareaFieldV1(data=tb.OutputData(path='_comment'), placeholder='comment'),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('choice'), payload='dog')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('choice'), payload='cat')),
            tb.HotkeysPluginV1(key_3=tb.SetActionV1(data=tb.OutputData('_ok'), payload=True)),
            tb.HotkeysPluginV1(key_4=tb.SetActionV1(data=tb.OutputData('_ok'), payload=False)),
            tb.TolokaPluginV1(layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0)),
        ],
    )


def test_annotation_project():
    # [x] Label as input
    # [x] Overlapping types in input and output
    task_spec = spec.AnnotationTaskSpec(
        task_spec=base.TaskSpec(
            id='id',
            instruction=None,  # noqa
            name=base.LocalizedString({'EN': 'name'}),
            description=base.LocalizedString({'EN': 'desc'}),
            function=base.AnnotationFunction(
                inputs=(objects.Image, objects.Text), outputs=(objects.Text, lib.ImageClass)
            ),
        ),
        lang='EN',
    )

    annotation_view, annotation_mapping = task_spec.view, task_spec.task_mapping
    check_view, check_mapping = task_spec.check.view, task_spec.check.task_mapping

    assert annotation_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image'), (('url', 'image'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_1'), (('text', 'text_1'),)),
        ),
        output_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_2'), (('text', 'text_2'),)),
            ObjectMapping(base.ObjectMeta(lib.ImageClass, name='choice'), (('value', 'choice'),)),
        ),
    )
    assert check_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image'), (('url', 'image'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_1'), (('text', 'text_1'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text_2'), (('text', 'text_2'),)),
            ObjectMapping(base.ObjectMeta(lib.ImageClass, name='choice'), (('value', 'choice'),)),
        ),
        output_mapping=(
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='eval',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the solution accurate?',
                                'KK': 'Тапсырманың шешімі дұрыс па?',
                                'RU': 'Решение верное?',
                                'TR': 'Görevin kararı doğru mu?',
                            }
                        )
                    ),
                ),
                (('ok', 'eval'),),
            ),
        ),
    )
    assert annotation_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.ImageViewV1(url=tb.InputData(path='image')),
                tb.TextViewV1(content=tb.InputData(path='text_1')),
                tb.TextareaFieldV1(data=tb.OutputData(path='text_2')),
                tb.RadioGroupFieldV1(
                    data=tb.OutputData(path='choice'),
                    disabled=False,
                    options=[
                        tb.GroupFieldOption(value='dog', label='dog'),
                        tb.GroupFieldOption(value='cat', label='cat'),
                        tb.GroupFieldOption(value='crow', label='crow'),
                    ],
                    validation=tb.RequiredConditionV1(
                        hint='Choose one of the options', data=tb.OutputData(path='choice')
                    ),
                ),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('choice'), payload='dog')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('choice'), payload='cat')),
            tb.HotkeysPluginV1(key_3=tb.SetActionV1(data=tb.OutputData('choice'), payload='crow')),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )
    assert check_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.ImageViewV1(url=tb.InputData(path='image')),
                tb.TextViewV1(content=tb.InputData(path='text_1')),
                tb.TextViewV1(content=tb.InputData(path='text_2')),
                tb.RadioGroupFieldV1(
                    data=tb.InternalData(path='choice', default=tb.InputData(path='choice')),
                    options=[
                        tb.GroupFieldOption(value='dog', label='dog'),
                        tb.GroupFieldOption(value='cat', label='cat'),
                        tb.GroupFieldOption(value='crow', label='crow'),
                    ],
                    disabled=True,
                ),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Is the solution accurate?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='eval'),
                                options=[
                                    tb.GroupFieldOption(value=True, label='Yes'),
                                    tb.GroupFieldOption(value=False, label='No'),
                                ],
                                disabled=False,
                                validation=tb.RequiredConditionV1(
                                    hint='Choose one of the options', data=tb.OutputData(path='eval')
                                ),
                            ),
                        ]
                    )
                ),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('eval'), payload=True)),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('eval'), payload=False)),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )


def test_classification_project_with_object_metas_and_titles_and_custom_text_format():
    # [x] Definition through ObjectMeta
    # [x] Titles for Label types
    # [x] Custom Text format

    builder = project_params.ClassificationBuilder(
        base.ClassificationFunction(
            inputs=(objects.TextMeta(objects.Text, name='description', format=base.TextFormat.MARKDOWN),),
            cls=base.ClassMeta(
                Animal,
                name='animal',
                title=base.Title(
                    text=base.LocalizedString({'EN': 'Which animal best describes this text?'}),
                    format=base.TextFormat.MARKDOWN,
                ),
            ),
        ),
        lang='EN',
    )

    classification_view, classification_mapping = builder.get_default_scenario()

    assert classification_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(
                objects.TextMeta(objects.Text, name='description', format=base.TextFormat.MARKDOWN),
                (('text', 'description'),),
            ),
        ),
        output_mapping=(
            ObjectMapping(
                base.ClassMeta(
                    Animal,
                    name='animal',
                    title=base.Title(
                        text=base.LocalizedString({'EN': 'Which animal best describes this text?'}),
                        format=base.TextFormat.MARKDOWN,
                    ),
                ),
                (('value', 'animal'),),
            ),
        ),
    )
    assert classification_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.MarkdownViewV1(content=tb.InputData(path='description')),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.MarkdownViewV1(content='Which animal best describes this text?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='animal'),
                                options=[
                                    tb.GroupFieldOption(value='dog', label='DOG'),
                                    tb.GroupFieldOption(value='cat', label='CAT'),
                                ],
                                disabled=False,
                                validation=tb.RequiredConditionV1(
                                    hint='Choose one of the options', data=tb.OutputData(path='animal')
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('animal'), payload='dog')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('animal'), payload='cat')),
            tb.TolokaPluginV1(layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0)),
        ],
    )


class Topic(base.Class):
    MOVIE = 'movie'
    NEWS = 'news'


class Review(base.Class):
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'
    SKEPTICAL = 'skeptical'
    APPROVING = 'approving'


options_if = base.create_available_labels_if(
    'topic',
    [
        (Topic.MOVIE.value, [Review.POSITIVE, Review.NEGATIVE, Review.NEUTRAL]),
        (Topic.NEWS.value, [Review.SKEPTICAL, Review.APPROVING]),
    ],
)


def test_sbs_project_with_conditional_options():
    # [x] Conditional options for Class
    # [x] Condition on input argument
    # [x] Conditions transform for SbS function

    builder = project_params.SbSBuilder(
        base.SbSFunction(
            inputs=(
                base.ClassMeta(Topic, name='topic'),
                base.ClassMeta(Review, name='review', available_labels=options_if),
            ),
        ),
        lang='RU',
    )
    sbs_view, sbs_mapping = builder.get_default_scenario()
    assert sbs_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ClassMeta(Topic, name='topic'), (('value', 'topic_a'),)),
            ObjectMapping(base.ClassMeta(Review, name='review', available_labels=options_if), (('value', 'review_a'),)),
            ObjectMapping(base.ClassMeta(Topic, name='topic'), (('value', 'topic_b'),)),
            ObjectMapping(base.ClassMeta(Review, name='review', available_labels=options_if), (('value', 'review_b'),)),
        ),
        output_mapping=(ObjectMapping(base.ObjectMeta(base.SbSChoice, name='choice'), (('value', 'choice'),)),),
    )
    assert sbs_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.CompareLayoutV1(
                    items=[
                        tb.CompareLayoutItem(
                            content=tb.ListViewV1(
                                items=[
                                    tb.RadioGroupFieldV1(
                                        data=tb.InternalData(path='topic_a', default=tb.InputData(path='topic_a')),
                                        options=[
                                            tb.GroupFieldOption(value='movie', label='movie'),
                                            tb.GroupFieldOption(value='news', label='news'),
                                        ],
                                        disabled=True,
                                    ),
                                    tb.IfHelperV1(
                                        condition=tb.EqualsConditionV1(
                                            data=tb.InputData(path='topic_a'),
                                            to='movie',
                                        ),
                                        then=tb.RadioGroupFieldV1(
                                            data=tb.InternalData(
                                                path='review_a', default=tb.InputData(path='review_a')
                                            ),
                                            options=[
                                                tb.GroupFieldOption(value='positive', label='positive'),
                                                tb.GroupFieldOption(value='negative', label='negative'),
                                                tb.GroupFieldOption(value='neutral', label='neutral'),
                                            ],
                                            disabled=True,
                                        ),
                                        else_=tb.IfHelperV1(
                                            condition=tb.EqualsConditionV1(
                                                data=tb.InputData(path='topic_a'),
                                                to='news',
                                            ),
                                            then=tb.RadioGroupFieldV1(
                                                data=tb.InternalData(
                                                    path='review_a', default=tb.InputData(path='review_a')
                                                ),
                                                options=[
                                                    tb.GroupFieldOption(value='skeptical', label='skeptical'),
                                                    tb.GroupFieldOption(value='approving', label='approving'),
                                                ],
                                                disabled=True,
                                            ),
                                        ),
                                    ),
                                ]
                            )
                        ),
                        tb.CompareLayoutItem(
                            content=tb.ListViewV1(
                                items=[
                                    tb.RadioGroupFieldV1(
                                        data=tb.InternalData(path='topic_b', default=tb.InputData(path='topic_b')),
                                        options=[
                                            tb.GroupFieldOption(value='movie', label='movie'),
                                            tb.GroupFieldOption(value='news', label='news'),
                                        ],
                                        disabled=True,
                                    ),
                                    tb.IfHelperV1(
                                        condition=tb.EqualsConditionV1(
                                            data=tb.InputData(path='topic_b'),
                                            to='movie',
                                        ),
                                        then=tb.RadioGroupFieldV1(
                                            data=tb.InternalData(
                                                path='review_b', default=tb.InputData(path='review_b')
                                            ),
                                            options=[
                                                tb.GroupFieldOption(value='positive', label='positive'),
                                                tb.GroupFieldOption(value='negative', label='negative'),
                                                tb.GroupFieldOption(value='neutral', label='neutral'),
                                            ],
                                            disabled=True,
                                        ),
                                        else_=tb.IfHelperV1(
                                            condition=tb.EqualsConditionV1(
                                                data=tb.InputData(path='topic_b'),
                                                to='news',
                                            ),
                                            then=tb.RadioGroupFieldV1(
                                                data=tb.InternalData(
                                                    path='review_b', default=tb.InputData(path='review_b')
                                                ),
                                                options=[
                                                    tb.GroupFieldOption(value='skeptical', label='skeptical'),
                                                    tb.GroupFieldOption(value='approving', label='approving'),
                                                ],
                                                disabled=True,
                                            ),
                                        ),
                                    ),
                                ]
                            )
                        ),
                    ],
                    common_controls=tb.ColumnsLayoutV1(
                        items=[
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='choice'),
                                disabled=False,
                                options=[tb.GroupFieldOption(label='Левый вариант', value='a')],
                            ),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='choice'),
                                disabled=False,
                                options=[tb.GroupFieldOption(label='Правый вариант', value='b')],
                            ),
                        ],
                        min_width=10.0,
                        vertical_align='top',
                        validation=tb.RequiredConditionV1(
                            hint='Выберите один из вариантов', data=tb.OutputData(path='choice')
                        ),
                    ),
                    wide_common_controls=True,
                )
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('choice'), payload='a')),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('choice'), payload='b')),
            tb.TolokaPluginV1(layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0)),
        ],
    )


def test_annotation_project_with_conditional_options_solved_tasks_verification():
    # [x] Condition on argument moved from output to input
    # [x] Conditional options for Class

    task_spec = base.TaskSpec(
        id='id',
        instruction=None,  # noqa
        name=base.LocalizedString({'EN': 'name'}),
        description=base.LocalizedString({'EN': 'desc'}),
        function=base.AnnotationFunction(
            inputs=(base.ObjectMeta(objects.Image, name='picture'),),
            outputs=(
                base.ObjectMeta(objects.Text, name='comment'),
                base.ClassMeta(Topic, name='topic'),
                base.ClassMeta(Review, name='review', available_labels=options_if),
            ),
        ),
    )
    experts_task_spec = spec.AnnotationTaskSpec(
        task_spec,
        'RU',
        project_params.Scenario.EXPERT_LABELING_OF_TASKS,
    )
    view, task_mapping = experts_task_spec.check.view, experts_task_spec.check.task_mapping
    assert task_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='picture'), (('url', 'picture'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='comment'), (('text', 'comment'),)),
            ObjectMapping(base.ClassMeta(Topic, name='topic'), (('value', 'topic'),)),
            ObjectMapping(base.ClassMeta(Review, name='review', available_labels=options_if), (('value', 'review'),)),
        ),
        output_mapping=(
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='eval',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the solution accurate?',
                                'KK': 'Тапсырманың шешімі дұрыс па?',
                                'RU': 'Решение верное?',
                                'TR': 'Görevin kararı doğru mu?',
                            }
                        )
                    ),
                ),
                (('ok', 'eval'),),
            ),
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='_ok',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the task (and the solution, if given) correct?',
                                'RU': 'Корректно ли задание (и решение, при наличии)?',
                            }
                        )
                    ),
                ),
                (('ok', '_ok'),),
            ),
            ObjectMapping(
                base.ObjectMeta(
                    objects.Text,
                    name='_comment',
                    title=base.Title(text=base.LocalizedString(lang_to_text={'EN': 'comment', 'RU': 'комментарий'})),
                    required=False,
                ),
                (('text', '_comment'),),
            ),
        ),
    )
    assert view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.ImageViewV1(url=tb.InputData(path='picture')),
                tb.TextViewV1(content=tb.InputData(path='comment')),
                tb.RadioGroupFieldV1(
                    data=tb.InternalData(path='topic', default=tb.InputData(path='topic')),
                    options=[
                        tb.GroupFieldOption(value='movie', label='movie'),
                        tb.GroupFieldOption(value='news', label='news'),
                    ],
                    disabled=True,
                ),
                tb.IfHelperV1(
                    condition=tb.EqualsConditionV1(
                        data=tb.InputData(path='topic'),
                        to='movie',
                    ),
                    then=tb.RadioGroupFieldV1(
                        data=tb.InternalData(path='review', default=tb.InputData(path='review')),
                        options=[
                            tb.GroupFieldOption(value='positive', label='positive'),
                            tb.GroupFieldOption(value='negative', label='negative'),
                            tb.GroupFieldOption(value='neutral', label='neutral'),
                        ],
                        disabled=True,
                    ),
                    else_=tb.IfHelperV1(
                        condition=tb.EqualsConditionV1(
                            data=tb.InputData(path='topic'),
                            to='news',
                        ),
                        then=tb.RadioGroupFieldV1(
                            data=tb.InternalData(path='review', default=tb.InputData(path='review')),
                            options=[
                                tb.GroupFieldOption(value='skeptical', label='skeptical'),
                                tb.GroupFieldOption(value='approving', label='approving'),
                            ],
                            disabled=True,
                        ),
                    ),
                ),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Решение верное?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='eval'),
                                options=[
                                    tb.GroupFieldOption(value=True, label='Да'),
                                    tb.GroupFieldOption(value=False, label='Нет'),
                                ],
                                disabled=False,
                                validation=tb.RequiredConditionV1(
                                    hint='Выберите один из вариантов', data=tb.OutputData(path='eval')
                                ),
                            ),
                        ]
                    )
                ),
                tb.MarkdownViewV1('---'),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Корректно ли задание (и решение, при наличии)?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='_ok'),
                                disabled=False,
                                options=[
                                    tb.GroupFieldOption(value=True, label='Да'),
                                    tb.GroupFieldOption(value=False, label='Нет'),
                                ],
                                validation=tb.RequiredConditionV1(
                                    hint='Выберите один из вариантов',
                                    data=tb.OutputData(path='_ok'),
                                ),
                            ),
                        ]
                    )
                ),
                tb.TextareaFieldV1(data=tb.OutputData(path='_comment'), placeholder='комментарий'),
            ]
        ),
        plugins=[
            tb.HotkeysPluginV1(key_1=tb.SetActionV1(data=tb.OutputData('eval'), payload=True)),
            tb.HotkeysPluginV1(key_2=tb.SetActionV1(data=tb.OutputData('eval'), payload=False)),
            tb.HotkeysPluginV1(key_3=tb.SetActionV1(data=tb.OutputData('_ok'), payload=True)),
            tb.HotkeysPluginV1(key_4=tb.SetActionV1(data=tb.OutputData('_ok'), payload=False)),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=700.0),
                notifications=[
                    tb.TextViewV1(content='Перед выполнением проверьте, что все медиа-элементы загрузились.'),
                    tb.TextViewV1(content='Если нет хотя бы одного медиа-элемента, перезагрузите страницу.'),
                ],
            ),
        ],
    )


def test_default_image_annotation():
    task_spec = spec.AnnotationTaskSpec(
        task_spec=base.TaskSpec(
            id='id',
            instruction=None,  # noqa
            name=base.LocalizedString({'EN': 'name'}),
            description=base.LocalizedString({'EN': 'desc'}),
            function=base.AnnotationFunction(
                inputs=(objects.Image, objects.Text),
                outputs=(base.ImageAnnotation,),
            ),
        ),
        lang='EN',
    )

    image_annotation_view, image_annotation_mapping = task_spec.view, task_spec.task_mapping
    image_annotation_check_view, image_annotation_check_mapping = task_spec.check.view, task_spec.check.task_mapping

    assert image_annotation_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image'), (('url', 'image'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text'), (('text', 'text'),)),
        ),
        output_mapping=(
            ObjectMapping(
                base.ObjectMeta(
                    base.ImageAnnotation,
                    name='image_annotation',
                ),
                (('data', 'image_annotation'),),
            ),
        ),
    )
    assert image_annotation_check_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image'), (('url', 'image'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text'), (('text', 'text'),)),
            ObjectMapping(
                base.ObjectMeta(
                    base.ImageAnnotation,
                    name='image_annotation',
                ),
                (('data', 'image_annotation'),),
            ),
        ),
        output_mapping=(
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='eval',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the solution accurate?',
                                'KK': 'Тапсырманың шешімі дұрыс па?',
                                'RU': 'Решение верное?',
                                'TR': 'Görevin kararı doğru mu?',
                            }
                        )
                    ),
                ),
                (('ok', 'eval'),),
            ),
        ),
    )
    assert image_annotation_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text')),
                tb.ImageAnnotationFieldV1(
                    data=tb.OutputData(path='image_annotation'),
                    image=tb.InputData(path='image'),
                    validation=tb.conditions.RequiredConditionV1(
                        data=tb.OutputData(path='image_annotation'), hint='Select at least one area'
                    ),
                    full_height=True,
                ),
            ]
        ),
        plugins=[
            tb.ImageAnnotationHotkeysPluginV1(),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='pager'),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )
    assert image_annotation_check_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text')),
                tb.ImageAnnotationFieldV1(
                    data=tb.InternalData(path='image_annotation', default=tb.InputData(path='image_annotation')),
                    image=tb.InputData(path='image'),
                    disabled=True,
                    full_height=True,
                ),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Is the solution accurate?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='eval'),
                                options=[
                                    tb.GroupFieldOption(value=True, label='Yes'),
                                    tb.GroupFieldOption(value=False, label='No'),
                                ],
                                disabled=False,
                                validation=tb.RequiredConditionV1(
                                    hint='Choose one of the options', data=tb.OutputData(path='eval')
                                ),
                            ),
                        ]
                    )
                ),
            ]
        ),
        plugins=[
            tb.ImageAnnotationHotkeysPluginV1(),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='pager'),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )


def test_custom_image_annotation():
    class Area(base.Class):
        CAR = 'car'
        SIGN = 'sign'
        OTHER = 'other'

        @classmethod
        def labels(cls) -> Dict['Area', Dict[str, str]]:
            return {
                cls.CAR: {'EN': 'A car', 'RU': 'Машина'},
                cls.SIGN: {'EN': 'A sign', 'RU': 'Знак'},
                cls.OTHER: {'EN': 'Something else', 'RU': 'Другое'},
            }

    task_spec = spec.AnnotationTaskSpec(
        task_spec=base.TaskSpec(
            id='id',
            instruction=None,  # noqa
            name=base.LocalizedString({'EN': 'name'}),
            description=base.LocalizedString({'EN': 'desc'}),
            function=base.AnnotationFunction(
                inputs=(
                    base.ObjectMeta(type=objects.Image),
                    base.ObjectMeta(objects.Text),
                ),
                outputs=(
                    base.ImageAnnotationMeta(
                        type=base.ImageAnnotation,
                        available_shapes={tb.fields.ImageAnnotationFieldV1.Shape.POLYGON},
                        labels=Area,
                    ),
                ),
            ),
        ),
        lang='EN',
    )

    image_annotation_view, image_annotation_mapping = task_spec.view, task_spec.task_mapping
    image_annotation_check_view, image_annotation_check_mapping = task_spec.check.view, task_spec.check.task_mapping

    assert image_annotation_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image'), (('url', 'image'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text'), (('text', 'text'),)),
        ),
        output_mapping=(
            ObjectMapping(
                base.ImageAnnotationMeta(
                    base.ImageAnnotation,
                    name='image_annotation',
                    available_shapes={tb.fields.ImageAnnotationFieldV1.Shape.POLYGON},
                    labels=Area,
                ),
                (('data', 'image_annotation'),),
            ),
        ),
    )
    assert image_annotation_check_mapping == TaskMapping(
        input_mapping=(
            ObjectMapping(base.ObjectMeta(objects.Image, name='image'), (('url', 'image'),)),
            ObjectMapping(base.ObjectMeta(objects.Text, name='text'), (('text', 'text'),)),
            ObjectMapping(
                base.ImageAnnotationMeta(
                    base.ImageAnnotation,
                    name='image_annotation',
                    available_shapes={tb.fields.ImageAnnotationFieldV1.Shape.POLYGON},
                    labels=Area,
                ),
                (('data', 'image_annotation'),),
            ),
        ),
        output_mapping=(
            ObjectMapping(
                base.EvaluationMeta(
                    base.BinaryEvaluation,
                    name='eval',
                    title=base.Title(
                        text=base.LocalizedString(
                            lang_to_text={
                                'EN': 'Is the solution accurate?',
                                'KK': 'Тапсырманың шешімі дұрыс па?',
                                'RU': 'Решение верное?',
                                'TR': 'Görevin kararı doğru mu?',
                            }
                        )
                    ),
                ),
                (('ok', 'eval'),),
            ),
        ),
    )
    assert image_annotation_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text')),
                tb.ImageAnnotationFieldV1(
                    data=tb.OutputData(path='image_annotation'),
                    image=tb.InputData(path='image'),
                    labels=[
                        tb.ImageAnnotationFieldV1.Label(label=label, value=value)
                        for (label, value) in [('A car', 'car'), ('A sign', 'sign'), ('Something else', 'other')]
                    ],
                    shapes={tb.ImageAnnotationFieldV1.Shape.POLYGON: True},
                    validation=tb.conditions.RequiredConditionV1(
                        data=tb.OutputData(path='image_annotation'), hint='Select at least one area'
                    ),
                    full_height=True,
                ),
            ]
        ),
        plugins=[
            tb.ImageAnnotationHotkeysPluginV1(),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='pager'),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )
    assert image_annotation_check_view == toloka.project.TemplateBuilderViewSpec(
        view=tb.ListViewV1(
            items=[
                tb.TextViewV1(content=tb.InputData(path='text')),
                tb.ImageAnnotationFieldV1(
                    data=tb.InternalData(path='image_annotation', default=tb.InputData(path='image_annotation')),
                    image=tb.InputData(path='image'),
                    labels=[
                        tb.ImageAnnotationFieldV1.Label(label=label, value=value)
                        for (label, value) in [('A car', 'car'), ('A sign', 'sign'), ('Something else', 'other')]
                    ],
                    shapes={tb.ImageAnnotationFieldV1.Shape.POLYGON: True},
                    disabled=True,
                    full_height=True,
                ),
                tb.GroupViewV1(
                    content=tb.ListViewV1(
                        items=[
                            tb.TextViewV1(content='Is the solution accurate?'),
                            tb.RadioGroupFieldV1(
                                data=tb.OutputData(path='eval'),
                                options=[
                                    tb.GroupFieldOption(value=True, label='Yes'),
                                    tb.GroupFieldOption(value=False, label='No'),
                                ],
                                disabled=False,
                                validation=tb.RequiredConditionV1(
                                    hint='Choose one of the options', data=tb.OutputData(path='eval')
                                ),
                            ),
                        ]
                    )
                ),
            ]
        ),
        plugins=[
            tb.ImageAnnotationHotkeysPluginV1(),
            tb.TolokaPluginV1(
                layout=tb.TolokaPluginV1.TolokaPluginLayout(kind='pager'),
                notifications=[
                    tb.TextViewV1(content='Before performing a task, make sure that all media elements have loaded.'),
                    tb.TextViewV1(content='If at least one media element is missing, reload the page.'),
                ],
            ),
        ],
    )
