from collections import defaultdict
from dataclasses import dataclass
import pytest

import toloka.client as toloka

from crowdom import base, mapping
from crowdom.objects import Audio, Image, Text
from . import lib


class TestValues:
    @dataclass
    class TestObject(base.Object):
        name: str
        count: int
        ready: bool

    @dataclass
    class TestObjectChild(TestObject):
        desc: str

    @dataclass
    class InvalidObject1(base.Object):
        volume: float

    @dataclass
    class InvalidObject2(base.Object):
        audio_class: lib.AudioClass

    def test_primitive_types_conversion(self):
        obj = self.TestObject(name='my obj name', count=42, ready=True)
        values = {'name': 'my obj name', 'count': 42, 'ready': True}

        assert mapping.obj_to_values(obj) == values
        assert mapping.values_to_obj(values, self.TestObject) == obj

    def test_class_conversion(self):
        obj = lib.sp
        values = {base.CLASS_OBJ_FIELD: 'sp'}

        assert mapping.obj_to_values(obj) == values
        assert mapping.values_to_obj(values, lib.AudioClass) == obj

    def test_inherited_fields(self):
        obj = self.TestObjectChild(name='my obj name', count=42, ready=True, desc='detailed desc')
        values = {'name': 'my obj name', 'count': 42, 'ready': True, 'desc': 'detailed desc'}

        assert mapping.obj_to_values(obj) == values
        assert mapping.values_to_obj(values, self.TestObjectChild) == obj

    def test_invalid_objects(self):
        with pytest.raises(ValueError) as e:
            mapping.obj_to_values(self.InvalidObject1(volume=0.5))
        assert str(e.value) == "object field \"volume\" has unsupported type <class 'float'>"

        with pytest.raises(ValueError) as e:
            mapping.obj_to_values(self.InvalidObject2(audio_class=lib.sp))
        assert str(e.value) == "object field \"audio_class\" has unsupported type <enum 'AudioClass'>"

    def test_invalid_values(self):
        with pytest.raises(ValueError) as e:
            mapping.values_to_obj({base.CLASS_OBJ_FIELD: 1}, lib.AudioClass)
        assert str(e.value) == '1 is not a valid AudioClass'

        with pytest.raises(AssertionError) as e:
            mapping.values_to_obj({'name': 'my obj name', 'count': 'some', 'ready': True}, self.TestObject)
        assert str(e.value) == "obj field type <class 'int'> does not match to values type <class 'str'>"

        with pytest.raises(TypeError) as e:
            mapping.values_to_obj({'name': 'my obj name', 'count': 42}, self.TestObject)
        assert str(e.value).endswith("__init__() missing 1 required positional argument: 'ready'")


