import pytest
from typing import List

from mock import patch
import pandas as pd
import toloka.client as toloka

from crowdom import base, datasource, objects
from . import lib


def test_parse_rows():
    task_mapping = lib.audio_transcript_ext_mapping

    assert datasource.parse_rows(
        [{'audio_link': 'https://storage.net/1.wav'}, {'audio_link': 'https://storage.net/2.wav'}],
        task_mapping,
        has_solutions=False,
    ) == [
        (objects.Audio(url='https://storage.net/1.wav'),),
        (objects.Audio(url='https://storage.net/2.wav'),),
    ]

    assert datasource.parse_rows(
        [
            {'audio_link': 'https://storage.net/1.wav', 'choice': 'sil'},
            {'audio_link': 'https://storage.net/2.wav', 'output': 'hello', 'choice': 'sp'},
        ],
        task_mapping,
        has_solutions=True,
    ) == [
        ((objects.Audio(url='https://storage.net/1.wav'),), (None, lib.sil)),
        (
            (objects.Audio(url='https://storage.net/2.wav'),),
            (
                objects.Text(text='hello'),
                lib.sp,
            ),
        ),
    ]

    no_solutions_err = "error in file entry #1: it must have the following fields: [('audio_link', <class 'str'>)]"

    with pytest.raises(ValueError) as e:
        datasource.parse_rows([{}], task_mapping, has_solutions=False)
    assert str(e.value) == no_solutions_err

    with pytest.raises(ValueError) as e:
        datasource.parse_rows([{'audio': 42}], task_mapping, has_solutions=False)
    assert str(e.value) == no_solutions_err

    has_solutions_err = (
        "error in file entry #1: it must have the following fields: [('audio_link', <class 'str'>), "
        "('output', <class 'str'>), ('choice', <class 'str'>)]"
    )

    with pytest.raises(ValueError) as e:
        datasource.parse_rows([{}], task_mapping, has_solutions=True)
    assert str(e.value) == has_solutions_err

    with pytest.raises(ValueError) as e:
        datasource.parse_rows(
            [{'audio': 'https://storage.net/1.wav', 'output': 'hello'}], task_mapping, has_solutions=True
        )
    assert str(e.value) == has_solutions_err

    with pytest.raises(ValueError) as e:
        datasource.parse_rows(
            [{'audio': 'https://storage.net/1.wav', 'choice': True}], task_mapping, has_solutions=True
        )
    assert str(e.value) == has_solutions_err


def test_file_format():
    task_mapping = lib.audio_transcript_ext_mapping

    pd.testing.assert_frame_equal(
        datasource.file_format(task_mapping, has_solutions=False), pd.DataFrame([{'name': 'audio_link', 'type': 'str'}])
    )
    pd.testing.assert_frame_equal(
        datasource.file_format(task_mapping, has_solutions=True),
        pd.DataFrame(
            [
                {'name': 'audio_link', 'type': 'str'},
                {'name': 'output', 'type': 'str'},
                {'name': 'choice', 'type': 'str'},
            ]
        ),
    )


