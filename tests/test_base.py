import pandas as pd
import pytest
from typing import Dict

from crowdom import base, objects

from . import lib


def test_display():
    function = base.ClassificationFunction(
        inputs=(base.ObjectMeta(objects.Text, 'my_text'), base.ObjectMeta(objects.Image, 'my_image')),
        cls=lib.ImageClass,
    )
    df = pd.DataFrame(
        [
            {'type': 'Text', 'name': 'my_text'},
            {'type': 'Image', 'name': 'my_image'},
            {'type': 'ImageClass', 'name': 'choice'},
        ]
    )
    assert function.display_arguments(function.get_all_arguments()) == str(df)


class TestValidate:
    def test_correct_classification_no_names(self):
        base.ClassificationFunction(inputs=(objects.Text, objects.Text, objects.Image), cls=lib.ImageClass)

    def test_correct_classification_with_input_names(self):
        base.ClassificationFunction(
            inputs=(
                base.ObjectMeta(objects.Text, 'my_text'),
                base.ObjectMeta(objects.Text, 'other_text'),
                base.ObjectMeta(objects.Image, 'my_image'),
            ),
            cls=lib.ImageClass,
        )

    def test_correct_classification_with_all_names(self):
        base.ClassificationFunction(
            inputs=(
                base.ObjectMeta(objects.Text, 'my_text'),
                base.ObjectMeta(objects.Text, 'other_text'),
                base.ObjectMeta(objects.Image, 'my_image'),
            ),
            cls=base.ClassMeta(lib.ImageClass, 'my_class'),
        )

    def test_correct_sbs_no_names(self):
        base.SbSFunction(inputs=(objects.Text, objects.Text, objects.Image), hints=(objects.Text, objects.Image))

    def test_correct_annotation_no_names(self):
        base.AnnotationFunction(inputs=(objects.Text, objects.Text, objects.Image), outputs=(lib.ImageClass,))

    def test_incorrect_classification_not_object(self):
        with pytest.raises(ValueError) as e:
            base.ClassificationFunction(inputs=(int,), cls=lib.ImageClass)  # noqa
        assert str(e.value) == f'Unexpected type or instance: "{int}"'

    def test_incorrect_classification_regex_empty(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(inputs=(base.ObjectMeta(objects.Text, ''),), cls=lib.ImageClass)

        assert str(e.value) == 'Incorrect name: ""'

    def test_incorrect_classification_regex_long(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(inputs=(base.ObjectMeta(objects.Text, '1' * 31),), cls=lib.ImageClass)

        assert str(e.value) == f'Incorrect name: "{"1" * 31}"'

    def test_incorrect_classification_regex_non_ascii(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(inputs=(base.ObjectMeta(objects.Text, 'abcdeё'),), cls=lib.ImageClass)

        assert str(e.value) == 'Incorrect name: "abcdeё"'

    def test_incorrect_classification_regex_underscore(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(inputs=(base.ObjectMeta(objects.Text, '_my_name'),), cls=lib.ImageClass)

        assert str(e.value) == 'Names starting with "_" are reserved for internal usage'

    def test_incorrect_classification_missing_names_with_class_name(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(
                inputs=(objects.Text, objects.Text, objects.Image), cls=base.ClassMeta(lib.ImageClass, 'my_class')
            )
        df = pd.DataFrame(
            [
                {'type': 'Text', 'name': 'None'},
                {'type': 'Text', 'name': 'None'},
                {'type': 'Image', 'name': 'None'},
                {'type': 'ImageClass', 'name': 'my_class'},
            ]
        )
        assert str(e.value) == f'You should provide names for all types. Current names:\n{str(df)}'

    def test_incorrect_classification_missing_names(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(
                inputs=(
                    base.ObjectMeta(objects.Text, 'my_text'),
                    base.ObjectMeta(objects.Text),
                    base.ObjectMeta(objects.Image, 'my_image'),
                ),
                cls=base.ClassMeta(lib.ImageClass, 'my_class'),
            )
        df = pd.DataFrame(
            [
                {'type': 'Text', 'name': 'my_text'},
                {'type': 'Text', 'name': 'None'},
                {'type': 'Image', 'name': 'my_image'},
                {'type': 'ImageClass', 'name': 'my_class'},
            ]
        )
        assert str(e.value) == f'You should provide names for all types. Current names:\n{str(df)}'

    def test_incorrect_classification_overlapping_input_names(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(
                inputs=(
                    base.ObjectMeta(objects.Text, 'my_text'),
                    base.ObjectMeta(objects.Text, 'my_text'),
                    base.ObjectMeta(objects.Image, 'my_image'),
                ),
                cls=base.ClassMeta(lib.ImageClass, 'my_class'),
            )
        df = pd.DataFrame(
            [
                {'type': 'Text', 'name': 'my_text'},
                {'type': 'Text', 'name': 'my_text'},
                {'type': 'Image', 'name': 'my_image'},
                {'type': 'ImageClass', 'name': 'my_class'},
            ]
        )
        assert str(e.value) == f'Names should be unique. Current names:\n{str(df)}'

    def test_incorrect_classification_overlapping_class_name(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(
                inputs=(
                    base.ObjectMeta(objects.Text, 'my_text'),
                    base.ObjectMeta(objects.Text, 'choice'),
                    base.ObjectMeta(objects.Image, 'my_image'),
                ),
                cls=lib.ImageClass,
            )
        df = pd.DataFrame(
            [
                {'type': 'Text', 'name': 'my_text'},
                {'type': 'Text', 'name': 'choice'},
                {'type': 'Image', 'name': 'my_image'},
                {'type': 'ImageClass', 'name': 'choice'},
            ]
        )
        assert str(e.value) == f'Names should be unique. Current names:\n{str(df)}'

    def test_incorrect_classification_additional_validate_not_class(self):
        with pytest.raises(AssertionError):
            base.ClassificationFunction(inputs=(objects.Image,), cls=objects.Text)  # noqa

    def test_incorrect_classification_additional_validate_not_classmeta(self):
        with pytest.raises(AssertionError):
            meta = base.ObjectMeta(lib.ImageClass, 'my_class')
            base.ClassificationFunction(inputs=(base.ObjectMeta(objects.Text, 'my_text'),), cls=meta)  # noqa

    def test_incorrect_sbs_overlapping_class_name(self):
        with pytest.raises(AssertionError) as e:
            base.SbSFunction(inputs=(base.ObjectMeta(objects.Text, 'my_text'), base.ObjectMeta(objects.Text, 'choice')))
        df = pd.DataFrame(
            [
                {'type': 'Text', 'name': 'my_text'},
                {'type': 'Text', 'name': 'choice'},
                {'type': 'SbSChoice', 'name': 'choice'},
            ]
        )
        assert str(e.value) == f'Names should be unique. Current names:\n{str(df)}'

    def test_incorrect_sbs_additional_validate(self):
        with pytest.raises(NotImplementedError) as e:
            meta = base.SbSChoiceMeta(lib.ImageClass, 'choice_a')
            base.SbSFunction(inputs=(objects.Image,), choice=meta)
        assert str(e.value) == f'Unexpected type or instance: "{meta}"'

    def test_incorrect_annotation_overlapping_class_name(self):
        with pytest.raises(AssertionError) as e:
            base.AnnotationFunction(
                inputs=(base.ObjectMeta(objects.Text, 'source_text'), base.ObjectMeta(objects.Text, 'eval')),
                outputs=(base.ObjectMeta(objects.Text, 'translated_text'),),
            )
        df = pd.DataFrame(
            [
                {'type': 'Text', 'name': 'source_text'},
                {'type': 'Text', 'name': 'eval'},
                {'type': 'Text', 'name': 'translated_text'},
                {'type': 'BinaryEvaluation', 'name': 'eval'},
            ]
        )
        assert str(e.value) == f'Names should be unique. Current names:\n{str(df)}'

    def test_incorrect_annotation_additional_validate(self):
        with pytest.raises(NotImplementedError) as e:
            meta = base.EvaluationMeta(lib.ImageClass, 'choice')
            base.AnnotationFunction(
                inputs=(base.ObjectMeta(objects.Text, 'source_text'),),
                outputs=(base.ObjectMeta(objects.Text, 'translated_text'),),
                evaluation=meta,
            )  # noqa
        assert str(e.value) == f'Unexpected type: "{meta}"'

    def test_incorrect_classification_optional_choice(self):
        with pytest.raises(AssertionError) as e:
            base.ClassificationFunction(
                inputs=(base.ObjectMeta(objects.Text),),
                cls=base.ClassMeta(lib.ImageClass, required=False),
            )
        assert str(e.value) == 'choice is required'


class TestLocalizedString:
    def test_concat(self):
        assert base.LocalizedString({'EN': 'one'}) + base.LocalizedString(
            {'EN': ' two', 'DE': ' zwei'}
        ) == base.LocalizedString({'EN': 'one two', 'DE': 'one zwei'})
        assert base.LocalizedString({'EN': 'one', 'DE': 'einer'}) + base.LocalizedString(
            {'EN': ' two'}
        ) == base.LocalizedString({'EN': 'one two', 'DE': 'einer two'})
        assert base.LocalizedString({'EN': 'one', 'DE': 'einer'}) + '.' == base.LocalizedString(
            {'EN': 'one.', 'DE': 'einer.'}
        )
        assert base.LocalizedString({'DE': 'einer', 'EN': 'one', 'RU': 'один'}) + ', ' + base.LocalizedString(
            {'RU': 'два', 'KK': 'екі', 'EN': 'two'}
        ) + '; ' + base.LocalizedString({'EN': 'three', 'RU': 'три'}) == base.LocalizedString(
            {'EN': 'one, two; three', 'RU': 'один, два; три', 'DE': 'einer, two; three', 'KK': 'one, екі; three'}
        )
        with pytest.raises(AssertionError) as e:
            base.LocalizedString({'DE': 'einer'}) + base.LocalizedString({'EN': ' two'})
        assert str(e.value) == 'no text for EN language'

    def test_task_spec(self):
        dict_task_spec = base.TaskSpec(
            id='id',
            function=None,  # noqa
            name={'EN': 'en_name', 'RU': 'ru_name'},
            description={'EN': 'en_desc', 'RU': 'ru_desc'},
            instruction={'EN': 'en_instruction', 'RU': 'ru_instruction'},
        )

        ls_task_spec = base.TaskSpec(
            id='id',
            function=None,  # noqa
            name=base.LocalizedString({'EN': 'en_name', 'RU': 'ru_name'}),
            description=base.LocalizedString({'EN': 'en_desc', 'RU': 'ru_desc'}),
            instruction=base.LocalizedString({'EN': 'en_instruction', 'RU': 'ru_instruction'}),
        )

        assert dict_task_spec == ls_task_spec

    def test_class(self):
        class Speech(base.Class):
            YES = 'yes'
            NO = 'no'
            OTHER = 'other'

            @classmethod
            def labels(cls) -> Dict['Speech', Dict[str, str]]:
                return {
                    cls.YES: {'EN': 'yes', 'RU': 'да'},
                    cls.NO: {'EN': 'no', 'RU': 'нет'},
                    cls.OTHER: {'EN': 'other', 'RU': 'другое'},
                }

        assert Speech.get_display_labels() == [
            base.LocalizedString({'EN': 'yes', 'RU': 'да'}),
            base.LocalizedString({'EN': 'no', 'RU': 'нет'}),
            base.LocalizedString({'EN': 'other', 'RU': 'другое'}),
        ]


def test_incorrectly_valued_class():
    with pytest.raises(AssertionError) as e:

        class MOS(base.Class):
            ONE = 1
            TWO = 2

        assert str(e.value) == 'only str-valued Classes are accepted'