class TestMapping:
    def test_object_mapping(self):
        assert lib.audio_mapping.to_values(Audio(url='https://1.wav')) == {'audio_link': 'https://1.wav'}
        assert lib.audio_mapping.from_values({'audio_link': 'https://1.wav'}) == Audio(url='https://1.wav')

    def test_object_mapping_on_none(self):
        with pytest.raises(AssertionError) as e:
            lib.audio_mapping.to_values(None)
        assert str(e.value) == (
            "object ObjectMeta(type=<class 'crowdom.objects.std.Audio'>, name=None, "
            "title=None, required=True) is required"
        )

        with pytest.raises(AssertionError) as e:
            lib.audio_mapping.from_values({})
        assert str(e.value) == (
            "missing fields {'audio_link'} in required object ObjectMeta(type=<class "
            "'crowdom.objects.std.Audio'>, name=None, title=None, required=True)"
        )

        assert lib.text_mapping.from_values({}) is None
        assert lib.text_mapping.to_values(None) == {}

    def test_invalid_object_mapping_not_dataclass(self):
        class NotDataclass:
            pass

        with pytest.raises(AssertionError) as e:
            mapping.ObjectMapping(obj_meta=base.ObjectMeta(NotDataclass), obj_task_fields=()).validate()
        assert str(e.value) == f'{NotDataclass} is not a dataclass nor an options class'

    def test_invalid_object_mapping_missing_object_field(self):
        with pytest.raises(AssertionError) as e:
            mapping.ObjectMapping(obj_meta=base.ObjectMeta(Audio), obj_task_fields=(('link', 'url'),)).validate()
        assert str(e.value) == f'{Audio} does not have attribute "link"'

    def test_invalid_task_mapping_fields_intersection(self):
        with pytest.raises(AssertionError) as e:
            mapping.TaskMapping(
                input_mapping=(
                    mapping.ObjectMapping(obj_meta=base.ObjectMeta(Image), obj_task_fields=(('url', 'url'),)),
                    mapping.ObjectMapping(obj_meta=base.ObjectMeta(Image), obj_task_fields=(('url', 'url'),)),
                ),
                output_mapping=(
                    mapping.ObjectMapping(
                        obj_meta=base.ObjectMeta(lib.ImageClass), obj_task_fields=(('value', 'choice'),)
                    ),
                ),
            ).validate()
        assert str(e.value) == "fields intersection in mapping list: ['url', 'url']"

    def test_object_mapping_to_values_wrong_object_class(self):
        with pytest.raises(AssertionError) as e:
            lib.audio_mapping.to_values(Text(text='hi'))
        assert str(e.value) == f'passed {Text} does not correspond to mapping {Audio}'

    def test_task_mapping(self):
        assert lib.audio_transcript_ext_mapping.to_task((Audio(url='https://1.wav'),)) == toloka.Task(
            input_values={'audio_link': 'https://1.wav', 'id': 'Audio(url=\'https://1.wav\')'}
        )

        assert lib.audio_transcript_ext_mapping.from_task(
            toloka.Task(input_values={'audio_link': 'https://1.wav', 'id': 'Audio(url=\'https://1.wav\')'})
        ) == (Audio(url='https://1.wav'),)

        assert lib.audio_transcript_ext_mapping.to_solution((Text(text='hi'), lib.sp)) == toloka.solution.Solution(
            output_values={'output': 'hi', 'choice': 'sp'}
        )

        # text is optional
        assert lib.audio_transcript_ext_mapping.to_solution((None, lib.sp)) == toloka.solution.Solution(
            output_values={'choice': 'sp'}
        )

        assert lib.audio_transcript_ext_mapping.from_solution(
            toloka.solution.Solution(output_values={'output': 'hi', 'choice': 'sp'})
        ) == (Text(text='hi'), lib.sp)

        # text is optional
        assert lib.audio_transcript_ext_mapping.from_solution(
            toloka.solution.Solution(output_values={'choice': 'sp'})
        ) == (None, lib.sp)

    def test_task_mapping_input_objects_validation(self):
        with pytest.raises(AssertionError) as e:
            lib.audio_transcript_ext_mapping.to_solution([Text(text='hi')])
        assert str(e.value) == 'expected length 2, got 1'

        with pytest.raises(AssertionError) as e:
            lib.audio_transcript_ext_mapping.to_task([Text(text='hi')])
        assert (
            str(e.value) == "expected type <class 'crowdom.objects.std.Audio'>, got <class 'crowdom.objects.std.Text'>"
        )

        # audio class is required
        with pytest.raises(AssertionError) as e:
            lib.audio_transcript_ext_mapping.to_solution([Text(text='hi'), None])
        assert str(e.value) == "expected type <enum 'AudioClass'>, got <class 'NoneType'>"

    def test_control_task_mapping(self):
        assert lib.audio_transcript_ext_mapping.to_control_task(
            ((Audio(url='https://1.wav'),), (Text(text='hi'), lib.sp))
        ) == toloka.Task(
            input_values={'audio_link': 'https://1.wav', 'id': 'Audio(url=\'https://1.wav\')'},
            known_solutions=[
                toloka.Task.KnownSolution(output_values={'output': 'hi', 'choice': 'sp'}, correctness_weight=1)
            ],
            infinite_overlap=True,
        )

    def test_control_task_mapping_output_objects_validation(self):
        with pytest.raises(AssertionError):
            lib.audio_transcript_ext_mapping.to_control_task(((Audio(url='https://1.wav'),), (Text(text='hi'),)))

    def test_task_id(self):
        counter = defaultdict(int)
        for audio_text_pair in [
            (Audio(url='https://1.wav'), Text(text='hi')),
            (Audio(url='https://1.wav'), Text(text='')),
            (Audio(url='https://1.wav'), Text(text='hi')),
            (Audio(url='https://2.wav'), Text(text='hi')),
        ]:
            counter[lib.audio_transcript_check_mapping.task_id(audio_text_pair)] += 1

        assert {task_id.id: count for task_id, count in counter.items()} == {
            "Audio(url='https://1.wav') Text(text='hi')": 2,
            "Audio(url='https://1.wav') Text(text='')": 1,
            "Audio(url='https://2.wav') Text(text='hi')": 1,
        }

    def test_get_solutions(self):
        audios = [Audio(url=f'https://{i + 1}.wav') for i in range(3)]
        control_audio = Audio(url='https://42.wav')

        tasks = [lib.audio_transcript_ext_mapping.to_task((audio,)) for audio in audios]
        control_task = lib.audio_transcript_ext_mapping.to_control_task(
            ((control_audio,), (Text(text='let'), lib.sp))
        )

        assignment_1 = toloka.Assignment(
            tasks=[tasks[0], tasks[2], control_task],
            solutions=[
                lib.audio_transcript_ext_mapping.to_solution((Text(text='hi'), lib.sp)),
                lib.audio_transcript_ext_mapping.to_solution((Text(text='hallo'), lib.sp)),
                lib.audio_transcript_ext_mapping.to_solution((Text(text='led'), lib.sp)),
            ],
        )
        assignment_2 = toloka.Assignment(
            tasks=[tasks[2], control_task, tasks[1]],
            solutions=[
                lib.audio_transcript_ext_mapping.to_solution((Text(text=''), lib.sil)),
                lib.audio_transcript_ext_mapping.to_solution((Text(text='met'), lib.sp)),
                lib.audio_transcript_ext_mapping.to_solution((Text(text='no thanks'), lib.sp)),
            ],
        )
        assignments = [assignment_1, assignment_2]

        pool_input_objects = [(audio,) for audio in audios]

        for with_control_tasks, expected_assignments_solutions in (
            (
                False,
                [
                    (
                        assignment_1,
                        [
                            ((audios[0],), (Text(text='hi'), lib.sp)),
                            ((audios[2],), (Text(text='hallo'), lib.sp)),
                        ],
                    ),
                    (
                        assignment_2,
                        [
                            ((audios[2],), (Text(text=''), lib.sil)),
                            ((audios[1],), (Text(text='no thanks'), lib.sp)),
                        ],
                    ),
                ],
            ),
            (
                True,
                [
                    (
                        assignment_1,
                        [
                            ((audios[0],), (Text(text='hi'), lib.sp)),
                            ((audios[2],), (Text(text='hallo'), lib.sp)),
                            ((control_audio,), (Text(text='led'), lib.sp)),
                        ],
                    ),
                    (
                        assignment_2,
                        [
                            ((audios[2],), (Text(text=''), lib.sil)),
                            ((control_audio,), (Text(text='met'), lib.sp)),
                            ((audios[1],), (Text(text='no thanks'), lib.sp)),
                        ],
                    ),
                ],
            ),
        ):
            assert (
                mapping.get_assignments_solutions(assignments, lib.audio_transcript_ext_mapping, with_control_tasks)
                == expected_assignments_solutions
            )

        solutions = mapping.get_solutions(assignments, lib.audio_transcript_ext_mapping, pool_input_objects)
        solutions = [
            ([id(obj) for obj in input_objects], output_objects)  # input objects must be the same
            for input_objects, output_objects in solutions
        ]

        assert solutions == [
            (
                [id(audios[0])],
                [((Text(text='hi'), lib.sp), assignment_1)],
            ),
            (
                [id(audios[1])],
                [((Text(text='no thanks'), lib.sp), assignment_2)],
            ),
            (
                [id(audios[2])],
                [
                    ((Text(text='hallo'), lib.sp), assignment_1),
                    ((Text(text=''), lib.sil), assignment_2),
                ],
            ),
        ]

    def test_feedback_loop_mapping(self):
        assert mapping.generate_feedback_loop_mapping(
            input_objects_mapping=(lib.audio_mapping,),
            markup_objects_mapping=(lib.text_mapping, lib.audio_class_mapping),
            check_objects_mapping=(lib.binary_evaluation_mapping, lib.audio_class_mapping),
        ) == (
            mapping.TaskMapping(
                input_mapping=(lib.audio_mapping,), output_mapping=(lib.text_mapping, lib.audio_class_mapping)
            ),
            mapping.TaskMapping(
                input_mapping=(lib.audio_mapping, lib.text_mapping, lib.audio_class_mapping),
                output_mapping=(lib.binary_evaluation_mapping, lib.audio_class_mapping),
            ),
        )

    def test_feedback_loop_first_check_mapping_is_not_evaluation(self):
        with pytest.raises(AssertionError):
            mapping.generate_feedback_loop_mapping(
                input_objects_mapping=(lib.audio_mapping,),
                markup_objects_mapping=(lib.text_mapping, lib.audio_class_mapping),
                check_objects_mapping=(lib.audio_class_mapping, lib.binary_evaluation_mapping),
            )

    def test_toloka_spec_gen(self):
        task_mapping = mapping.TaskMapping(
            input_mapping=(lib.text_mapping, lib.image_mapping, lib.metadata_mapping),
            output_mapping=(
                lib.binary_evaluation_mapping,
                lib.image_class_mapping,
                lib.mos_mapping,
                lib.score_mapping,
                lib.comment_mapping,
            ),
        )
        toloka_input_spec = {
            'output': toloka.project.StringSpec(required=False),
            'image_url': toloka.project.UrlSpec(),
            'id': toloka.project.StringSpec(hidden=True),
            'extra': toloka.project.StringSpec(hidden=True),
        }
        toloka_output_spec = {
            'ok': toloka.project.BooleanSpec(allowed_values=[False, True]),
            'score': toloka.project.IntegerSpec(),
            'mos': toloka.project.FloatSpec(),
            'choice': toloka.project.StringSpec(allowed_values=['cat', 'crow', 'dog']),
            '_comment': toloka.project.StringSpec(required=False),
        }
        assert task_mapping.to_toloka_input_spec() == toloka_input_spec
        assert task_mapping.to_toloka_output_spec() == toloka_output_spec

    def test_toloka_spec_overlapping_fields(self):
        task_mapping = mapping.TaskMapping(
            input_mapping=(lib.text_mapping, lib.text_mapping), output_mapping=(lib.binary_evaluation_mapping,)
        )
        with pytest.raises(AssertionError):
            task_mapping.to_toloka_input_spec()