@patch('boto3.session.Session', lib.Boto3SessionStub)
def test_substitute_media_output():
    assignments = [
        (
            toloka.Assignment(status=toloka.Assignment.REJECTED),
            [
                ((objects.Text(text='hello'),), (objects.Audio(url='attachment-id_1'), objects.Text(text='ok'))),
                ((objects.Text(text='no thank you'),), (objects.Audio(url='attachment-id_2'), None)),
            ],
        ),
        (
            toloka.Assignment(status=toloka.Assignment.ACCEPTED),
            [
                ((objects.Text(text='nice'),), (objects.Audio(url='attachment-id_3'), None)),
                ((objects.Text(text='bye-bye'),), (objects.Audio(url='attachment-id_4'), None)),
            ],
        ),
        (
            toloka.Assignment(status=toloka.Assignment.SUBMITTED),
            [
                ((objects.Text(text='ok'),), (objects.Audio(url='attachment-id_5'), objects.Text(text='ok'))),
                ((objects.Text(text='where is he'),), (objects.Audio(url='attachment-id_6'), objects.Text(text='ok'))),
            ],
        ),
        (
            toloka.Assignment(status=toloka.Assignment.SUBMITTED),
            [
                ((objects.Text(text='later'),), (objects.Audio(url='attachment-id_7'), objects.Text(text='ok'))),
                ((objects.Text(text='no'),), (objects.Audio(url='attachment-id_8'), objects.Text(text='bad'))),
            ],
        ),
    ]

    class TolokaClientStub(lib.TolokaClientCallRecorderStub):
        def __init__(self, attachments: List[toloka.Attachment]):
            self.id_to_attachment = {attachment.id: attachment for attachment in attachments}
            super(TolokaClientStub, self).__init__()

        def get_attachment(self, attachment_id: str) -> toloka.Attachment:
            super(TolokaClientStub, self).get_attachment(attachment_id)
            return self.id_to_attachment[attachment_id]

    s3 = datasource.S3(endpoint='storage.net', bucket='my-bucket', path='Data/Audio')
    stub = TolokaClientStub(
        attachments=[
            toloka.attachment.AssignmentAttachment(id=id, name=name, media_type='application/octet-stream')
            for id, name in [
                ('attachment-id_1', 'aabb.wav'),
                ('attachment-id_2', '1234.wav'),
                ('attachment-id_3', 'qqss.wav'),
                ('attachment-id_4', '5gg5.wav'),
                ('attachment-id_5', '1001.wav'),
                ('attachment-id_6', 'zz99.wav'),
                ('attachment-id_7', 'rr22.wav'),
                ('attachment-id_8', '9876.wav'),
            ]
        ]
    )
    new_assignments = datasource.substitute_media_output(assignments, s3, stub)  # noqa

    assert new_assignments == [
        (
            toloka.Assignment(status=toloka.Assignment.REJECTED),
            [
                (
                    (objects.Text(text='hello'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/aabb.wav'), objects.Text(text='ok')),
                ),
                (
                    (objects.Text(text='no thank you'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/1234.wav'), None),
                ),
            ],
        ),
        (
            toloka.Assignment(status=toloka.Assignment.ACCEPTED),
            [
                (
                    (objects.Text(text='nice'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/qqss.wav'), None),
                ),
                (
                    (objects.Text(text='bye-bye'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/5gg5.wav'), None),
                ),
            ],
        ),
        (
            toloka.Assignment(status=toloka.Assignment.SUBMITTED),
            [
                (
                    (objects.Text(text='ok'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/1001.wav'), objects.Text(text='ok')),
                ),
                (
                    (objects.Text(text='where is he'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/zz99.wav'), objects.Text(text='ok')),
                ),
            ],
        ),
        (
            toloka.Assignment(status=toloka.Assignment.SUBMITTED),
            [
                (
                    (objects.Text(text='later'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/rr22.wav'), objects.Text(text='ok')),
                ),
                (
                    (objects.Text(text='no'),),
                    (objects.Audio(url='https://storage.net/my-bucket/Data/Audio/9876.wav'), objects.Text(text='bad')),
                ),
            ],
        ),
    ]

    assert s3.client.calls == [
        (
            'put_object',
            {
                'ACL': 'public-read',
                'Bucket': 'my-bucket',
                'ContentType': 'application/octet-stream',
                'Key': 'Data/Audio/1001.wav',
            },
        ),
        (
            'put_object',
            {
                'ACL': 'public-read',
                'Bucket': 'my-bucket',
                'ContentType': 'application/octet-stream',
                'Key': 'Data/Audio/zz99.wav',
            },
        ),
        (
            'put_object',
            {
                'ACL': 'public-read',
                'Bucket': 'my-bucket',
                'ContentType': 'application/octet-stream',
                'Key': 'Data/Audio/rr22.wav',
            },
        ),
        (
            'put_object',
            {
                'ACL': 'public-read',
                'Bucket': 'my-bucket',
                'ContentType': 'application/octet-stream',
                'Key': 'Data/Audio/9876.wav',
            },
        ),
    ]

    assert stub.calls == [
        ('get_attachment', ('attachment-id_1',)),
        ('get_attachment', ('attachment-id_2',)),
        ('get_attachment', ('attachment-id_3',)),
        ('get_attachment', ('attachment-id_4',)),
        ('get_attachment', ('attachment-id_5',)),
        ('get_attachment', ('attachment-id_6',)),
        ('get_attachment', ('attachment-id_7',)),
        ('get_attachment', ('attachment-id_8',)),
        ('download_attachment', ('attachment-id_5',)),
        ('download_attachment', ('attachment-id_6',)),
        ('download_attachment', ('attachment-id_7',)),
        ('download_attachment', ('attachment-id_8',)),
    ]


def test_has_media_output():
    assert (
        datasource.has_media_output(base.AnnotationFunction(inputs=(objects.Audio,), outputs=(objects.Text,))) is False
    )
    assert (
        datasource.has_media_output(
            base.AnnotationFunction(inputs=(objects.Text,), outputs=(objects.Text, objects.Image))
        )
        is True
    )


def test_assert_tasks_are_unique():
    with pytest.raises(AssertionError):
        datasource.assert_tasks_are_unique(
            [
                ((objects.Audio(url='https://storage.net/1.wav'),), (lib.sil,)),
                ((objects.Audio(url='https://storage.net/2.wav'),), (lib.sp,)),
                ((objects.Audio(url='https://storage.net/1.wav'),), (lib.sil,)),
            ]
        )


def test_assert_tasks_are_unique_with_metadata():
    datasource.assert_tasks_are_unique(
        [
            (objects.Audio(url='https://storage.net/1.wav'), base.Metadata('metadata-1')),
            (objects.Audio(url='https://storage.net/2.wav'), base.Metadata('metadata-2')),
            (objects.Audio(url='https://storage.net/1.wav'), base.Metadata('metadata-3')),
        ]
    )
