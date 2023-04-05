import datetime
import json
import pytest
from typing import Any, Dict, Type

import toloka.client as toloka

from crowdom import (
    base,
    classification,
    classification_loop,
    control,
    evaluation,
    feedback_loop,
    objects,
    lzy,
    worker,
    params,
    pricing,
)


# This should be a unit test, but there is pure_protobuf dependency in Arcadia.


def check(obj: Any, proto_type: Type[lzy.ProtobufSerializer], bytes_expected: bytes):
    bytes_actual = proto_type.serialize(obj).dumps()
    assert bytes_actual == bytes_expected
    assert proto_type.loads(bytes_actual).deserialize() == obj


def test_serialization():
    name = base.LocalizedString({'RU': 'привет', 'EN': 'hello'})
    check(
        name,
        lzy.LocalizedString,
        b'\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello',
    )

    text_format = base.TextFormat.MARKDOWN
    check(text_format, lzy.TextFormat, b'\n\x08markdown')

    label = base.Title(text=name, format=text_format)
    check(
        label,
        lzy.Title,
        b'\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown',
    )

    class Animal(base.Class):
        DOG = 'dog'
        CAT = 'cat'
        OTHER = 'other'

        @classmethod
        def labels(cls) -> Dict['Animal', Dict[str, str]]:
            return {
                cls.DOG: {'EN': 'dog', 'RU': 'собака'},
                cls.CAT: {'EN': 'cat', 'RU': 'кошка'},
                cls.OTHER: {'EN': 'other', 'RU': 'другое'},
            }

    lzy.register_type(Animal, 'Animal')

    dog = Animal.DOG
    check(dog, lzy.Class, b'\n\x03dog\x12\x06Animal')

    sbs_a = base.SbSChoice.A
    check(sbs_a, lzy.SbSChoice, b'\n\x01a')

    true = base.BinaryEvaluation(ok=True)
    check(true, lzy.BinaryEvaluation, b'\x08\x01')

    md = base.Metadata('foo')
    check(md, lzy.Metadata, b'\n\x03foo')

    text = objects.Text('hello')
    check(text, lzy.Text, b'\n\x05hello')

    audio = objects.Audio(url='https://storage.net/1.wav')
    check(audio, lzy.Audio, b'\n\x19https://storage.net/1.wav')

    image = objects.Image(url='https://storage.net/1.jpg')
    check(image, lzy.Image, b'\n\x19https://storage.net/1.jpg')

    video = objects.Video(url='https://storage.net/1.mp4')
    check(video, lzy.Video, b'\n\x19https://storage.net/1.mp4')

    check(dog, lzy.Label, b'\n\r\n\x03dog\x12\x06Animal')

    check(sbs_a, lzy.Label, b'\x12\x03\n\x01a')

    check(true, lzy.Label, b'\x1a\x02\x08\x01')

    check(dog, lzy.Object, b'\n\r\n\x03dog\x12\x06Animal')

    check(sbs_a, lzy.Object, b'\x12\x03\n\x01a')

    check(true, lzy.Object, b'\x1a\x02\x08\x01')

    check(md, lzy.Object, b'"\x05\n\x03foo')

    check(text, lzy.Object, b'*\x07\n\x05hello')

    check(audio, lzy.Object, b'2\x1b\n\x19https://storage.net/1.wav')

    check(image, lzy.Object, b':\x1b\n\x19https://storage.net/1.jpg')

    check(video, lzy.Object, b'B\x1b\n\x19https://storage.net/1.mp4')

    check(video, lzy.OptionalObject, b'\n\x1dB\x1b\n\x19https://storage.net/1.mp4')

    check(None, lzy.OptionalObject, b'')

    objs = (text, None, image)
    check(objs, lzy.Objects, b'\n\x0b\n\t*\x07\n\x05hello\n\x00\n\x1f\n\x1d:\x1b\n\x19https://storage.net/1.jpg')

    objs_empty = tuple()
    check(objs_empty, lzy.Objects, b'')

    objs_2 = (true, dog)
    task_single_solution = (objs, objs_2)
    check(
        task_single_solution,
        lzy.TaskSingleSolution,
        b'\n0\n\x0b\n\t*\x07\n\x05hello\n\x00\n\x1f\n\x1d:\x1b\n\x19https://storage.net/1.jpg\x12\x1b\n\x06\n\x04\x1a\x02\x08\x01\n\x11\n\x0f\n\r\n\x03dog\x12\x06Animal',
    )

    audio_meta = base.ObjectMeta(type=objects.Audio, name='record', title=label, required=False)
    check(
        audio_meta,
        lzy.ObjectMeta,
        b'\n\x05Audio\x12\x06record\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x00',
    )

    video_meta = base.ObjectMeta(type=objects.Video)
    check(video_meta, lzy.ObjectMeta, b'\n\x05Video \x01')

    image_meta = base.ObjectMeta(
        type=objects.Image,
        name='pic',
        title=label,
        required=False,
    )
    check(
        image_meta,
        lzy.ObjectMeta,
        b'\n\x05Image\x12\x03pic\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x00',
    )

    text_validation = objects.TextValidation(
        regex=base.LocalizedString({'RU': '[а-я]+', 'EN': '[a-z]'}),
        hint=base.LocalizedString({'RU': 'только маленькие буквы', 'EN': 'only lowercase letters'}),
    )
    check(
        text_validation,
        lzy.TextValidation,
        b'\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters',
    )

    text_meta = objects.TextMeta(
        type=objects.Text, name='article', format=base.TextFormat.MARKDOWN, validation=text_validation
    )
    check(
        text_meta,
        lzy.TextMeta,
        b'\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters',
    )

    available_labels = base.AvailableLabels([Animal.DOG, Animal.OTHER])
    check(
        available_labels, lzy.AvailableLabels, b'\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal'
    )

    check(
        available_labels, lzy.Consequence, b'\n$\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal'
    )

    condition_equals = base.ConditionEquals(what='cls', to='value')
    check(condition_equals, lzy.ConditionEquals, b'\n\x03cls\x12\x05value')

    check(condition_equals, lzy.Condition, b'\n\x0c\n\x03cls\x12\x05value')

    condition_equals_2 = base.ConditionEquals(what='cls', to='bar')
    condition_equals_3 = base.ConditionEquals(what='cls', to='foo')
    condition_equals_4 = base.ConditionEquals(what='cls', to='baz')
    available_labels_2 = base.AvailableLabels([Animal.DOG])
    available_labels_3 = base.AvailableLabels([Animal.CAT])
    available_labels_4 = base.AvailableLabels([Animal.CAT, Animal.DOG, Animal.OTHER])

    if_ = base.If(
        condition=condition_equals,
        then=base.If(
            condition=condition_equals_2,
            then=base.If(
                condition_equals_3,
                then=available_labels,
                else_=base.If(
                    condition=condition_equals_4,
                    then=available_labels_2,
                ),
            ),
            else_=available_labels_3,
        ),
        else_=base.If(
            condition=condition_equals_3,
            then=available_labels_4,
        ),
    )
    check(
        if_,
        lzy.If,
        b'\n\x0e\n\x0c\n\x03cls\x12\x05value\x12\x80\x01\n\x0c\n\n\n\x03cls\x12\x03bar\x12[\n\x0c\n\n\n\x03cls\x12\x03foo\x1a&\n$\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal"#\n\x0c\n\n\n\x03cls\x12\x03baz\x1a\x13\n\x11\n\x0f\n\r\n\x03dog\x12\x06Animal*\x13\n\x11\n\x0f\n\r\n\x03cat\x12\x06Animal"G\n\x0c\n\n\n\x03cls\x12\x03foo\x1a7\n5\n\x0f\n\r\n\x03cat\x12\x06Animal\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal',
    )

    labels_display_type = base.LabelsDisplayType.MONO
    check(labels_display_type, lzy.LabelsDisplayType, b'\n\x04mono')

    class_meta = base.ClassMeta(
        type=Animal, title=label, available_labels=if_, input_display_type=base.LabelsDisplayType.MONO
    )
    check(
        class_meta,
        lzy.ClassMeta,
        b'\n\x06Animal\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x01\xa2\x06\xdc\x01\n\x0e\n\x0c\n\x03cls\x12\x05value\x12\x80\x01\n\x0c\n\n\n\x03cls\x12\x03bar\x12[\n\x0c\n\n\n\x03cls\x12\x03foo\x1a&\n$\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal"#\n\x0c\n\n\n\x03cls\x12\x03baz\x1a\x13\n\x11\n\x0f\n\r\n\x03dog\x12\x06Animal*\x13\n\x11\n\x0f\n\r\n\x03cat\x12\x06Animal"G\n\x0c\n\n\n\x03cls\x12\x03foo\x1a7\n5\n\x0f\n\r\n\x03cat\x12\x06Animal\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal\xaa\x06\x06\n\x04mono\xb2\x06\x07\n\x05plain',
    )

    check(
        audio_meta,
        lzy.ObjectMetaT,
        b'\nB\n\x05Audio\x12\x06record\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x00',
    )

    check(
        text_meta,
        lzy.ObjectMetaT,
        b'\x1a\x92\x01\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters',
    )

    check(
        class_meta,
        lzy.ObjectMetaT,
        b'\x12\xae\x02\n\x06Animal\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x01\xa2\x06\xdc\x01\n\x0e\n\x0c\n\x03cls\x12\x05value\x12\x80\x01\n\x0c\n\n\n\x03cls\x12\x03bar\x12[\n\x0c\n\n\n\x03cls\x12\x03foo\x1a&\n$\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal"#\n\x0c\n\n\n\x03cls\x12\x03baz\x1a\x13\n\x11\n\x0f\n\r\n\x03dog\x12\x06Animal*\x13\n\x11\n\x0f\n\r\n\x03cat\x12\x06Animal"G\n\x0c\n\n\n\x03cls\x12\x03foo\x1a7\n5\n\x0f\n\r\n\x03cat\x12\x06Animal\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal\xaa\x06\x06\n\x04mono\xb2\x06\x07\n\x05plain',
    )

    function_argument_type = objects.Video
    check(function_argument_type, lzy.FunctionArgument, b'\n\x05Video')

    function_argument_meta = text_meta
    check(
        function_argument_meta,
        lzy.FunctionArgument,
        b'\x12\x95\x01\x1a\x92\x01\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters',
    )

    classification_function = base.ClassificationFunction(inputs=(objects.Image,), cls=Animal)
    check(classification_function, lzy.ClassificationFunction, b'\n\x07\n\x05Image\x12\x08\n\x06Animal')

    sbs_function_1 = base.SbSFunction(
        inputs=(audio_meta, text_meta),
        hints=(base.ObjectMeta(type=objects.Video, name='tape'),),
    )
    check(
        sbs_function_1,
        lzy.SbSFunction,
        b'\nF\x12D\nB\n\x05Audio\x12\x06record\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x00\n\x98\x01\x12\x95\x01\x1a\x92\x01\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters\x12\x13\x12\x11\n\x0f\n\x05Video\x12\x04tape \x01\x1a\x0b\n\tSbSChoice',
    )

    sbs_function_2 = base.SbSFunction(inputs=(objects.Audio,))
    check(sbs_function_2, lzy.SbSFunction, b'\n\x07\n\x05Audio\x1a\x0b\n\tSbSChoice')

    class_meta.name = 'type'  # to pass none-or-all name validation
    annotation_function = base.AnnotationFunction(
        inputs=(
            text_meta,
            base.ObjectMeta(
                type=objects.Image,
                name='photo',
                required=False,
            ),
        ),
        outputs=(
            class_meta,
            base.ObjectMeta(
                type=objects.Audio,
                name='record',
            ),
        ),
    )
    check(
        annotation_function,
        lzy.AnnotationFunction,
        b'\n\x98\x01\x12\x95\x01\x1a\x92\x01\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters\n\x14\x12\x12\n\x10\n\x05Image\x12\x05photo \x00\x12\xba\x02\x12\xb7\x02\x12\xb4\x02\n\x06Animal\x12\x04type\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x01\xa2\x06\xdc\x01\n\x0e\n\x0c\n\x03cls\x12\x05value\x12\x80\x01\n\x0c\n\n\n\x03cls\x12\x03bar\x12[\n\x0c\n\n\n\x03cls\x12\x03foo\x1a&\n$\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal"#\n\x0c\n\n\n\x03cls\x12\x03baz\x1a\x13\n\x11\n\x0f\n\r\n\x03dog\x12\x06Animal*\x13\n\x11\n\x0f\n\r\n\x03cat\x12\x06Animal"G\n\x0c\n\n\n\x03cls\x12\x03foo\x1a7\n5\n\x0f\n\r\n\x03cat\x12\x06Animal\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal\xaa\x06\x06\n\x04mono\xb2\x06\x07\n\x05plain\x12\x15\x12\x13\n\x11\n\x05Audio\x12\x06record \x01\x1a\x12\n\x10BinaryEvaluation',
    )

    check(classification_function, lzy.TaskFunction, b'\n\x13\n\x07\n\x05Image\x12\x08\n\x06Animal')

    check(
        sbs_function_1,
        lzy.TaskFunction,
        b'\x12\x85\x02\nF\x12D\nB\n\x05Audio\x12\x06record\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x00\n\x98\x01\x12\x95\x01\x1a\x92\x01\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters\x12\x13\x12\x11\n\x0f\n\x05Video\x12\x04tape \x01\x1a\x0b\n\tSbSChoice',
    )

    check(
        annotation_function,
        lzy.TaskFunction,
        b'\x1a\x99\x04\n\x98\x01\x12\x95\x01\x1a\x92\x01\n\x04Text\x12\x07article \x01\xa2\x06\n\n\x08markdown\xaa\x06q\n\x1d\n\x0e\n\x02RU\x12\x08[\xd0\xb0-\xd1\x8f]+\n\x0b\n\x02EN\x12\x05[a-z]\x12P\n0\n\x02RU\x12*\xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb5\xd0\xbd\xd1\x8c\xd0\xba\xd0\xb8\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xba\xd0\xb2\xd1\x8b\n\x1c\n\x02EN\x12\x16only lowercase letters\n\x14\x12\x12\n\x10\n\x05Image\x12\x05photo \x00\x12\xba\x02\x12\xb7\x02\x12\xb4\x02\n\x06Animal\x12\x04type\x1a/\n!\n\x12\n\x02RU\x12\x0c\xd0\xbf\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82\n\x0b\n\x02EN\x12\x05hello\x12\n\n\x08markdown \x01\xa2\x06\xdc\x01\n\x0e\n\x0c\n\x03cls\x12\x05value\x12\x80\x01\n\x0c\n\n\n\x03cls\x12\x03bar\x12[\n\x0c\n\n\n\x03cls\x12\x03foo\x1a&\n$\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal"#\n\x0c\n\n\n\x03cls\x12\x03baz\x1a\x13\n\x11\n\x0f\n\r\n\x03dog\x12\x06Animal*\x13\n\x11\n\x0f\n\r\n\x03cat\x12\x06Animal"G\n\x0c\n\n\n\x03cls\x12\x03foo\x1a7\n5\n\x0f\n\r\n\x03cat\x12\x06Animal\n\x0f\n\r\n\x03dog\x12\x06Animal\n\x11\n\x0f\n\x05other\x12\x06Animal\xaa\x06\x06\n\x04mono\xb2\x06\x07\n\x05plain\x12\x15\x12\x13\n\x11\n\x05Audio\x12\x06record \x01\x1a\x12\n\x10BinaryEvaluation',
    )

    task_spec = base.TaskSpec(
        id='my-task',
        function=classification_function,
        name={'EN': 'Cat or dog', 'RU': 'Кошка или собака'},
        description={'EN': 'Identification of animals in photos', 'RU': 'Определение животных на изображениях'},
        instruction={
            'EN': 'Identify the animal in the photo',
            'RU': 'Определите, какое животное на фотографии',
        },
    )
    check(
        task_spec,
        lzy.TaskSpec,
        b'\n\x07my-task\x12\x15\n\x13\n\x07\n\x05Image\x12\x08\n\x06Animal\x1a8\n\x10\n\x02EN\x12\nCat or dog\n$\n\x02RU\x12\x1e\xd0\x9a\xd0\xbe\xd1\x88\xd0\xba\xd0\xb0 \xd0\xb8\xd0\xbb\xd0\xb8 \xd1\x81\xd0\xbe\xd0\xb1\xd0\xb0\xd0\xba\xd0\xb0"x\n)\n\x02EN\x12#Identification of animals in photos\nK\n\x02RU\x12E\xd0\x9e\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xbb\xd0\xb5\xd0\xbd\xd0\xb8\xd0\xb5 \xd0\xb6\xd0\xb8\xd0\xb2\xd0\xbe\xd1\x82\xd0\xbd\xd1\x8b\xd1\x85 \xd0\xbd\xd0\xb0 \xd0\xb8\xd0\xb7\xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd0\xb6\xd0\xb5\xd0\xbd\xd0\xb8\xd1\x8f\xd1\x85*{\n&\n\x02EN\x12 Identify the animal in the photo\nQ\n\x02RU\x12K\xd0\x9e\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xbb\xd0\xb8\xd1\x82\xd0\xb5, \xd0\xba\xd0\xb0\xd0\xba\xd0\xbe\xd0\xb5 \xd0\xb6\xd0\xb8\xd0\xb2\xd0\xbe\xd1\x82\xd0\xbd\xd0\xbe\xd0\xb5 \xd0\xbd\xd0\xb0 \xd1\x84\xd0\xbe\xd1\x82\xd0\xbe\xd0\xb3\xd1\x80\xd0\xb0\xd1\x84\xd0\xb8\xd0\xb8',
    )

    comparison_type = control.ComparisonType.LESS_OR_EQUAL
    check(comparison_type, lzy.ComparisonType, b'\n\x02<=')

    predicate_value_float = 1.0
    check(predicate_value_float, lzy.PredicateValue, b'\r\x00\x00\x80?')

    predicate_value_timedelta = datetime.timedelta(hours=2, minutes=10, seconds=30)
    check(predicate_value_timedelta, lzy.PredicateValue, b'\x12\x05\x08\x96=\x10\x00')

    assignment_accuracy_predicate = control.AssignmentAccuracyPredicate(
        threshold=0.5,
        comparison=control.ComparisonType.GREATER,
    )
    check(assignment_accuracy_predicate, lzy.Predicate, b'\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01>\x18\x00')

    assignment_duration_predicate = control.AssignmentDurationPredicate(
        threshold=datetime.timedelta(minutes=1),
        comparison=control.ComparisonType.LESS_OR_EQUAL,
    )
    check(assignment_duration_predicate, lzy.Predicate, b'\x12\x0e\n\x06\x12\x04\x08<\x10\x00\x12\x04\n\x02<=\x18\x00')

    always_true_predicate = control.AlwaysTruePredicate()
    check(always_true_predicate, lzy.Predicate, b'\x18\x01')

    assignment_accuracy_predicate_2 = control.AssignmentAccuracyPredicate(
        threshold=0.5,
        comparison=control.ComparisonType.LESS,
    )
    predicate_expression = control.PredicateExpression(
        boolean_operator=control.BooleanOperator.OR,
        predicates=[
            assignment_accuracy_predicate,
            assignment_accuracy_predicate_2,
        ],
    )
    check(
        predicate_expression,
        lzy.Predicate,
        b'\x18\x00"\x04\n\x02or*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01>\x18\x00*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00',
    )

    block_user_1 = control.BlockUser(
        scope=toloka.user_restriction.UserRestriction.Scope.POOL,
        private_comment='too fast',
    )
    check(
        block_user_1,
        lzy.BlockUser,
        b'\n\x04POOL\x12\x08too fast',
    )

    block_user_2 = control.BlockUser(
        scope=toloka.user_restriction.UserRestriction.Scope.PROJECT,
        private_comment='',
        duration=datetime.timedelta(hours=4),
    )
    check(
        block_user_2,
        lzy.BlockUser,
        b'\n\x07PROJECT\x12\x00\x1a\x05\x08\xc0p\x10\x00',
    )

    give_bonus_to_user = control.GiveBonusToUser(amount_usd=1.0)
    check(give_bonus_to_user, lzy.GiveBonusToUser, b'\r\x00\x00\x80?')

    set_assignment_status = control.SetAssignmentStatus(status=toloka.Assignment.Status.REJECTED)
    check(set_assignment_status, lzy.SetAssignmentStatus, b'\n\x08REJECTED')

    check(block_user_2, lzy.Action, b'\n\x12\n\x07PROJECT\x12\x00\x1a\x05\x08\xc0p\x10\x00')

    check(give_bonus_to_user, lzy.Action, b'\x12\x05\r\x00\x00\x80?')

    check(set_assignment_status, lzy.Action, b'\x1a\n\n\x08REJECTED')

    rule_1 = control.Rule(predicate=assignment_accuracy_predicate_2, action=block_user_1)
    check(
        rule_1,
        lzy.Rule,
        b'\n\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00\x12\x12\n\x10\n\x04POOL\x12\x08too fast',
    )

    rule_2 = control.Rule(predicate=predicate_expression, action=give_bonus_to_user)
    check(
        rule_2,
        lzy.Rule,
        b'\n,\x18\x00"\x04\n\x02or*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01>\x18\x00*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00\x12\x07\x12\x05\r\x00\x00\x80?',
    )

    ctrl = control.Control(rules=[rule_1, rule_2])
    check(
        ctrl,
        lzy.Control,
        b'\n&\n\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00\x12\x12\n\x10\n\x04POOL\x12\x08too fast\n7\n,\x18\x00"\x04\n\x02or*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01>\x18\x00*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00\x12\x07\x12\x05\r\x00\x00\x80?',
    )

    ctrl_empty = control.Control(rules=[])
    check(ctrl_empty, lzy.Control, b'')

    with open('pool.json') as f:
        pool = toloka.Pool.structure(json.load(f))
    check(
        pool,
        lzy.TolokaPool,
        b'\n\x9a"{"project_id": "121693", "private_name": "check pool", "may_contain_adult_content": true, "reward_per_assignment": 0.03, "assignment_max_duration_seconds": 900, "defaults": {"default_overlap_for_new_task_suites": 1, "default_overlap_for_new_tasks": 1}, "will_expire": "2022-10-13T09:30:42.574000", "auto_close_after_complete_delay_seconds": 0, "auto_accept_solutions": false, "auto_accept_period_day": 14, "assignments_issuing_config": {"issue_task_suites_in_creation_order": false}, "priority": 30, "filter": {"and": [{"or": [{"operator": "LT", "value": 1095064242, "key": "date_of_birth", "category": "profile"}]}, {"and": [{"operator": "IN", "value": "RU", "key": "languages", "category": "profile"}, {"or": [{"operator": "IN", "value": 225, "key": "region_by_phone", "category": "computed"}, {"operator": "IN", "value": 187, "key": "region_by_phone", "category": "computed"}, {"operator": "IN", "value": 149, "key": "region_by_phone", "category": "computed"}]}, {"or": [{"operator": "EQ", "value": "BROWSER", "key": "client_type", "category": "computed"}, {"operator": "EQ", "value": "TOLOKA_APP", "key": "client_type", "category": "computed"}]}]}]}, "quality_control": {"captcha_frequency": "LOW", "configs": [{"rules": [{"action": {"parameters": {"scope": "PROJECT", "duration": 8, "duration_unit": "HOURS", "private_comment": "Captcha"}, "type": "RESTRICTION_V2"}, "conditions": [{"operator": "GTE", "value": 5, "key": "stored_results_count"}, {"operator": "LTE", "value": 30.0, "key": "success_rate"}]}], "collector_config": {"uuid": "310db6f7-3e61-441f-9498-c10bfa6a6403", "parameters": {"history_size": 10}, "type": "CAPTCHA"}}, {"rules": [{"action": {"parameters": {"scope": "PROJECT", "duration": 8, "duration_unit": "HOURS", "private_comment": "Skipped assignments"}, "type": "RESTRICTION_V2"}, "conditions": [{"operator": "GTE", "value": 5, "key": "skipped_in_row_count"}]}], "collector_config": {"uuid": "0ba5999e-da0b-436b-9183-4be838419a7d", "type": "SKIPPED_IN_ROW_ASSIGNMENTS"}}, {"rules": [{"action": {"parameters": {"scope": "PROJECT", "duration": 1440, "duration_unit": "MINUTES", "private_comment": "Fast submits, <= 0.01"}, "type": "RESTRICTION_V2"}, "conditions": [{"operator": "GTE", "value": 1, "key": "total_submitted_count"}, {"operator": "GTE", "value": 1, "key": "fast_submitted_count"}]}], "collector_config": {"uuid": "9190e075-0245-458a-b2ea-a9ca474736ac", "parameters": {"fast_submit_threshold_seconds": 1, "history_size": 10}, "type": "ASSIGNMENT_SUBMIT_TIME"}}, {"rules": [{"action": {"parameters": {"scope": "PROJECT", "duration": 120, "duration_unit": "MINUTES", "private_comment": "Fast submits, 0.01 < time <= 0.05"}, "type": "RESTRICTION_V2"}, "conditions": [{"operator": "GTE", "value": 1, "key": "total_submitted_count"}, {"operator": "GTE", "value": 1, "key": "fast_submitted_count"}]}], "collector_config": {"uuid": "7cb9eee9-7201-4043-ad7f-3eb6ecd7833c", "parameters": {"fast_submit_threshold_seconds": 9, "history_size": 10}, "type": "ASSIGNMENT_SUBMIT_TIME"}}, {"rules": [{"action": {"parameters": {"scope": "PROJECT", "duration": 60, "duration_unit": "MINUTES", "private_comment": "Control tasks: [0, 1) done correctly"}, "type": "RESTRICTION_V2"}, "conditions": [{"operator": "GTE", "value": 1, "key": "total_answers_count"}, {"operator": "GTE", "value": 0.0, "key": "correct_answers_rate"}, {"operator": "LT", "value": 100.0, "key": "correct_answers_rate"}]}], "collector_config": {"uuid": "ad95564f-fa6c-43af-afca-db5ec4cbf120", "parameters": {"history_size": 1}, "type": "GOLDEN_SET"}}, {"rules": [{"action": {"parameters": {"scope": "PROJECT", "duration": 5, "duration_unit": "HOURS", "private_comment": "Completed many assignments, vacation"}, "type": "RESTRICTION_V2"}, "conditions": [{"operator": "GTE", "value": 20, "key": "assignments_accepted_count"}]}], "collector_config": {"uuid": "abf380be-7a84-4124-9d0d-316267a7c649", "type": "ANSWER_COUNT"}}]}, "speed_quality_balance": {"percent": 90, "type": "TOP_PERCENTAGE_BY_QUALITY"}, "mixer_config": {"real_tasks_count": 8, "golden_tasks_count": 1, "training_tasks_count": 0}, "owner": {"id": "0ba8b02169300a7318c04a2d1544f8cf", "myself": true}, "id": "1286059", "status": "ARCHIVED", "last_close_reason": "COMPLETED", "created": "2022-09-13T09:30:42.608000", "last_started": "2022-09-13T09:36:02.632000", "last_stopped": "2022-09-13T09:38:00.090000", "type": "REGULAR"}',
    )

    filter_condition = (
        (toloka.filter.DateOfBirth > int(datetime.datetime(1940, 11, 5).timestamp()))
        & (toloka.filter.ClientType == toloka.filter.ClientType.ClientType.BROWSER)
    ) | (
        toloka.filter.Languages.in_('EN', verified=True)
        & (toloka.filter.RegionByPhone.in_(204) | toloka.filter.RegionByPhone.in_(983))
        & (toloka.filter.DateOfBirth < int(datetime.datetime(1996, 11, 5).timestamp()))
        & (toloka.filter.DateOfBirth > int(datetime.datetime(1980, 11, 5).timestamp()))
    )
    check(
        filter_condition,
        lzy.TolokaFilterCondition,
        b'\n\xd6\x05{"or": [{"and": [{"operator": "GT", "value": -920084400, "key": "date_of_birth", "category": "profile"}, {"operator": "EQ", "value": "BROWSER", "key": "client_type", "category": "computed"}]}, {"and": [{"or": [{"and": [{"operator": "IN", "value": "EN", "key": "languages", "category": "profile"}, {"key": "26366", "operator": "EQ", "value": 100, "category": "skill"}]}]}, {"or": [{"operator": "IN", "value": 204, "key": "region_by_phone", "category": "computed"}, {"operator": "IN", "value": 983, "key": "region_by_phone", "category": "computed"}]}, {"operator": "LT", "value": 847141200, "key": "date_of_birth", "category": "profile"}, {"operator": "GT", "value": 342219600, "key": "date_of_birth", "category": "profile"}]}]}',
    )

    skill = toloka.Skill(id='123')
    check(skill, lzy.TolokaSkill, b'\n\r{"id": "123"}')

    with open('project.json') as f:
        project = toloka.Project.structure(json.load(f))
    check(
        project,
        lzy.TolokaProject,
        b'\n\x8bN{"owner": {"id": "0ba8b02169300a7318c04a2d1544f8cf", "myself": true}, "public_name": "Cat or dog", "public_description": "Identification of animals in photos", "task_spec": {"input_spec": {"id": {"required": true, "hidden": true, "type": "string"}, "image": {"required": true, "hidden": false, "type": "url"}}, "output_spec": {"choice": {"required": true, "hidden": false, "allowed_values": ["cat", "dog", "other"], "type": "string"}}, "view_spec": {"inputExample": null, "localizationConfig": null, "config": "{\\n    \\"view\\": {\\n        \\"items\\": [\\n            {\\n                \\"url\\": {\\n                    \\"path\\": \\"image\\",\\n                    \\"type\\": \\"data.input\\"\\n                },\\n                \\"type\\": \\"view.image\\"\\n            },\\n            {\\n                \\"data\\": {\\n                    \\"path\\": \\"choice\\",\\n                    \\"type\\": \\"data.output\\"\\n                },\\n                \\"options\\": [\\n                    {\\n                        \\"value\\": \\"dog\\",\\n                        \\"label\\": \\"dog\\"\\n                    },\\n                    {\\n                        \\"value\\": \\"cat\\",\\n                        \\"label\\": \\"cat\\"\\n                    },\\n                    {\\n                        \\"value\\": \\"other\\",\\n                        \\"label\\": \\"other\\"\\n                    }\\n                ],\\n                \\"disabled\\": false,\\n                \\"validation\\": {\\n                    \\"data\\": {\\n                        \\"path\\": \\"choice\\",\\n                        \\"type\\": \\"data.output\\"\\n                    },\\n                    \\"hint\\": \\"Choose one of the options\\",\\n                    \\"type\\": \\"condition.required\\"\\n                },\\n                \\"type\\": \\"field.radio-group\\"\\n            }\\n        ],\\n        \\"type\\": \\"view.list\\"\\n    },\\n    \\"plugins\\": [\\n        {\\n            \\"1\\": {\\n                \\"data\\": {\\n                    \\"path\\": \\"choice\\",\\n                    \\"type\\": \\"data.output\\"\\n                },\\n                \\"payload\\": \\"dog\\",\\n                \\"type\\": \\"action.set\\"\\n            },\\n            \\"type\\": \\"plugin.hotkeys\\"\\n        },\\n        {\\n            \\"2\\": {\\n                \\"data\\": {\\n                    \\"path\\": \\"choice\\",\\n                    \\"type\\": \\"data.output\\"\\n                },\\n                \\"payload\\": \\"cat\\",\\n                \\"type\\": \\"action.set\\"\\n            },\\n            \\"type\\": \\"plugin.hotkeys\\"\\n        },\\n        {\\n            \\"3\\": {\\n                \\"data\\": {\\n                    \\"path\\": \\"choice\\",\\n                    \\"type\\": \\"data.output\\"\\n                },\\n                \\"payload\\": \\"other\\",\\n                \\"type\\": \\"action.set\\"\\n            },\\n            \\"type\\": \\"plugin.hotkeys\\"\\n        },\\n        {\\n            \\"layout\\": {\\n                \\"kind\\": \\"scroll\\",\\n                \\"taskWidth\\": 700.0\\n            },\\n            \\"notifications\\": [\\n                {\\n                    \\"content\\": \\"Before performing a task, make sure that all media elements have loaded.\\",\\n                    \\"type\\": \\"view.text\\"\\n                },\\n                {\\n                    \\"content\\": \\"If at least one media element is missing, reload the page.\\",\\n                    \\"type\\": \\"view.text\\"\\n                }\\n            ],\\n            \\"type\\": \\"plugin.toloka\\"\\n        }\\n    ]\\n}", "inferDataSpec": false, "type": "tb", "lock": {"core": "1.0.0", "view.image": "1.0.0", "condition.required": "1.0.0", "field.radio-group": "1.0.0", "view.list": "1.0.0", "action.set": "1.0.0", "plugin.hotkeys": "1.0.0", "view.text": "1.0.0", "plugin.toloka": "1.0.0"}}}, "assignments_issuing_type": "AUTOMATED", "assignments_automerge_enabled": false, "status": "ACTIVE", "created": "2022-02-24T12:21:08.090000", "id": "98756", "public_instructions": "<style>\\n body {\\n        scroll-behavior: smooth;\\n    }\\n\\n    h2, h3, h4 {\\n        font-weight: inherit;\\n        font-style: four;\\n        text-align: left;\\n        text-transform: none;\\n        margin: 20px 0 10px 0;\\n    }\\n\\n    p {\\n        font-size: 14px;\\n        align: left;\\n        color: #000000;\\n        margin: 2px 0;\\n        padding-right: 10px;\\n    }\\n\\n    ul, ol {\\n        padding-left: 15px;\\n        margin-left: 25px;\\n    }\\n\\n    li {\\n        font-size: 14px;\\n        align: left;\\n        color: #000000;\\n        margin: 2px 0;\\n        padding-right: 10px;\\n    }\\n\\n    .hide {\\n        display: none\\n    }\\n\\n    .hide + label ~ div {\\n        display: none\\n    }\\n\\n    .hide + label ~ p {\\n        display: none\\n    }\\n\\n    .hide + label {\\n        border-bottom: 1px dotted blue;\\n        padding: 0;\\n        margin: 0;\\n        cursor: pointer;\\n        display: inline-block;\\n        color: blue;\\n        font-size: 14px;\\n    }\\n\\n    .hide:checked + label {\\n        border-bottom: 0;\\n        color: green;\\n        padding-right: 10px;\\n        margin: 0;\\n        font-size: 14px;\\n    }\\n\\n    .hide:checked + label + div {\\n        display: block;\\n    }\\n\\n    .hide:checked + label + span {\\n        display: block;\\n    }\\n\\n    .hide:checked + label + p {\\n        display: block;\\n    }\\n\\n    img {\\n        width: 100%;\\n        max-width: 600px;\\n    }\\n</style>\\n<div>\\n <p>\\n  Look at photo and choose one of the options:\\n </p>\\n <ul><li>\\n   <strong>\\n    dog\\n   </strong>\\n   \\u2013 if dog is on the photo\\n  </li><li>\\n   <strong>\\n    cat\\n   </strong>\\n   \\u2013 if cat is on the photo\\n  </li><li>\\n   <strong>\\n    other\\n   </strong>\\n   \\u2013 if there is another animal in the photo, several animals, or no animals at all\\n  </li></ul>\\n</div>\\n<div>\\n <input class=\\"hide\\" id=\\"hd-1\\" type=\\"checkbox\\" />\\n <label for=\\"hd-1\\">\\n  <strong>\\n   Click to learn the information about solution verification\\n  </strong>\\n </label>\\n <div>\\n  <p>\\n   Several randomly selected tasks from the page are sent for verification. If the percentage of incorrectly\\n            performed tasks is more than the maximum allowed, then the task page is rejected, and numbers of\\n            incorrectly performed tasks are written in the message. Alternatively, your assignment will be evaluated\\n            as a whole and rejected, if general accuracy is below allowed.\\n  </p>\\n  <p>\\n   The tasks are numbered in order on the tasks page, starting from 1.\\n  </p>\\n  <div>\\n   <input class=\\"hide\\" id=\\"hd-2\\" type=\\"checkbox\\" />\\n   <label for=\\"hd-2\\">\\n    <strong>\\n     Task number example\\n    </strong>\\n   </label>\\n   <div>\\n    <img alt=\\"Task number\\" src=\\"https://storage.yandexcloud.net/crowdom-public/instructions/task-number.jpg\\" />\\n   </div>\\n  </div>\\n  <p>\\n   If you do not agree with the rejection of the task page, file an appeal by writing a message in the following\\n            format:\\n  </p>\\n  <ul><li>\\n    In the first line \\u2013 the word &#34;Appeal&#34;\\n   </li><li>\\n    In the second line \\u2013 the number of the task page\\n   </li><li>\\n    In the third line \\u2013 the numbers of incorrectly performed tasks that you consider to have been performed\\n                correctly\\n   </li><li>\\n    Starting from the fourth line, you can comment on specific tasks or the task page as a whole.\\n   </li></ul>\\n  <div>\\n   <input class=\\"hide\\" id=\\"hd-3\\" type=\\"checkbox\\" />\\n   <label for=\\"hd-3\\">\\n    <strong>\\n     Example when working from the browser\\n    </strong>\\n   </label>\\n   <div>\\n    <p>\\n     After checking the &#34;Profile &gt; History&#34; section, you will see a similar entry:\\n    </p>\\n    <img alt=\\"Rejection message\\" src=\\"https://storage.yandexcloud.net/crowdom-public/instructions/en/rejection-message_browser.png\\" />\\n    <p>\\n     Green is the number of the\\n     <strong>\\n      task page\\n     </strong>\\n     , blue is the number of incorrectly performed\\n     <strong>\\n      tasks\\n     </strong>\\n     .\\n    </p>\\n    <p>\\n     Let&#39;s say you think that you have correctly performed tasks 6 and 9. Then send a message in the\\n                    following format:\\n    </p>\\n    <img alt=\\"Appeal message\\" src=\\"https://storage.yandexcloud.net/crowdom-public/instructions/en/appeal-message_browser.png\\" />\\n    <p>\\n     If it is possible to specify a topic when writing a message, write &#34;Appeal&#34;.\\n    </p>\\n   </div>\\n  </div>\\n  <div>\\n   <input class=\\"hide\\" id=\\"hd-4\\" type=\\"checkbox\\" />\\n   <label for=\\"hd-4\\">\\n    <strong>\\n     Example when working from a mobile app\\n    </strong>\\n   </label>\\n   <div>\\n    <p>\\n     After checking the &#34;My Tasks&#34; section, you will see a card like this in the list:\\n    </p>\\n    <img alt=\\"Completed tasks\\" src=\\"https://storage.yandexcloud.net/crowdom-public/instructions/en/completed-tasks_app.png\\" />\\n    <p>\\n     Click on the card. On the task screen, the numbers of incorrectly performed tasks are outlined in blue.\\n    </p>\\n    <img alt=\\"Rejection message\\" src=\\"https://storage.yandexcloud.net/crowdom-public/instructions/en/rejection-message_app.png\\" />\\n    <p>\\n     Let&#39;s say you think that you have correctly performed tasks 5 and 9. Copy the task page number by\\n                    clicking on &#34;Copy ID&#34; (outlined in green), click on &#34;Write to the customer&#34; (outlined in purple).\\n                    Send the message is in the following format:\\n    </p>\\n    <img alt=\\"Appeal message\\" src=\\"https://storage.yandexcloud.net/crowdom-public/instructions/en/appeal-message_app.png\\" />\\n   </div>\\n  </div>\\n  <p>\\n   If your assignment was evaluated as a whole, you will see a message\\n            &#34;Too few correct solutions&#34;. If you do not agree with the page rejection,\\n            file an appeal by writing a message in the format described above. Specify the numbers of tasks you\\n            think you have done correctly.\\n  </p>\\n </div>\\n</div>\\n", "private_comment": "dogs-and-cats_EN"}',
    )

    with open('assignments.json') as f:
        assignments = [toloka.Assignment.structure(a) for a in json.load(f)]
    check(
        assignments[0],
        lzy.TolokaAssignment,
        b'\n\xe0\x0b{"id": "000011c83d--626ab04adbe4e9761d7b5613", "task_suite_id": "000011c83d--626ab04adbe4e9761d7b5611", "pool_id": "1165373", "user_id": "f87548bd9c317ed987e22c8ebe3dea3c", "status": "ACCEPTED", "reward": 1.0, "tasks": [{"input_values": {"image": "https://tlk.s3.yandex.net/dataset/cats_vs_dogs/dogs/c24f504ea1d941808d7cd0ef46b926fc.jpg", "id": "Image(url=\'https://tlk.s3.yandex.net/dataset/cats_vs_dogs/dogs/c24f504ea1d941808d7cd0ef46b926fc.jpg\')"}, "id": "000011c83d--626aafee3e1f6f02bc867ea1", "infinite_overlap": false, "overlap": 1, "pool_id": "1165373", "remaining_overlap": 0, "reserved_for": [], "unavailable_for": [], "created": "2022-04-28T15:17:02.924000"}, {"input_values": {"image": "https://tlk.s3.yandex.net/dataset/cats_vs_dogs/dogs/64513c280688475189471aa563f58f90.jpg", "id": "Image(url=\'https://tlk.s3.yandex.net/dataset/cats_vs_dogs/dogs/64513c280688475189471aa563f58f90.jpg\')"}, "known_solutions": [{"output_values": {"choice": "dog"}, "correctness_weight": 1.0}], "id": "000011c83d--626aafeb3e1f6f02bc867e85", "infinite_overlap": true, "pool_id": "1165373", "reserved_for": [], "unavailable_for": [], "created": "2022-04-28T15:16:59.695000", "overlap": null}], "automerged": false, "created": "2022-04-28T15:18:34.993000", "submitted": "2022-04-28T15:18:42.918000", "accepted": "2022-04-28T15:22:05.774000", "solutions": [{"output_values": {"choice": "dog"}}, {"output_values": {"choice": "dog"}}], "mixed": true, "owner": {"id": "0ba8b02169300a7318c04a2d1544f8cf", "myself": true}}',
    )

    skill_2 = toloka.Skill(id='777')
    expert_filter = worker.ExpertFilter(skills=[skill, skill_2])
    check(expert_filter, lzy.ExpertFilter, b'\n\x0f\n\r{"id": "123"}\n\x0f\n\r{"id": "777"}')

    language_requirement = worker.LanguageRequirement(lang='DE', verified=False)
    check(language_requirement, lzy.LanguageRequirement, b'\n\x02DE\x10\x00')

    worker_filter_params_1 = worker.WorkerFilter.Params(
        langs={worker.LanguageRequirement(lang='EN', verified=True), worker.LanguageRequirement(lang='IT')},
        regions={worker.RegionCodes.TURKEY, worker.RegionCodes.SPAIN},
        age_range=(24, 40),
    )
    check(
        worker_filter_params_1,
        lzy.WorkerFilterParams,
        b'\n\x06\n\x02EN\x10\x01\n\x06\n\x02IT\x10\x00\x12\x04\x98\x03\xae\x0f\x180 P',
    )

    worker_filter_params_2 = worker.WorkerFilter.Params(
        langs={language_requirement},
    )
    check(worker_filter_params_2, lzy.WorkerFilterParams, b'\n\x06\n\x02DE\x10\x00\x12\x00\x18$')

    worker_filter_empty = worker.WorkerFilter(filters=[], training_score=None)
    check(worker_filter_empty, lzy.WorkerFilter, b'')

    worker_filter = worker.WorkerFilter(training_score=50, filters=[worker_filter_params_1, worker_filter_params_2])
    check(
        worker_filter,
        lzy.WorkerFilter,
        b'\x08d\xa2\x06\x1a\n\x06\n\x02EN\x10\x01\n\x06\n\x02IT\x10\x00\x12\x04\x98\x03\xae\x0f\x180 P\xa2\x06\x0c\n\x06\n\x02DE\x10\x00\x12\x00\x18$',
    )

    custom_filter_empty = worker.CustomWorkerFilter(filter=None, training_score=None)
    check(custom_filter_empty, lzy.CustomWorkerFilter, b'')

    custom_worker_filter = worker.CustomWorkerFilter(filter=filter_condition, training_score=None)
    check(
        custom_worker_filter,
        lzy.CustomWorkerFilter,
        b'\xa2\x06\xd9\x05\n\xd6\x05{"or": [{"and": [{"operator": "GT", "value": -920084400, "key": "date_of_birth", "category": "profile"}, {"operator": "EQ", "value": "BROWSER", "key": "client_type", "category": "computed"}]}, {"and": [{"or": [{"and": [{"operator": "IN", "value": "EN", "key": "languages", "category": "profile"}, {"key": "26366", "operator": "EQ", "value": 100, "category": "skill"}]}]}, {"or": [{"operator": "IN", "value": 204, "key": "region_by_phone", "category": "computed"}, {"operator": "IN", "value": 983, "key": "region_by_phone", "category": "computed"}]}, {"operator": "LT", "value": 847141200, "key": "date_of_birth", "category": "profile"}, {"operator": "GT", "value": 342219600, "key": "date_of_birth", "category": "profile"}]}]}',
    )

    check(expert_filter, lzy.HumanFilter, b'\n"\n\x0f\n\r{"id": "123"}\n\x0f\n\r{"id": "777"}')

    check(
        worker_filter,
        lzy.HumanFilter,
        b'\x12.\x08d\xa2\x06\x1a\n\x06\n\x02EN\x10\x01\n\x06\n\x02IT\x10\x00\x12\x04\x98\x03\xae\x0f\x180 P\xa2\x06\x0c\n\x06\n\x02DE\x10\x00\x12\x00\x18$',
    )

    check(
        custom_worker_filter,
        lzy.HumanFilter,
        b'\x1a\xdd\x05\xa2\x06\xd9\x05\n\xd6\x05{"or": [{"and": [{"operator": "GT", "value": -920084400, "key": "date_of_birth", "category": "profile"}, {"operator": "EQ", "value": "BROWSER", "key": "client_type", "category": "computed"}]}, {"and": [{"or": [{"and": [{"operator": "IN", "value": "EN", "key": "languages", "category": "profile"}, {"key": "26366", "operator": "EQ", "value": 100, "category": "skill"}]}]}, {"or": [{"operator": "IN", "value": 204, "key": "region_by_phone", "category": "computed"}, {"operator": "IN", "value": 983, "key": "region_by_phone", "category": "computed"}]}, {"operator": "LT", "value": 847141200, "key": "date_of_birth", "category": "profile"}, {"operator": "GT", "value": 342219600, "key": "date_of_birth", "category": "profile"}]}]}',
    )

    static_pricing_strategy = pricing.StaticPricingStrategy()
    check(static_pricing_strategy, lzy.StaticPricingStrategy, b'')

    dynamic_pricing_strategy = pricing.DynamicPricingStrategy(max_ratio=2.0)
    check(dynamic_pricing_strategy, lzy.DynamicPricingStrategy, b'\r\x00\x00\x00@')

    check(static_pricing_strategy, lzy.PricingStrategy, b'\n\x00')

    check(dynamic_pricing_strategy, lzy.PricingStrategy, b'\x12\x05\r\x00\x00\x00@')

    human = worker.Human(toloka.Assignment(id='aid', user_id='uid'))
    check(human, lzy.Human, b'\n\x03uid\x12\x03aid')

    def model_func(x: int):
        return x**2

    lzy.register_func(model_func, 'square')

    model = worker.Model(name='my-model', func=model_func)
    check(model, lzy.Model, b'\n\x08my-model\x12\x06square')

    model_deserialized = lzy.Model.loads(b'\n\x08my-model\x12\x06square').deserialize()
    assert model_deserialized.func(3) == 9

    model_missing_func_deserialized = lzy.Model.loads(b'\n\x08my-model\x12\x06?').deserialize()
    with pytest.raises(RuntimeError):
        model_missing_func_deserialized.func()

    check(human, lzy.Worker, b'\n\n\n\x03uid\x12\x03aid')

    check(model, lzy.Model, b'\n\x08my-model\x12\x06square')

    label_proba = Animal.DOG, 1.0
    check(label_proba, lzy.LabelProba, b'\n\x0f\n\r\n\x03dog\x12\x06Animal\x15\x00\x00\x80?')

    task_labels_probas = {Animal.DOG: 1.0, Animal.CAT: 0.0}
    check(
        task_labels_probas,
        lzy.TaskLabelsProbas,
        b'\n\x16\n\x0f\n\r\n\x03dog\x12\x06Animal\x15\x00\x00\x80?\n\x16\n\x0f\n\r\n\x03cat\x12\x06Animal\x15\x00\x00\x00\x00',
    )

    worker_label = (Animal.DOG, human)
    check(worker_label, lzy.WorkerLabel, b'\n\x0f\n\r\n\x03dog\x12\x06Animal\x12\x0c\n\n\n\x03uid\x12\x03aid')

    worker_weights = {'bob': 1.0, 'model': 0.0}
    check(worker_weights, lzy.WorkerWeights, b'\n\n\n\x03bob\x15\x00\x00\x80?\n\x0c\n\x05model\x15\x00\x00\x00\x00')

    worker_label_2 = (Animal.CAT, model)
    classification_results = [
        (task_labels_probas, [worker_label, worker_label_2]),
        (None, []),
    ]
    check(
        classification_results,
        lzy.Results,
        b"\n~\x12J\n\x1f\n\x0f\n\r\n\x03dog\x12\x06Animal\x12\x0c\n\n\n\x03uid\x12\x03aid\n'\n\x0f\n\r\n\x03cat\x12\x06Animal\x12\x14\x12\x12\n\x08my-model\x12\x06square\n0\n\x16\n\x0f\n\r\n\x03dog\x12\x06Animal\x15\x00\x00\x80?\n\x16\n\x0f\n\r\n\x03cat\x12\x06Animal\x15\x00\x00\x00\x00\n\x02\x12\x00",
    )

    static_overlap = classification_loop.StaticOverlap(overlap=5)
    check(static_overlap, lzy.StaticOverlap, b'\x08\n')

    dynamic_overlap_1 = classification_loop.DynamicOverlap(min_overlap=2, max_overlap=3, confidence=1.0)
    check(dynamic_overlap_1, lzy.DynamicOverlap, b'\x08\x04\x10\x06\x1d\x00\x00\x80?')

    dynamic_overlap_2 = classification_loop.DynamicOverlap(min_overlap=3, max_overlap=5, confidence=task_labels_probas)
    check(
        dynamic_overlap_2,
        lzy.DynamicOverlap,
        b'\x08\x06\x10\n"0\n\x16\n\x0f\n\r\n\x03dog\x12\x06Animal\x15\x00\x00\x80?\n\x16\n\x0f\n\r\n\x03cat\x12\x06Animal\x15\x00\x00\x00\x00',
    )

    check(static_overlap, lzy.Overlap, b'\n\x02\x08\n')

    check(
        dynamic_overlap_2,
        lzy.Overlap,
        b'\x126\x08\x06\x10\n"0\n\x16\n\x0f\n\r\n\x03dog\x12\x06Animal\x15\x00\x00\x80?\n\x16\n\x0f\n\r\n\x03cat\x12\x06Animal\x15\x00\x00\x00\x00',
    )

    aggregation_algorithm = classification.AggregationAlgorithm.DAWID_SKENE
    check(aggregation_algorithm, lzy.AggregationAlgorithm, b'\n\x0bdawid-skene')

    expert_params = params.ExpertParams(
        task_duration_hint=datetime.timedelta(seconds=10),
        pricing_config=pricing.PoolPricingConfig(assignment_price=1.0, real_tasks_count=2, control_tasks_count=0),
    )
    check(
        expert_params,
        lzy.ExpertParams,
        b'\n\x04\x08\n\x10\x00\x15\x00\x00\x80?\x18\x04',
    )

    classification_params = params.Params(
        task_duration_hint=datetime.timedelta(seconds=3),
        pricing_config=pricing.PoolPricingConfig(assignment_price=2.0, real_tasks_count=15, control_tasks_count=4),
        overlap=static_overlap,
        control=ctrl,
        worker_filter=worker_filter,
        aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
        pricing_strategy=static_pricing_strategy,
        task_duration_function=model_func,
    )
    check(
        classification_params,
        lzy.Params,
        b'\n\x04\x08\x03\x10\x00\x15\x00\x00\x00@\x18\x1e\xa2\x060\x12.\x08d\xa2\x06\x1a\n\x06\n\x02EN\x10\x01\n\x06\n\x02IT\x10\x00\x12\x04\x98\x03\xae\x0f\x180 P\xa2\x06\x0c\n\x06\n\x02DE\x10\x00\x12\x00\x18$\xa8\x06\x08\xb2\x06\x02\n\x00\xba\x06a\n&\n\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00\x12\x12\n\x10\n\x04POOL\x12\x08too fast\n7\n,\x18\x00"\x04\n\x02or*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01>\x18\x00*\x10\n\x0c\n\x05\r\x00\x00\x00?\x12\x03\n\x01<\x18\x00\x12\x07\x12\x05\r\x00\x00\x80?\xc2\x06\x04\n\x02\x08\n\xca\x06\x10\n\x0emax-likelihood\xda\x06\x06square',
    )

    assignment_check_sample = evaluation.AssignmentCheckSample(
        max_tasks_to_check=3,
        assignment_accuracy_finalization_threshold=1.0,
    )
    check(assignment_check_sample, lzy.AssignmentCheckSample, b'\x08\x06\x15\x00\x00\x80?')

    assignment_check_sample_empty = evaluation.AssignmentCheckSample(
        max_tasks_to_check=None,
        assignment_accuracy_finalization_threshold=None,
    )
    check(assignment_check_sample_empty, lzy.AssignmentCheckSample, b'')

    annotation_params = params.AnnotationParams(
        task_duration_hint=datetime.timedelta(minutes=1),
        pricing_config=pricing.PoolPricingConfig(assignment_price=3.0, real_tasks_count=5, control_tasks_count=0),
        overlap=classification_loop.DynamicOverlap(min_overlap=1, max_overlap=3, confidence=1.0),
        control=ctrl_empty,
        worker_filter=worker_filter_empty,
        aggregation_algorithm=None,
        pricing_strategy=dynamic_pricing_strategy,
        assignment_check_sample=assignment_check_sample,
        task_duration_function=None,
    )
    annotation_params.model = model
    check(
        annotation_params,
        lzy.AnnotationParams,
        b'\n\x04\x08<\x10\x00\x15\x00\x00@@\x18\n\xa2\x06\x02\x12\x00\xa8\x06\x00\xb2\x06\x07\x12\x05\r\x00\x00\x00@\xba\x06\x00\xc2\x06\x0b\x12\t\x08\x02\x10\x06\x1d\x00\x00\x80?\xd2\x06\x12\n\x08my-model\x12\x06square\xc2\x0c\x07\x08\x06\x15\x00\x00\x80?',
    )

    solution_evaluation = evaluation.SolutionEvaluation(
        ok=True,
        confidence=1.0,
        worker_labels=[worker_label, worker_label_2],
    )
    check(
        solution_evaluation,
        lzy.SolutionEvaluation,
        b"\x08\x01\x15\x00\x00\x80?\x1aJ\n\x1f\n\x0f\n\r\n\x03dog\x12\x06Animal\x12\x0c\n\n\n\x03uid\x12\x03aid\n'\n\x0f\n\r\n\x03cat\x12\x06Animal\x12\x14\x12\x12\n\x08my-model\x12\x06square",
    )

    solution_verdict = feedback_loop.SolutionVerdict.BAD
    check(solution_verdict, lzy.SolutionVerdict, b'\x08\x00')

    solution = feedback_loop.Solution(
        solution=objs,
        verdict=feedback_loop.SolutionVerdict.OK,
        evaluation=solution_evaluation,
        assignment_accuracy=1.0,
        assignment_evaluation_recall=0.0,
        worker=human,
    )
    check(
        solution,
        lzy.Solution,
        b"\n0\n\x0b\n\t*\x07\n\x05hello\n\x00\n\x1f\n\x1d:\x1b\n\x19https://storage.net/1.jpg\x12\x02\x08\x04\x1aS\x08\x01\x15\x00\x00\x80?\x1aJ\n\x1f\n\x0f\n\r\n\x03dog\x12\x06Animal\x12\x0c\n\n\n\x03uid\x12\x03aid\n'\n\x0f\n\r\n\x03cat\x12\x06Animal\x12\x14\x12\x12\n\x08my-model\x12\x06square%\x00\x00\x80?-\x00\x00\x00\x002\x0c\n\n\n\x03uid\x12\x03aid",
    )

    solution_2 = feedback_loop.Solution(
        solution=objs,
        verdict=feedback_loop.SolutionVerdict.UNKNOWN,
        evaluation=None,
        assignment_accuracy=0.0,
        assignment_evaluation_recall=1.0,
        worker=model,
    )
    check(
        solution_2,
        lzy.Solution,
        b'\n0\n\x0b\n\t*\x07\n\x05hello\n\x00\n\x1f\n\x1d:\x1b\n\x19https://storage.net/1.jpg\x12\x02\x08\x02%\x00\x00\x00\x00-\x00\x00\x80?2\x14\x12\x12\n\x08my-model\x12\x06square',
    )