class TestProjectSuitability:
    def test_is_suitable(self):
        assert (
            mapping.check_project_is_suitable(
                project=toloka.Project(
                    task_spec=toloka.project.TaskSpec(
                        input_spec={
                            'audio_link': toloka.project.UrlSpec(),
                            'id': toloka.project.StringSpec(hidden=True),
                        },
                        output_spec={
                            'output': toloka.project.StringSpec(required=False),
                            'choice': toloka.project.StringSpec(allowed_values=['sil', 'sp']),
                            'comment': toloka.project.StringSpec(),  # not present in task mapping
                        },
                    )
                ),
                task_mapping=lib.audio_transcript_ext_mapping,
            )
            is True
        )

    def test_project_spec_missing_fields(self):
        assert (
            mapping.check_project_is_suitable(
                project=toloka.Project(
                    task_spec=toloka.project.TaskSpec(
                        input_spec={
                            'audio_link': toloka.project.UrlSpec(),
                            'id': toloka.project.StringSpec(hidden=True),
                        },
                        output_spec={
                            'choice': toloka.project.StringSpec(),
                        },
                    )
                ),
                task_mapping=lib.audio_transcript_ext_mapping,
            )
            is False
        )

        assert (
            mapping.check_project_is_suitable(
                project=toloka.Project(
                    task_spec=toloka.project.TaskSpec(
                        input_spec={
                            'audio_link': toloka.project.UrlSpec(),
                        },
                        output_spec={
                            'output': toloka.project.StringSpec(),
                            'choice': toloka.project.StringSpec(allowed_values=['sil', 'sp']),
                        },
                    )
                ),
                task_mapping=lib.audio_transcript_ext_mapping,
            )
            is False
        )

    def test_project_spec_not_matching_fields(self):
        assert (
            mapping.check_project_is_suitable(
                project=toloka.Project(
                    task_spec=toloka.project.TaskSpec(
                        input_spec={
                            'audio_link': toloka.project.IntegerSpec(),
                            'id': toloka.project.StringSpec(hidden=True),
                        },
                        output_spec={
                            'output': toloka.project.StringSpec(),
                            'choice': toloka.project.StringSpec(allowed_values=['sil', 'sp']),
                        },
                    )
                ),
                task_mapping=lib.audio_transcript_ext_mapping,
            )
            is False
        )

        assert (
            mapping.check_project_is_suitable(
                project=toloka.Project(
                    task_spec=toloka.project.TaskSpec(
                        input_spec={
                            'audio_link': toloka.project.StringSpec(),
                            'id': toloka.project.StringSpec(hidden=True),
                        },
                        output_spec={
                            'output': toloka.project.StringSpec(),
                            'choice': toloka.project.BooleanSpec(),
                        },
                    )
                ),
                task_mapping=lib.audio_transcript_ext_mapping,
            )
            is False
        )

        assert (
            mapping.check_project_is_suitable(
                project=toloka.Project(
                    task_spec=toloka.project.TaskSpec(
                        input_spec={
                            'audio_link': toloka.project.UrlSpec(),
                            'id': toloka.project.StringSpec(hidden=True),
                        },
                        output_spec={
                            'output': toloka.project.StringSpec(),
                            'choice': toloka.project.StringSpec(allowed_values=['sil', 'sp', 'new']),
                        },
                    )
                ),
                task_mapping=lib.audio_transcript_ext_mapping,
            )
            is False
        )
