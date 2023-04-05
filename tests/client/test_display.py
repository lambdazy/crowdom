import datetime
from decimal import Decimal
import numpy as np
from itertools import chain
from typing import List, Tuple, Dict

import pytest
import pandas as pd
from pytest import fixture

import toloka.client as toloka

from crowdom import (
    base,
    client,
    evaluation,
    feedback_loop,
    mapping,
    objects,
    project,
    task_spec as spec,
    worker,
)
from crowdom.objects import Text
from .. import lib


class Noise(objects.Question):
    POOR = 'poor'
    FAIR = 'fair'
    BAD = 'bad'
    EXCELLENT = 'excellent'

    @classmethod
    def question_label(cls) -> Dict[str, str]:
        return {
            'RU': '**Встречаются ли лишние шумы или искажения сигнала?**',
            'EN': '**Are there any noises or singal corruption?**',
        }


class Intonation(objects.Question):
    EXCELLENT = 'excellent'
    BAD = 'bad'

    @classmethod
    def question_label(cls) -> Dict[str, str]:
        return {
            'RU': '**Верно ли интонация на аудио передаёт смысл написанного текста?**',
            'EN': '**Does intonation convey correct meaning of the text?**',
        }


Question, Answer, question_answers_list = objects.get_combined_classes([Noise, Intonation])


@fixture
def qq_function() -> base.ClassificationFunction:
    return base.ClassificationFunction(
        inputs=(
            base.ObjectMeta(type=objects.Audio, name='audio'),
            base.ClassMeta(
                type=Question,
                name='question',
                input_display_type=base.LabelsDisplayType.MONO,
                title=base.Title(text={'RU': 'Вопрос', 'EN': 'Question'}, format=base.TextFormat.MARKDOWN),
                text_format=base.TextFormat.MARKDOWN,
            ),
        ),
        cls=base.ClassMeta(
            type=Answer,
            name='answer',
            available_labels=base.create_available_labels_if('question', question_answers_list),
            title=base.Title(text={'RU': 'Ответ', 'EN': 'Answer'}, format=base.TextFormat.MARKDOWN),
        ),
    )


@fixture
def inner_spec() -> base.TaskSpec:
    return base.TaskSpec(
        function=base.ClassificationFunction(inputs=(objects.Image,), cls=lib.ImageClass),
        id='id',
        name=base.EMPTY_STRING,
        description=None,  # noqa
        instruction=None,  # noqa
    )


@fixture
def qq_inner_spec(qq_function: base.ClassificationFunction) -> base.TaskSpec:
    return base.TaskSpec(
        function=qq_function,
        id='id',
        name=base.EMPTY_STRING,
        description=None,  # noqa
        instruction=None,  # noqa
    )


@fixture
def inner_annotation_spec() -> base.TaskSpec:
    return base.TaskSpec(
        function=base.AnnotationFunction(
            inputs=(objects.ObjectMeta(objects.Image),),
            outputs=(objects.ObjectMeta(Text, required=False),),
        ),
        name=base.EMPTY_STRING,
        description=base.EMPTY_STRING,
        id='id',
        instruction=None,  # noqa
    )


@fixture
def inner_image_annotation_spec() -> base.TaskSpec:
    return base.TaskSpec(
        function=base.AnnotationFunction(
            inputs=(objects.ObjectMeta(objects.Image),),
            outputs=(objects.ObjectMeta(base.ImageAnnotation),),
        ),
        name=base.EMPTY_STRING,
        description=base.EMPTY_STRING,
        id='id',
        instruction=None,  # noqa
    )


@fixture
def task_spec(inner_spec: base.TaskSpec) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(task_spec=inner_spec, lang='RU')


@fixture
def qq_task_spec(qq_inner_spec: base.TaskSpec) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(task_spec=qq_inner_spec, lang='RU')


@fixture
def annotation_task_spec(inner_annotation_spec: base.TaskSpec) -> spec.AnnotationTaskSpec:
    return spec.AnnotationTaskSpec(task_spec=inner_annotation_spec, lang='RU')


@fixture
def image_annotation_task_spec(inner_image_annotation_spec: base.TaskSpec) -> spec.AnnotationTaskSpec:
    return spec.AnnotationTaskSpec(task_spec=inner_image_annotation_spec, lang='RU')


@fixture
def expert_solution_task_spec(inner_spec: base.TaskSpec) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(
        task_spec=inner_spec, scenario=project.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS, lang='RU'
    )


@fixture
def expert_task_task_spec(inner_spec: base.TaskSpec) -> spec.PreparedTaskSpec:
    return spec.PreparedTaskSpec(task_spec=inner_spec, scenario=project.Scenario.EXPERT_LABELING_OF_TASKS, lang='RU')


@fixture
def expert_task_annotation_task_spec(inner_annotation_spec: base.TaskSpec) -> spec.AnnotationTaskSpec:
    return spec.AnnotationTaskSpec(
        task_spec=inner_annotation_spec, lang='RU', scenario=project.Scenario.EXPERT_LABELING_OF_TASKS
    )


@fixture
def expert_solution_annotation_task_spec(inner_annotation_spec: base.TaskSpec) -> spec.AnnotationTaskSpec:
    return spec.AnnotationTaskSpec(
        task_spec=inner_annotation_spec, lang='RU', scenario=project.Scenario.EXPERT_LABELING_OF_SOLVED_TASKS
    )


@fixture
def images() -> List[objects.Image]:
    return [objects.Image(url=f'https://storage.net/{i}.jpg') for i in range(8)]


@fixture
def solutions(
    images: List[objects.Image],
) -> List[List[Tuple[objects.Image, lib.ImageClass, base.BinaryEvaluation, Text]]]:
    dog, cat, crow = lib.dog, lib.cat, lib.crow
    ok, bad = lib.ok, lib.bad

    return [
        [(images[0], cat, ok, Text('')), (images[1], dog, bad, Text('may be cat'))],
        [(images[2], cat, ok, Text('persian cat')), (images[3], dog, bad, Text('not sure'))],
        [(images[4], crow, ok, Text('may be pigeon')), (images[5], crow, ok, Text(''))],
    ]


@fixture
def annotation_solutions(
    images: List[objects.Image],
) -> List[List[Tuple[objects.Image, Text, base.BinaryEvaluation, base.BinaryEvaluation, Text]]]:
    true, false = base.BinaryEvaluation(ok=True), base.BinaryEvaluation(ok=False)
    return [
        [(images[0], Text('0'), false, false, Text('c-0')), (images[1], Text('1'), false, true, Text('c-1'))],
        [(images[2], Text('2'), true, false, Text('c-2')), (images[3], Text('3'), true, true, Text('c-3'))],
        [(images[4], Text('4'), false, false, Text('')), (images[5], Text('5'), false, true, Text(''))],
        [(images[6], Text('6'), true, false, Text('')), (images[7], Text('7'), true, true, Text(''))],
    ]


@fixture
def assignments() -> List[toloka.Assignment]:
    return [
        toloka.Assignment(
            user_id=user_id,
            created=datetime.datetime(year=2020, month=10, day=7, hour=10, minute=3),
            submitted=datetime.datetime(year=2020, month=10, day=7, hour=10, minute=4 + i),
            tasks=[(), ()],
        )
        for i, user_id in enumerate(['bob', 'mary', 'john', 'cate'])
    ]


@fixture
def results_task(
    images: List[objects.Image],
    assignments: List[toloka.Assignment],
    solutions: List[List[Tuple[objects.Image, lib.ImageClass, base.BinaryEvaluation, Text]]],
) -> List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]]:
    return [
        ((images[i],), ((images[i],), [((cls, ok, comment), assignments[i // 2])]))
        for i, (_, cls, ok, comment) in enumerate(chain(*solutions))
    ]


@fixture
def results_solution(
    images: List[objects.Image],
    assignments: List[toloka.Assignment],
    solutions: List[List[Tuple[objects.Image, lib.ImageClass, base.BinaryEvaluation, Text]]],
) -> List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]]:
    return [
        ((images[i], cls), ((images[i], cls), [((ok, comment), assignments[i // 2])]))
        for i, (_, cls, ok, comment) in enumerate(chain(*solutions))
    ]


@fixture
def annotation_results_task(
    images: List[objects.Image],
    assignments: List[toloka.Assignment],
    annotation_solutions: List[List[Tuple[objects.Image, lib.ImageClass, base.BinaryEvaluation, Text]]],
) -> List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]]:
    return [
        ((images[i],), ((images[i],), [((text, ok, ok_, comment), assignments[i // 2])]))
        for i, (_, text, ok, ok_, comment) in enumerate(chain(*annotation_solutions))
    ]


@fixture
def annotation_results_solution(
    images: List[objects.Image],
    assignments: List[toloka.Assignment],
    annotation_solutions: List[List[Tuple[objects.Image, lib.ImageClass, base.BinaryEvaluation, Text]]],
) -> List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]]:
    return [
        ((images[i], text), ((images[i], text), [((ok, ok_, comment), assignments[i // 2])]))
        for i, (_, text, ok, ok_, comment) in enumerate(chain(*annotation_solutions))
    ]


@fixture
def url() -> str:
    return 'https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzEEVlbxcdCEMDIxBTNQgeCjhoelVmaz4OFks1dQgEGTUOPgAjfC5VbDyC2KcMrJzsMAFC7GKyiqtwFtrUMhxM7O8wNghiECD28uHR8eMAXSD1OFpSjnx1BhhM2nwggY44F2Sodw0tM89hSp8-ANbgizCtbUiKaMc1QT0YrsAkEEA0iCARhBAKwggAEQQAcIIAhEBBqEAfCCAFhAIYBeEFQEMA7CCoQBMIIAGEEhOORULhWIeIUa4GgyyS0G0bHwAEcWHA6ZteuZQjd4OV1LS+MsIABaBCjFg8EyLNRk7w2QjaQ60GJxDxZBB6VJodIgACMZ3ClwE1y6YF8-kCkqeN3Cryihk+Hj4Cg4ED5YXypItXT4YGpUG0u0VQSlNx4Kr02l8FAA1vgFKk4mQAEy6i6qXgG4Ym+4Tc0crpWt4fNkgfiO52so09QMetRen1+-ABnPkkMsVW+iPR2OfMgAZmTrn1XhuxruZvZ5PzNsb9tLLuHs3duZr3pO9enjyXytbYY7MbjdRAxQUbzOkb05bUtBGEA4FUDfFokYA6kch2gAOwABk-2k-SpAUAQEk8DND66pMGQkBQFQ0HeIA+CDgiCCLYgCgD8IHCgDcIMiILIhCIKADwgqCoWCxLgoAMiAwrIgDiIES2KAIIgsL4UhEI4gKgCyIBhBE4VCAKoOiOKAMwgYKAMIg6IQhhEJ0WR2iLuSMraFQAAejaQdAMG-GogCoIHREmoNhUKoIAoiBwlCgDyIKgQK8YiyJwgJcKoExSKsRxXGEjisioYh-FCaJ0KwnRUJggSEKAGIgwkydm47SgQspKYqEpRcGoa+hQN4QJGbixPMxjZuQ+iGKoGCiPY5KCBQ7y0MgAD0VWEJkHD8MobBXnwOD4LSLBVWIEj4LQVUQGwiB6JkVVagAHFVn4AGwCuNVV8FA3UcLQArVCtACsY0AJw9u+2gAFY8DUQRHN4ACSJUABTsBwAC8ADkZUVdVtX1Y1+DNc0bUdV1JV9QNQ1QCNc3TbNE0LUtK1rQKm07Xth0IPdACUJixEAA'  # noqa


@fixture
def annotation_default_url() -> str:
    return 'https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJEgqADyMgZj4W3i46EIYGAaZqisre8Pgc6tp+rmz4biDGALpBcZZqNoTaHHC00UE8HCwIevSqzNgcfAoRAaTYANZ66t60YGwQHFyBsXy0XQDqcOpeqgDsAAxL2ksx2FAQFHDwYAJw0A1oTeDQVFAdaoD4IICsIIACILeALCCogEwggNIggPwggHwggNwggLwgt3+gA4QW6AHhBUJ97t9Xg9ADIggCEQW6yQDiIAjvm9AIIgt1QYOewMADCAAWkAsiC-cFAhHvVCAdhACYBmEHugGEQGnA37AzFw7QyWIhVTWAglNKOVBkSCXfCXbyAVBBMezUICEahAKIg3wRgHkQVCARhBqd8nv9vvSMXinoTSeS8f8EQTZJ8Hrc6YyWcCkahMQj7gSQYAxECZ3LG5ni-NwgtS+H8JjyvKDVhA1VqelSwwgXSyuWMY3I+kMqgwonshWwggoFB4tGQAHoK4Q+CN+Mo2AM+Dh8No2CwK2IJPhaBWIGxEHpaxWAIwADgrSwAbETxxW+FAuxxaET1BAECuAKxjgCcAGYFtoAFY8BA80R9YMASQLAAp2BwALwAcmLpfLVZrdb4DabLbbHZdpIvb9oOUDDnO06zhOC5Liua4bkS277oeJ4IM+ACUJjZEAA'  # noqa


@fixture
def annotation_check_default_url() -> str:
    return 'https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspChVX3bPyEiQVAB5GIGa+Fj6aFDp6BoGmaorKPjaE2v4xTtguboGkolR0DMwZ0Fk+gAQggKwggBIg5YC8IIAcIOWogEwg5YACIDWAfCDlAPwycaGq1gTJqY6oZOF8HiBewoMg+Dh8XEH9CfOT2hCG0WPYEDwUcND0qoW4yyyWqBRsV8EcfABG+CtWIIAoIIAMIGNkSxxXBgwZa0fAPZ6vHyAXBByoAhEBMAF1guo4LRnhx8OogSCwWp-nBwscoNNJtNZj5Fss+uZ1u9NtsKLsQLFsII9Nk1IAkEEA0iCARhA2nVYY0OoAWEDqNVQdUA7CDNL6tOpfGqwjpNakhWlqFwoo7QbRsfAARxYcH1WOZwXi12w8Fe6j1fBREAAtAg2NseIiLQN3kltBxUWk1lbcMNtK73Z6g4lQ-7aIHPACEHpTmhzgBGElaMkCObvSkrL0a7D0naGPYzPgKDgQB0MW73KPzPhgHVQbSg+Pq4M8RN6bSCCAUADW+AUp1iZAATJmItnvPN82rLWEtFtS53+FWa2a0MCOKDC8Hm632-hO8v5j2WEm2wPh6Px+kQI8FAzpkO9Du1LQwG6OAW4j4WghwAdQJec0AAdgABmg7RoJZEAoEHOB4DAAQiRTJhnGKfB3HmQB8EDacoRWablAH4QDpAG4QGpagaQAeEFQcjWhVNpABkQIVZEAcRBlWaQBBEEaeiSIVJ1AFkQKjyiEpVuVQKUvkAZhBWkAYRApTqKi6j4tjtCXb08VDUZzXGIpXDwjlsEAVBA+PU1BaNhVBAFEQDpYUAeRBUF5GTRU6eSOlQISxS+MSJKk2EvlkcjiLkxSVMFRo+NhVpFTqQAxECU7TVhpYNfQM4wkUbd4rxvFIIGrIcpmZBFjFWch9EMVQMFEexg0EChGVoZAAHp2sIZYOH4ZQ2B-PgcHwPUWHasQJHwWh2ogNhED0ZZ2rTAAOdroIANidFb2r4KAJv3J11AgBBaCdABWZaAE4AGZIO0AArHgECXfAAh8AzggJHwAElGoACnYDgAF4AHJmtajqup6vr8AG9DhtG8bGum2b5qgRbto2rbVt2-bTqOk7zqu26HqekGAEpUAAFVeig-tSUHUgpkxmSAA'  # noqa


@fixture
def expert_annotation_task_url() -> str:
    return 'https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJEgqADyMgZj4W3i46EIYGAaZqisre8Pgc6tp+rmz4biAxZJBQVPneALQlMrEhqtYEhNribADW6hCEUI6oudAFAaSiVHQMzNh5Xd6ABCCArCCAEiDjgLwggBwg46iATCDjgAIgM4B8IOMA-GXm8ZW41an4-m3OWu4gnsKH+Dh8XIHlB1YaWtoRFFFt2BA8FDg0HoqkGuEeLEsqAobEhQQ4fAARklvIAUEEADCDnawQqEwR60fDwpEow6AXBBxoAhEBMAF0guo4LQkRx8OoGHiOASgg8OHAXEDWqoLq4rjdvPdHntgq81GFPpFDL8QII9N01IAkEEA0iCARhA1nMKYsNoAWEDmM1Qc0A7CDLdGrObomYUjZLSVxKFDaD0wHQbQZACOLDgGVZ2SCLoSBGS3r49IgRQQbAiPBpIYqbxsNR5tGiyelVVscYTWPAnXwhUFvRoILQYOGJdV2EAWCAbVarcaALhAKZtUIBuEDmqHN6MNdoWqAAFL2W9N5uNZIB+EBtqBm6J7gHEQOZzACUu2e+1dR1saULYRFAlubwA+hB6s6UzKPl8fsG1P9PVBK0wyNzIQwYXC1AjkU8bwYoWn64vihJ-sSgFqOSVLZLSMoMkyLJsuBXKPLyAj8lcR5ltcJ7eBeV7blKu6yveCqPtgyqlm8mo6ja+qoEaJpmpaSzWra9qOteOZFlAHr8t6+B+gGKFUaRYZJCkbBRkCsbxiwibwdmu5ptoGZZi8anHPmSmHpceGiocZ6QNQ1C1rxZF3vKWkeAiYD4IIEDJPgbDeK2GyADwgXmzBSnGAJwgVlSRGaR8BkWTGAhO7eOpmmKjwHAsAgehvmCACMOGGT0+FeHc3LBYc5G2QlfAKBwEBRt+sIQTFhx8GAL7aASdmSYciXJXo2jORQ9T4AoII5NgABMWXCkZBH5RKJGhkVNnfJRMQeGVFVVao7Kctp3gNU1LWKrNbwdSlUDdRAvX9YNTjYAAzGNWQ5cZ56XoVbzFQtrX8OVlVBmgP61W1bw7UJe0SQdahHV1PV9QNhYACx3ceeVPcRqmhPND5LfhX1rWgG3-WD2BA16IOYwT1xJcdp3nTDj5kAiChfFc9R6D9ai0GA8YcE8IZ8LQ9QAOq8kjqAAOwAAxi9oYuY1AZ1wPAYBYcCAwdPklmHIA+CBrOMhrLBqM4bF2MyzAsXmoHOjprIAMiD6rIy4OssgCCIIsvnGuiRSALIgXbjL59oan26KAMwgqyAMIg5pzD2jtW9oL1qOpB6026au0WogCoII7PYLpSqCAKIgGwUoA8iCoFq-tGpsgcbKgru2p73u+-5s7a-2wdh3qiyOxSqxDoAYiAhzHM03rmNQJ1FqPtRTXUUC5l6RdSxjPOQ+iGKoGCiPYu6CBQ3y0MgAD0u+EI8HD8MobDs3wOD4N6LC72IEj4LQu8QGwiB6I8u-pQAHLvYsAGxFF-XefAoB3w5EUJoCBaBFAAKyfwAJzXRFtoAAVjwBAkpeTeAAJLrxHOwDgABeAA5Jvbee8D5HxPm5c+l9r633Xo-Z+r8oDv0AX-AB39gGgKgRAqBsCEFINQQgIh64TDZCAA'  # noqa


@fixture
def expert_annotation_solved_task_url() -> str:
    return 'https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspChVX3bPyEiQVAB5GIGa+Fj6aFDp6BoGmaorKPjaE2v4xTtguboGkolR0DMwZ0Fk+gAQggKwggBIg5YC8IIAcIOWogEwg5YACIDWAfCDlAPwycaGq1gTJqY6oZOF8HiBewoMg+Dh8XEH9CfOT2hCG0WPYEDwUcND0qoW4yyyWqBRsV8EcfABG+CtWIIAoIIAMIGNkSxxXBgwZa0fAPZ6vHyAXBByoAhEBMAF1guo4LRnhx8OogSCwWp-nBwscoNNJtNZj5Fss+uZ1u9NtsKLsQLFsII9Nk1IAkEEA0iCARhA2nVYY0OoAWEDqNVQdUA7CDNL6tOpfGqwjpNakhWlqFwoo7QbRsfAARxYcH1WOZwXi12w8Fe6j1fBREAAtAg2NseIiLQN3kltBxUWk1lbcMNtK73b8iq58O55k742rLYlQ+I2ABrdQQQjE83jKMlVRkSg0U5oc6ZGMc7CALBAOq1WuVAFwgsM6qEA3CB1VBSr4ixUNVAACk7Deq9XKskA-CDy1A1L4dwDiIHU6gBKXqrGnB32jXMTLRkgRzd4AfQgacT3rU9J2hj2IAOOqgpaYf0u11u9zUjxebzU30jFwBa5gQ4UFwW-aE4U9S9UXRTFsRA3FrGWAkBCJEk90LTwDx8E8z3XdVgyvRkb1zVl2R8Hl+XlIVUFFcVJRlJo5QVJUVXPDUo21Ik9UNY1TVvJN5htDg7TYB1jhdN0WA9ZkkSDZNbH9WhAw3BTknDaT-1JTCZmw+Yj0gahqErdjCK0LZrxUmZHjAfBBAgET8DYHxGw6QAeEDc2pYWYwBOEFMnxhLtVI+H1KZZK9DiQ0UgNbx4AEED0J9zgARnQiJ928eZKRWCKzIiCziKs-gFA4CAHQYd9EIInw+DAB9tFBKzBPeOKWASqBtHsig03wBRTliMgACY0rCnJdMy95sv8jZzIZJkWV0kqyrNNBgNA+T5lq+rGoEi9PHivROogbrev69IQAAZhGjLDzUXDprpWbLNivglvK1RKtymq6u4nbSOq+ZWvao6Tr6-8ABZrp08l9NPB7LyewqXrelbUDWqrmrULbfvwJq9ustrDq6nqwZ3bBHgUBlpjTPRUewWgwDdDgcriPhaDTAB1AkJtQAB2AAGfntH5haoGOuB4DAVCTgKZxihM+ZAHwQNpyhFZpuQnDo2xqWoGjc1ApxVNpABkQIVZHnZVmkAQRBGk8sUvidQBZEDbcpPKVbkuy+QBmEFaQBhEClOoOyt43tHhoZbG3Ab8wV95AFQQK2OxnOFUEAURAOlhQB5EFQXkPdFTovY6VA7YVJ2Xbd7zJxV7sff9wVGit2FWj7QAxEF90P8Mx8ORnwAIoNUwGDo6igHNPMLjARYxVnIfRDFUDBRHsYNBAoRlaGQAB6dfCGWDh+GUNgGb4HB8D1Fh17ECR8FodeIDYRA9GWdfkoADnX-mADYnRf9e+CgC+QKdJmBAtAnQAFZn4AE4Lq820AAKx4AgRMPcqy+GQWqAkPgACSi8BzsA4AAXgAOTL1XhvLeO895OUPsfU+59F7X1vvfKAj9v4fy-q-X+-8QFAJAeAqBMD4EIEIcuVAAAVZBA5UhENSMIkwzIgA'  # noqa


@fixture
def expert_annotation_verification_url() -> str:
    return 'https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspChVX3bPyEiQVAB5GIGa+Fj6aFDp6BoGmaorKPjaE2v4xTtguboFWIAC0+TJxoarWBMnibADW6hCEUI6oztBZHuRUdAzMGc347iUggFgggHwggAIgI4CsIIBcIIBCIIC8IEOogNwggBwgqIDsIIAMIIAsIBuzy+OoABSrE4ASION747KA-CAjq7MbK4DiIMvLAJQA-IXmCf1JKfgAg0yOE+K0vMJ+gB9CCVb4hX45UHaCCGaINbAQHgUODQeiqLq4PgcFiWVAUNik4IcPgAI3wXH6gBQQDbA6zE0kMGDE2j4al0hk+QC4IONpiYALrBdRwWh0jj4dRcnl8tQ4YlwcK4+qqEFacECSE5GFwoJFRFqZGoijokCxbCCPTZNSAJBBANIggEYQcZ3aYHIZbZazVDLNaoQBMIBs7rtpkNQ-D4mTulBpTjoNo2PgAI4sODpxW24LxnzwBnqNN8aUQXIINiongSgvFHL-DgytJmhO4Mraau1tkaPU6zwGnxQyDUai9QIN83YS1owwYkA8GlgfCCCAcdT4Ng+SZDQA8IPuLtMI8tAJwgccbamLm4BAT46bBtsl7cSXZbtDbnhJCD0+LQhIAIytKC+reNCsKXjO-YRCi85fkufAKBwEDlgwFJUq+-R8GAKZQNovIIYW-TLiwv74euFCVPgCj4rEZAAEwgQOpBDuBRqQaaPwdnO1oLvmaj8MhqF5mg3IcLy04djheEEfgRFXt+ZF6NolHUbRfY0goVqtJUeiiWotBgDWHCMgWfC0JUADqGrsagADsAAMjnaI5dogFAEA4vAYACFq-5ME0riTj4gD4IF64xbGGrrXEMiyzBc+z7qgtwxl6gAyID6shPNGYaAIIgBxHv6Gy5IAsiCLOMR6zNMrrrBsgDMICMgDCIGsywrHl6XaFBHb-KkfaZCF-SAKggeUrKgCXTKggCiIEM0yAPIgqDurVfrzPVCxFcsJXlZVx4bDcEWbI1LXLD6qB5dMIy7MsgBiIE1XVcQiPVdn1z5ST4pHkSkG6wk+xjisYprkPohiqBgoj2B2ggUNatDIAA9HDhDEhw-DKGwRl8Dg+BpiwcNiBI+C0HDEBsIgejEnDgEABxw45ABsuTU3DfBQPjEm5DUCC0LkACsVMAJwAMz2doABWPAIHGgJOvI0vwhqPgAJIQ4c7AcAAvAA5FDMPw4jyOo9uGNYzjeMQ0TJNk1AFNM-TjM0yzbPc5z3N80LIviwgmtvKgAAq0uHKkWupN7Ji2kAA'  # noqa


@fixture
def image_url() -> str:
    return 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg'


class TestTaskPreview:
    def test_classification(self, task_spec: spec.PreparedTaskSpec, url: str, image_url: str):
        actual_url = client.TaskPreview.get_url((objects.Image(url=image_url),), task_spec)
        assert actual_url == url

    def test_annotation(
        self,
        annotation_task_spec: spec.AnnotationTaskSpec,
        annotation_default_url: str,
        image_url: str,
    ):
        actual_url = client.TaskPreview.get_url((objects.Image(url=image_url),), annotation_task_spec)
        assert actual_url == annotation_default_url

    def test_annotation_check(
        self,
        annotation_task_spec: spec.AnnotationTaskSpec,
        annotation_check_default_url: str,
        image_url: str,
    ):
        actual_url = client.TaskPreview.get_url(
            (objects.Image(url=image_url), objects.Text('text')), annotation_task_spec
        )
        assert actual_url == annotation_check_default_url

    def test_expert_annotation_task(
        self,
        expert_task_annotation_task_spec: spec.AnnotationTaskSpec,
        expert_annotation_task_url,
        image_url: str,
    ):
        actual_url = client.TaskPreview.get_url((objects.Image(url=image_url),), expert_task_annotation_task_spec)
        assert actual_url == expert_annotation_task_url

    def test_expert_annotation_solved_task(
        self,
        expert_task_annotation_task_spec: spec.AnnotationTaskSpec,
        expert_annotation_solved_task_url,
        image_url: str,
    ):
        actual_url = client.TaskPreview.get_url(
            (objects.Image(url=image_url), objects.Text('text')), expert_task_annotation_task_spec.check
        )
        assert actual_url == expert_annotation_solved_task_url

    def test_expert_annotation_verification(
        self,
        expert_solution_annotation_task_spec: spec.AnnotationTaskSpec,
        expert_annotation_verification_url,
        image_url: str,
    ):
        actual_url = client.TaskPreview.get_url(
            (objects.Image(url=image_url), objects.Text('text')), expert_solution_annotation_task_spec
        )
        assert actual_url == expert_annotation_verification_url

    def test_no_task_spec(self, inner_spec: base.TaskSpec, url: str, image_url: str):
        actual_url = client.TaskPreview(
            (objects.Image(url=image_url),), task_function=inner_spec.function, lang='RU'
        ).get_link()

        assert actual_url == f'<a href="{url}" target="_blank" rel="noopener noreferrer">task preview</a>'


class TestResults:
    def test_classification_results(self, task_spec: spec.PreparedTaskSpec):
        input_objects = [
            (objects.Image(url='https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg'),),
            (objects.Image(url='https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg'),),
            (objects.Image(url='https://upload.wikimedia.org/wikipedia/commons/0/0e/Felis_silvestris_silvestris.jpg'),),
        ]
        bob, alice, john = (worker.Human(toloka.Assignment(user_id=user_id)) for user_id in ('bob', 'alice', 'john'))
        results = [
            ({lib.cat: 0.7, lib.dog: 0.3}, [(lib.dog, john), (lib.cat, alice)]),
            ({lib.cat: 0.1, lib.dog: 0.9}, [(lib.dog, alice), (lib.cat, bob), (lib.dog, john)]),
            (None, []),
        ]

        worker_weights = {bob.id: 0.9, alice.id: 0.67, john.id: 0.25}

        # in this example one of the tasks doesn't have any solutions (can happen in MOS),
        # this is incorrect from task function point of view (choice is required), so we disable validation
        with mapping.DisableValidation():
            results_w = client.ClassificationResults(input_objects, results, task_spec)
            results_with_weights = client.ClassificationResults(input_objects, results, task_spec, worker_weights)
            for actual_df, expected_dict in (
                (
                    results_w.predict(),
                    [
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'result': 'cat',
                            'confidence': 0.7,
                            'overlap': 2,
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'result': 'dog',
                            'confidence': 0.9,
                            'overlap': 3,
                        },
                        {
                            'image': 'https://upload.wikimedia.org/wikipedia/commons/0/0e/Felis_silvestris_silvestris.jpg',
                            'result': np.nan,
                            'confidence': 0.0,
                            'overlap': 0,
                        },
                    ],
                ),
                (
                    results_w.predict_proba(),
                    [
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'proba_cat': 0.7,
                            'proba_dog': 0.3,
                            'proba_crow': 0.0,
                            'overlap': 2,
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'proba_cat': 0.1,
                            'proba_dog': 0.9,
                            'proba_crow': 0.0,
                            'overlap': 3,
                        },
                        {
                            'image': 'https://upload.wikimedia.org/wikipedia/commons/0/0e/Felis_silvestris_silvestris.jpg',
                            'proba_cat': 0.0,
                            'proba_dog': 0.0,
                            'proba_crow': 0.0,
                            'overlap': 0,
                        },
                    ],
                ),
                (
                    results_w.worker_labels(),
                    [
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'label': 'dog',
                            'worker': 'john',
                        },
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'label': 'cat',
                            'worker': 'alice',
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'label': 'dog',
                            'worker': 'alice',
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'label': 'cat',
                            'worker': 'bob',
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'label': 'dog',
                            'worker': 'john',
                        },
                    ],
                ),
                (
                    results_w._add_task_previews(results_w.predict()),
                    [
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'result': 'cat',
                            'confidence': 0.7,
                            'overlap': 2,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB4JiueTScVwBEI2g4txyQR4WwQekaaGaID6CgghncIAA1nonrDaLsIBwKu8+LRiQB1ODqLyqADsAAZOdpOVUQFAIHV4Ks6g0GDjIMV8MVvIB8EEArCCAARAFYAWEFQgCYQQDSIIB+EEAfCCAbhBALwgCqNgA4QBWAHhBUDqlXqNcrADIggCEQBWyQDiIM69ZrAIIgCtQlrVZsADCBAwCyIAarabnVrUIB2EGDgGYQJWAYRA42aDWafY7tPMQB9vDYEVQAB4oibxaBUWWwwCoID7M6gTc7UIBRED1zsA8iCoQCMILG9aqjXrE97A6qQ+HI4Gjc7g7IdcqFQnk2mza7UD7nUrg+bAGIgKdzh2hnyL2lLOSh5hhIzRLAxUDP1IgxLclQuxiP5H0hlUGFE9k+QQKAoHhaGQAB6cDCHKDh+GUNhKT4HB8D+FhwLECR8FocCIDYRA9HKcCAEYAA5wM5AA2IFSPAvgoAwjhaCBToECYgBWEiAE4AGZ2W0AArHhuiPeJEgCdIxhE8hyRGABJACAAp2A4ABeAByICQLAyDoJpOD8AQ1ZkNQ9CAOw3D8LKDhiLIyjqLIuiGKYlj2K43iBKEtSAEpUAAHnkzCAGE+loWhtAAEQAeQAcTQNSWLUgA+ExKiAA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'result': 'dog',
                            'confidence': 0.9,
                            'overlap': 3,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB4JiueTScVwBEI2g4txyQR4WwQekaaGaID6CgghncIAA1nonrDaLsIBwKu8+LRiQB1ODqLyqADsAAZOdpOVUQFAIHV4Ks6g0GDjIMV8MVvIB8EEArCCAARAFYAWEFQgCYQQDSIIB+EEAfCCAbhBALwgCqNgA4QBWAHhBUDqlXqNcrADIggCEQBWyQDiIM69ZrAIIgCtQlrVZsADCBAwCyIAarabnVrUIB2EGDgGYQJWAYRA42aDWafY7tPMQB9vDYEVQAB4oibxaBUWWwwCoID7M6gTc7UIBRED1zsA8iCoQCMILG9aqjXrE97A6qQ+HI4Gjc7g7IdcqFQnk2mza7UD7nUrg+bAGIgKdzh2hnyL2lLOSh5hhIzRLAxUDP1IgxLclQuxiP5H0hlUGFE9k+QQKAoHhaGQAB6cD+kQHh-Aodh8D+FhwMIHggSlasKHA8EOAgAFaHAgAmTkAEYABZwJIkjwNFfo2HwR5aFI7QACseG6I94kSAJ0jGTjyHJEYAEkAIACnYDgAF4AHIgJAsDIOghBYLAeD6KQlC0IwmUsJwvD1AI4jyMo6jaPoxjmLYhBpIASlQAAeESJHwABhPpaFobQABEAHkAHE0GkzprIAPhMSogA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                        },
                        {
                            'image': 'https://upload.wikimedia.org/wikipedia/commons/0/0e/Felis_silvestris_silvestris.jpg',
                            'result': np.nan,
                            'confidence': 0.0,
                            'overlap': 0,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB4JiueTScVwBEI2g4txyQR4WwQekaaGaID6CgghncIAA1nonrDaLsIBwKu8+LRiQB1ODqLyqADsAAZOdpOVUQFAIHV4Ks6g0GDjIMV8MVvIB8EEArCCAARAFYAWEFQgCYQQDSIIB+EEAfCCAbhBALwgCqNgA4QBWAHhBUDqlXqNcrADIggCEQBWyQDiIM69ZrAIIgCtQlrVZsADCBAwCyIAarabnVrUIB2EGDgGYQJWAYRA42aDWafY7tPMQB9vDYEVQAB4oibxaBUWWwwCoID7M6gTc7UIBRED1zsA8iCoQCMILG9aqjXrE97A6qQ+HI4Gjc7g7IdcqFQnk2mza7UD7nUrg+bAGIgKdzh2hnyL2lLOSh5hhIzRLAxUDP1IgxLclQuxiP5H0hlUGFE9k+QQKAoHhaGQAB6cDwQ4CAAW0Qg4FJahHjgHQIDYBBwIQ0llBuPhwMgahqAacDOVI-BwIAMSGW4AH1aDgDgcHwWgXjohimJYtjaG0AArHhuiPURyRGABJACAAp2A4ABeAByICQLAyDoNg35sLEFC0IwrDELgXDUIIiAiJIsjOQo6ikVoejGOY1i2HY2yuIcnj+IQOSAEpUAAOWgFQP2MIA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                        },
                    ],
                ),
                (
                    results_with_weights.worker_labels(),
                    [
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'label': 'dog',
                            'worker': 'john',
                            'worker_weight': 0.25,
                        },
                        {
                            'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                            'label': 'cat',
                            'worker': 'alice',
                            'worker_weight': 0.67,
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'label': 'dog',
                            'worker': 'alice',
                            'worker_weight': 0.67,
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'label': 'cat',
                            'worker': 'bob',
                            'worker_weight': 0.9,
                        },
                        {
                            'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                            'label': 'dog',
                            'worker': 'john',
                            'worker_weight': 0.25,
                        },
                    ],
                ),
            ):
                assert actual_df.reset_index(drop=True).to_dict('records') == expected_dict

    def test_classification_combined_classes_results(self, qq_task_spec: spec.PreparedTaskSpec):
        input_objects = [
            (
                objects.Audio(
                    url='https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f212dc2e-ceb0-47c8-8c35-e31a193010a3.wav'
                ),
                Question.NOISE,
            ),
            (
                objects.Audio(
                    url='https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav'
                ),
                Question.NOISE,
            ),
            (
                objects.Audio(
                    url='https://storage.yandexcloud.net/crowdom-public/examples/qq/data/eeb39fac-c35d-4258-afc2-1a2232f46150.wav'
                ),
                Question.INTONATION,
            ),
            (
                objects.Audio(
                    url='https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f6e240cd-50d3-4968-a39b-466bc31cafc5.wav'
                ),
                Question.INTONATION,
            ),
        ]
        bob, alice, john = (worker.Human(toloka.Assignment(user_id=user_id)) for user_id in ('bob', 'alice', 'john'))
        results = [
            (
                {Answer.NOISE__BAD: 0.7, Answer.NOISE__EXCELLENT: 0.3},
                [(Answer.NOISE__BAD, john), (Answer.NOISE__EXCELLENT, alice)],
            ),
            (
                {Answer.NOISE__POOR: 0.4, Answer.NOISE__FAIR: 0.3, Answer.NOISE__EXCELLENT: 0.3},
                [(Answer.NOISE__POOR, alice), (Answer.NOISE__FAIR, bob), (Answer.NOISE__EXCELLENT, john)],
            ),
            (None, []),
            (
                {Answer.INTONATION__BAD: 0.55, Answer.INTONATION__EXCELLENT: 0.45},
                [(Answer.INTONATION__BAD, bob), (Answer.INTONATION__EXCELLENT, john)],
            ),
        ]

        with mapping.DisableValidation():
            results_w = client.ClassificationResults(input_objects, results, qq_task_spec)
            for actual_df, expected_dict in (
                (
                    results_w.predict(),
                    [
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f212dc2e-ceb0-47c8-8c35-e31a193010a3.wav',  # noqa
                            'confidence': 0.7,
                            'overlap': 2,
                            'question': 'noise',
                            'result': 'bad',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav',  # noqa
                            'confidence': 0.4,
                            'overlap': 3,
                            'question': 'noise',
                            'result': 'poor',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/eeb39fac-c35d-4258-afc2-1a2232f46150.wav',  # noqa
                            'confidence': 0.0,
                            'overlap': 0,
                            'question': 'intonation',
                            'result': np.nan,
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f6e240cd-50d3-4968-a39b-466bc31cafc5.wav',  # noqa
                            'confidence': 0.55,
                            'overlap': 2,
                            'question': 'intonation',
                            'result': 'bad',
                        },
                    ],
                ),
                (
                    results_w.predict_proba(),
                    [
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f212dc2e-ceb0-47c8-8c35-e31a193010a3.wav',  # noqa
                            'overlap': 2,
                            'proba_bad': 0.7,
                            'proba_excellent': 0.3,
                            'proba_fair': 0.0,
                            'proba_poor': 0.0,
                            'question': 'noise',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav',  # noqa
                            'overlap': 3,
                            'proba_bad': 0.0,
                            'proba_excellent': 0.3,
                            'proba_fair': 0.3,
                            'proba_poor': 0.4,
                            'question': 'noise',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/eeb39fac-c35d-4258-afc2-1a2232f46150.wav',  # noqa
                            'overlap': 0,
                            'proba_bad': 0.0,
                            'proba_excellent': 0.0,
                            'proba_fair': 0.0,
                            'proba_poor': 0.0,
                            'question': 'intonation',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f6e240cd-50d3-4968-a39b-466bc31cafc5.wav',  # noqa
                            'overlap': 2,
                            'proba_bad': 0.55,
                            'proba_excellent': 0.45,
                            'proba_fair': 0.0,
                            'proba_poor': 0.0,
                            'question': 'intonation',
                        },
                    ],
                ),
                (
                    results_w.worker_labels(),
                    [
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f212dc2e-ceb0-47c8-8c35-e31a193010a3.wav',  # noqa
                            'label': 'bad',
                            'question': 'noise',
                            'worker': 'john',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f212dc2e-ceb0-47c8-8c35-e31a193010a3.wav',  # noqa
                            'label': 'excellent',
                            'question': 'noise',
                            'worker': 'alice',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav',  # noqa
                            'label': 'poor',
                            'question': 'noise',
                            'worker': 'alice',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav',  # noqa
                            'label': 'fair',
                            'question': 'noise',
                            'worker': 'bob',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav',  # noqa
                            'label': 'excellent',
                            'question': 'noise',
                            'worker': 'john',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f6e240cd-50d3-4968-a39b-466bc31cafc5.wav',  # noqa
                            'label': 'bad',
                            'question': 'intonation',
                            'worker': 'bob',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f6e240cd-50d3-4968-a39b-466bc31cafc5.wav',  # noqa
                            'label': 'excellent',
                            'question': 'intonation',
                            'worker': 'john',
                        },
                    ],
                ),
                (
                    results_w._add_task_previews(results_w.predict()),
                    [
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f212dc2e-ceb0-47c8-8c35-e31a193010a3.wav',  # noqa
                            'confidence': 0.7,
                            'overlap': 2,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY+LACZwI2ADSpsFAJ498IkOIF8AdHCg8WFbAF852HHw5wNFKVG4LlqlPPDRJN6Fp4c+i-OIBaGBYODkVjUxAlFTU8Ii0xSWkQE1QySCgqTPtyKjoGZmwMrMNnbEAkEEA+EEB+EEABEErAQRBZF2inNDMCQi1qPjYAa3EIQjsUuXS3SlscimT2kCgIOFonSOs+HP4hNQBHFnxaDxHI1rU1nT0DCJbHNQz3Wy18XYt6UZbBfBHSIugStQAqf7lBqAIRBaoBWEEA4iCABhBAHIgIIagHkQVCAbhBABwgqLRgAkQQC8IGjwagsYBhEEAPCCAaRBUGj0ZSGoAuEGhgDYQcF45ENNGAZhAcdCUdCAPyA5oOGJlXCdbq9AZDEapbD4DjLHJ3SbQaazFy6GZQARTECrTQbATCEW7faHQVRG4is66fSlGUW4VzJWHR7PeVXBQfL5pH6ZT6lOaA8rg2o4yqYyk4kGVLmAMRA0ciuahoUTACwgaPD1RD4NT0MAiiAg1ANckNFGoLnVNENaE4sPs8Mg8G00F8gW666OlxxLo9fqDYYeh1tFwfDgqNg6GCDk4i0fjyfGAC6x0tc27WksB2nq67YoQbAgLB4V3GUHuKucZBmagWSxWLjWBq2xr2Bx1K872GtFztH+HvvPKBXRYF5py9RVfn9HJKBoV40EKVw-WyEVADwQEFACYQcEQXNGc1zFXtJQHN4yEfS9sE2I05j4KBaEIfA2HNcR8BgMQOADH0QAotRqNo+icJ3L9NHOW1t0-dQhI1eitS4N5sAgHhDjgpgyHMDg9hvRZlgAfS0ngIAgBj22wHwACM5TUPSDJPMwLHUkVb20rSWLgQzIlM8yRWcwzUhU2z-3mTT8B0ky+HEc13JkuYQrC4ibLU-yHKCrT8AADzAOUOCgoyQAitRUvS0IsqMZcHyWPgTMymK0AoNg9j-NR4DlcQtDYUKpACfdD2PFISqFfz103X8O36vcDyPQc5QVMjEMA1U1A1aBtQvPUKHWaauJfU132G04JJ-UT-OdB4nhA91ZKicDpuKLLvlyWCClPP5UIwrD+LE9cCP7aUxkE1an0olweLo1yH2Y1j2N4Q1uJo4G3v878RPO3CHz2qg2Gkwd5MUh64rsuYFq1Q4dPyjKsrc8qPLmEnCuQnzcf8gmlqgYLQvCinIpcaKl1WMqKv8BgarqnbPIIDhmtapIOrG7rivqkUBqWIa+tiUauoOtQ53ohckYEkBNYnOApx6uW8PiQbB28FgEF0JSEJ8RRDwh7A+l0KqXFoMAD1CHC+FoPoAHUrGfNAAHYAAYw60MP7QWGx4DAJnbcem6XEAfBBs1TVB0LJapKhRHFmXxElUDqSpMNqQAZEEbORIWjLOGgJEkczRaEAkAWRAUXBJuowpQB2EGhdlaiJXuqSrCutDhlX4ioFKhuT5C5kAVBBSwxAvC0AURBKhBZFAEYQClKlTOtwyb9NW47rvmRBaE5CzCF+8H4e0UbIswRrNFYyJCfsuRjpp9Su1epDgsmpa2QEZgcAgH0NaxUjDtnID+ZwGBRASCkBrCgFAeC0GQAAemwQcAyfAED4C0IoaiTE0oQIkFoKA+AKDYM9kMQY1AAj6AqnAMA2DUp8GoN4fY2DtjbGwWsbBMAABMABGUR4gwCiPwAEdKJkw4BAACwhzAAADgCOosAABmAArAEfAOjxF8HEQATh0WHcRYc+A6K0IQPgOBzQmjfBeOYiVzRAz4vZQKLMYqRCsGoAAgigiAAAKdgHAAC8AByQQ6DME4LwTMVqRCSFkPypQ5qNC6EMMIEwlhLA2EcK4TwzKtB+GCOEWIyR0jZHyPwIolRajNHaP0YY4xpiLFWJsXYhxOAYkAEpUAAB4ADCEBqAmV0P4AAiq+F0AA5AA8gASQAMoAFE0AxMSjEgAfKMgA4p8eiAh-BBJhlrFZGzNk6QAEJBIACI7MSn4g5xgUhAA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                            'question': 'noise',
                            'result': 'bad',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/fc0f7dce-0d77-44ea-a7ba-abc698aa2103.wav',  # noqa
                            'confidence': 0.4,
                            'overlap': 3,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY+LACZwI2ADSpsFAJ498IkOIF8AdHCg8WFbAF852HHw5wNFKVG4LlqlPPDRJN6Fp4c+i-OIBaGBYODkVjUxAlFTU8Ii0xSWkQE1QySCgqTPtyKjoGZmwMrMNnbEAkEEA+EEB+EEABEErAQRBZF2inNDMCQi1qPjYAa3EIQjsUuXS3SlscimT2kCgIOFonSOs+HP4hNQBHFnxaDxHI1rU1nT0DCJbHNQz3Wy18XYt6UZbBfBHSIugStQAqf7lBqAIRBaoBWEEA4iCABhBAHIgIIagHkQVCAbhBABwgqLRgAkQQC8IGjwagsYBhEEAPCCAaRBUGj0ZSGoAuEGhgDYQcF45ENNGAZhAcdCUdCAPyA5oOGJlXCdbq9AZDEapbD4DjLHJ3SbQaazFy6GZQARTECrTQbATCEW7faHQVRG4is66fSlGUW4VzJWHR7PeVXBQfL5pH6ZT6lOaA8rg2o4yqYyk4kGVLmAMRA0ciuahoUTACwgaPD1RD4NT0MAiiAg1ANckNFGoLnVNENaE4sPs8Mg8G00F8gW666OlxxLo9fqDYYeh1tFwfDgqNg6GCDk4i0fjyfGAC6x0tc27WksB2nq67YoQbAgLB4V3GUHuKucZBmagWSxWLjWBq2xr2Bx1K872GtFztH+HvvPKBXRYF5py9RVfn9HJKBoV40EKVw-WyEVADwQEFACYQcEQXNGc1zFXtJQHN4yEfS9sE2I05j4KBaEIfA2HNcR8BgMQOADH0QAotRqNo+icJ3L9NHOW1t0-dQhI1eitS4N5sAgHhDjgpgyHMDg9hvRZlgAfS0ngIAgBj22wHwACM5TUPSDJPMwLHUkVb20rSWLgQzIlM8yRWcwzUhU2z-3mTT8B0ky+HEc13JkuYQrC4ibLU-yHKCrT8AADzAOUOCgoyQAitRUvS0IsqMZcHyWPgTMymK0AoNg9j-NR4DlcQtDYUKpACfdD2PFISqFfz103X8O36vcDyPQc5QVMjEMA1U1A1aBtQvPUKHWaauJfU132G04JJ-UT-OdB4nhA91ZKicDpuKLLvlyWCClPP5UIwrD+LE9cCP7aUxkE1an0olweLo1yH2Y1j2N4Q1uJo4G3v878RPO3CHz2qg2Gkwd5MUh64rsuYFq1Q4dPyjKsrc8qPLmEnCuQnzcf8gmlqgYLQvCinIpcaKl1WMqKv8BgarqnbPIIDhmtapIOrG7rivqkUBqWIa+tiUauoOtQ53ohckYEkBNYnOApx6uW8PiQbB28FgEF0JSEJ8RRDwh7A+l0KqXFoMAD1CHC+FoPoAHUrGfNAAHYAAYw60MP7QWGx4DAJnbcem6XEAfBBs1TVB0LJapKhRHFmXxElUDqSpMNqQAZEEbORIWjLOGgJEkczRaEAkAWRAUXBJuowpQB2EGhdlaiJXuqSrCutDhlX4ioFKhuT5C5kAVBBSwxAvC0AURBKhBZFAEYQClKlTOtwyb9NW47rvmRBaE5CzCF+8H4e0UbIswRrNFYyJCfsuRjpp9Su1epDgsmpa2QEZgcAgH0NaxUjDtnID+ZwGBRASCkBrCgFAeC0GQAAemwQcAyfAED4C0IoaiTE0oQIkFoKA+AKDYM9kMQY1AAj6AqnAMA2DUp8GoN4fY2DtjbGwWsbBMAwBhxgCHcQ6UAhh3ECHEOAQAAsij8B8ACHwEOIV1EmTAAANgAJwAA4+B8AAEwAEYw4AGYtCED4Dgc0Jo3wXjmIlc0QM+L2UCjpSyINsBWDUAAQRQRAAAFOwDgABeAA5IIdBmCcF4JmK1IhJCyH5Uoc1GhdCGGECYSwlgbCOFcJ4ZlWg-DBHCNEeIyR0jZHyKUSotRGitHlT0UYkxFjrG2PsdEgAlKgAAPAAYQgNQEyuh-AAEVXwugAHIAHkACSABlAAomgaJiVokAD4hkAHFPj0QEP4QJMMtaLNWWsnSAAFBZCyABKmzEo+P0mwXZxgUhAA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                            'question': 'noise',
                            'result': 'poor',
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/eeb39fac-c35d-4258-afc2-1a2232f46150.wav',  # noqa
                            'confidence': 0.0,
                            'overlap': 0,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY+LACZwI2ADSpsFAJ498IkOIF8AdHCg8WFbAF852HHw5wNFKVG4LlqlPPDRJN6Fp4c+i-OIBaGBYODkVjUxAlFTU8Ii0xSWkQE1QySCgqTPtyKjoGZmwMrMNnbEAkEEA+EEB+EEABEErAQRBZF2inNDMCQi1qPjYAa3EIQjsUuXS3SlscimT2kCgIOFonSOs+HP4hNQBHFnxaDxHI1rU1nT0DCJbHNQz3Wy18XYt6UZbBfBHSIugStQAqf7lBqAIRBaoBWEEA4iCABhBAHIgIIagHkQVCAbhBABwgqLRgAkQQC8IGjwagsYBhEEAPCCAaRBUGj0ZSGoAuEGhgDYQcF45ENNGAZhAcdCUdCAPyA5oOGJlXCdbq9AZDEapbD4DjLHJ3SbQaazFy6GZQARTECrTQbATCEW7faHQVRG4is66fSlGUW4VzJWHR7PeVXBQfL5pH6ZT6lOaA8rg2o4yqYyk4kGVLmAMRA0ciuahoUTACwgaPD1RD4NT0MAiiAg1ANckNFGoLnVNENaE4sPs8Mg8G00F8gW666OlxxLo9fqDYYeh1tFwfDgqNg6GCDk4i0fjyfGAC6x0tc27WksB2nq67YoQbAgLB4V3GUHuKucZBmagWSxWLjWBq2xr2Bx1K872GtFztH+HvvPKBXRYF5py9RVfn9HJKBoV40EKVw-WyEVADwQEFACYQcEQXNGc1zFXtJQHN4yEfS9sE2I05j4KBaEIfA2HNcR8BgMQOADH0QAotRqNo+icJ3L9NHOW1t0-dQhI1eitS4N5sAgHhDjgpgyHMDg9hvRZlgAfS0ngIAgBj22wHwACM5TUPSDJPMwLHUkVb20rSWLgQzIlM8yRWcwzUhU2z-3mTT8B0ky+HEc13JkuYQrC4ibLU-yHKCrT8AADzAOUOCgoyQAitRUvS0IsqMZcHyWPgTMymK0AoNg9j-NR4DlcQtDYUKpACfdD2PFISqFfz103X8O36vcDyPQc5QVMjEMA1U1A1aBtQvPUKHWaauJfU132G04JJ-UT-OdB4nhA91ZKicDpuKLLvlyWCClPP5UIwrD+LE9cCP7aUxkE1an0olweLo1yH2Y1j2N4Q1uJo4G3v878RPO3CHz2qg2Gkwd5MUh64rsuYFq1Q4dPyjKsrc8qPLmEnCuQnzcf8gmlqgYLQvCinIpcaKl1WMqKv8BgarqnbPIIDhmtapIOrG7rivqkUBqWIa+tiUauoOtQ53ohckYEkBNYnOApx6uW8PiQbB28FgEF0JSEJ8RRDwh7A+l0KqXFoMAD1CHC+FoPoAHUrGfNAAHYAAYw60MP7QWGx4DAJnbcem6XEAfBBs1TVB0LJapKhRHFmXxElUDqSpMNqQAZEEbORIWjLOGgJEkczRaEAkAWRAUXBJuowpQB2EGhdlaiJXuqSrCutDhlX4ioFKhuT5C5kAVBBSwxAvC0AURBKhBZFAEYQClKlTOtwyb9NW47rvmRBaE5CzCF+8H4e0UbIswRrNFYyJCfsuRjpp9Su1epDgsmpa2QEZgcAgH0NaxUjDtnID+ZwGBRASCkBrCgFAeC0GQAAemwQcAyfAED4C0IoaiTE0oQIkFoKA+AKDYM9kMQY1AAj6AqnAMA2DUp8GoN4fY2DtjbGwWsTh+ATIAGYACcLEwABDAGIgArIEAALAAJnkQADgCHwGAYAVEBAAIx8BUSosRKiYBKIAGz6PkZHQgfAcDmhNG+C8+NMiLTNNlKwagACCKCIAAAp2AcAALwAHJBDoMwTgvBMxWpEJIWQ-KlDmo0LoQwwgTCWEsDYRwrhPDMq0H4YI4R+BRGSOkbIhRyi1GaO0bogxRiTFmMsdY2x9jQkAEpUAAB4ADCEBqAmV0P4AAiq+F0ABJAAcgAFQAPJTO8TMiZCy0ChMZocUJAA+VAUzoBOFgUYIAA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                            'question': 'intonation',
                            'result': np.nan,
                        },
                        {
                            'audio': 'https://storage.yandexcloud.net/crowdom-public/examples/qq/data/f6e240cd-50d3-4968-a39b-466bc31cafc5.wav',  # noqa
                            'confidence': 0.55,
                            'overlap': 2,
                            'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY+LACZwI2ADSpsFAJ498IkOIF8AdHCg8WFbAF852HHw5wNFKVG4LlqlPPDRJN6Fp4c+i-OIBaGBYODkVjUxAlFTU8Ii0xSWkQE1QySCgqTPtyKjoGZmwMrMNnbEAkEEA+EEB+EEABEErAQRBZF2inNDMCQi1qPjYAa3EIQjsUuXS3SlscimT2kCgIOFonSOs+HP4hNQBHFnxaDxHI1rU1nT0DCJbHNQz3Wy18XYt6UZbBfBHSIugStQAqf7lBqAIRBaoBWEEA4iCABhBAHIgIIagHkQVCAbhBABwgqLRgAkQQC8IGjwagsYBhEEAPCCAaRBUGj0ZSGoAuEGhgDYQcF45ENNGAZhAcdCUdCAPyA5oOGJlXCdbq9AZDEapbD4DjLHJ3SbQaazFy6GZQARTECrTQbATCEW7faHQVRG4is66fSlGUW4VzJWHR7PeVXBQfL5pH6ZT6lOaA8rg2o4yqYyk4kGVLmAMRA0ciuahoUTACwgaPD1RD4NT0MAiiAg1ANckNFGoLnVNENaE4sPs8Mg8G00F8gW666OlxxLo9fqDYYeh1tFwfDgqNg6GCDk4i0fjyfGAC6x0tc27WksB2nq67YoQbAgLB4V3GUHuKucZBmagWSxWLjWBq2xr2Bx1K872GtFztH+HvvPKBXRYF5py9RVfn9HJKBoV40EKVw-WyEVADwQEFACYQcEQXNGc1zFXtJQHN4yEfS9sE2I05j4KBaEIfA2HNcR8BgMQOADH0QAotRqNo+icJ3L9NHOW1t0-dQhI1eitS4N5sAgHhDjgpgyHMDg9hvRZlgAfS0ngIAgBj22wHwACM5TUPSDJPMwLHUkVb20rSWLgQzIlM8yRWcwzUhU2z-3mTT8B0ky+HEc13JkuYQrC4ibLU-yHKCrT8AADzAOUOCgoyQAitRUvS0IsqMZcHyWPgTMymK0AoNg9j-NR4DlcQtDYUKpACfdD2PFISqFfz103X8O36vcDyPQc5QVMjEMA1U1A1aBtQvPUKHWaauJfU132G04JJ-UT-OdB4nhA91ZKicDpuKLLvlyWCClPP5UIwrD+LE9cCP7aUxkE1an0olweLo1yH2Y1j2N4Q1uJo4G3v878RPO3CHz2qg2Gkwd5MUh64rsuYFq1Q4dPyjKsrc8qPLmEnCuQnzcf8gmlqgYLQvCinIpcaKl1WMqKv8BgarqnbPIIDhmtapIOrG7rivqkUBqWIa+tiUauoOtQ53ohckYEkBNYnOApx6uW8PiQbB28FgEF0JSEJ8RRDwh7A+l0KqXFoMAD1CHC+FoPoAHUrGfNAAHYAAYw60MP7QWGx4DAJnbcem6XEAfBBs1TVB0LJapKhRHFmXxElUDqSpMNqQAZEEbORIWjLOGgJEkczRaEAkAWRAUXBJuowpQB2EGhdlaiJXuqSrCutDhlX4ioFKhuT5C5kAVBBSwxAvC0AURBKhBZFAEYQClKlTOtwyb9NW47rvmRBaE5CzCF+8H4e0UbIswRrNFYyJCfsuRjpp9Su1epDgsmpa2QEZgcAgH0NaxUjDtnID+ZwGBRASCkBrCgFAeC0GQAAemwQcAyfAED4C0IoaiTE0oQIkFoKA+AKDYM9kMQY1AAj6AqnAMA2DUp8GoN4fY2DtjbGwWsbBMAABs+AABMAAWMOYBAgAFYw7iAAMwBCkQATlEQADgCHwZR6iTJqNEaIkyYBlEAEYE4wDAPIrQhA+A4HNCaN8F58aZEWmabKQM+IikZkTLSXNspWDUAAQRQRAAAFOwDgABeAA5IIdBmCcF4JmK1IhJCyH5Uoc1GhdCGGECYSwlgbCOFcJ4ZlWg-DBHCLEZImRciAiKJUWozROi9EGKMSYsxli+DWNsfYnAcSACUqAAA8ABhCA1ATK6H8AARVfC6AAkgAOQACoAHlVkhPWcs7ZaA4l+NsHEgAfOMgA4p8eiAh-AhJhlrNZWydl7O2TpAAQiEgAIoc450AWbiDOcYFIQA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                            'question': 'intonation',
                            'result': 'bad',
                        },
                    ],
                ),
            ):
                assert actual_df.reset_index(drop=True).to_dict('records') == expected_dict

    def test_annotation_results(self, annotation_task_spec: spec.AnnotationTaskSpec):
        input_objects = [
            (objects.Image(url='https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg'),),
            (objects.Image(url='https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg'),),
        ]
        bob, alice, john, carl = (
            worker.Human(toloka.Assignment(user_id=user_id)) for user_id in ('bob', 'alice', 'john', 'carl')
        )
        false, true = base.BinaryEvaluation(ok=False), base.BinaryEvaluation(ok=True)
        results = [
            [
                feedback_loop.Solution(
                    solution=(Text(text='two dogs'),),
                    verdict=feedback_loop.SolutionVerdict.OK,
                    worker=bob,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=True,
                        confidence=0.9,
                        worker_labels=[(true, alice), (true, john)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),  # noqa
                feedback_loop.Solution(
                    solution=(Text(text='two dogs'),),
                    verdict=feedback_loop.SolutionVerdict.OK,
                    worker=carl,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=True,
                        confidence=0.9,
                        worker_labels=[(true, alice), (true, john)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),  # noqa
                feedback_loop.Solution(
                    solution=(None,),
                    verdict=feedback_loop.SolutionVerdict.BAD,
                    worker=alice,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=False,
                        confidence=0.1,
                        worker_labels=[(false, bob)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),  # noqa
            ],
            [
                feedback_loop.Solution(
                    solution=(Text(text='one cat'),),
                    verdict=feedback_loop.SolutionVerdict.OK,
                    worker=bob,
                    evaluation=None,
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                )
            ],
        ]
        worker_weights = {bob.id: 0.9, alice.id: 0.2, john.id: 0.8}

        results_w = client.AnnotationResults(input_objects, results, annotation_task_spec)
        results_with_weights = client.AnnotationResults(input_objects, results, annotation_task_spec, worker_weights)
        for actual_df, expected_dict in (
            (
                results_w.predict(),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'text': 'one cat',
                    },
                ],
            ),
            (
                results_w.predict_proba(),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'confidence': 0.9,
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': np.nan,
                        'confidence': 0.1,
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'text': 'one cat',
                        'confidence': np.nan,
                    },
                ],
            ),
            (
                results_w.worker_labels(),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'carl',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'carl',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': np.nan,
                        'annotation_overlap': 3,
                        'annotator': 'alice',
                        'confidence': 0.1,
                        'eval': False,
                        'evaluation_overlap': 1,
                        'evaluator': 'bob',
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'text': 'one cat',
                        'annotation_overlap': 1,
                        'annotator': 'bob',
                        'confidence': np.nan,
                        'eval': np.nan,
                        'evaluation_overlap': 0,
                        'evaluator': np.nan,
                    },
                ],
            ),
            (
                results_w._add_task_previews(results_w.predict()),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspChVX3bPyEiQVAB5GIGa+Fj6aFDp6BoGmaorKPjaE2v4xALrB8ZZqSdoccLQxwTwcLAh69KrM2Bx8ChCGHiAA1nrqPrRgbBAcXEFxfLTNAOpw6t6qAOwADNPa07HYUBAUcPBgAnDQlWjV4NBugVYggPgggKwggAIgZ4AsIKiATCCA0iCA-CCAfCCA3CCAvCBnH4AcIGeAPCCoJ4XF53S6AGRBAEIgZ1kgHEQSEve6AQRAzqh-jcfoAGEAAtIBZEDeAO+kIeqEA7CCYwDMIBdAMIgpJ+bx+SPB2hkcVCqmsBGSqUcqGcB3w7g5IEAqCBIhmoL6Q1CAURAXpDAPIgqEAjCAkl7XD4vCmI9HXLF4gnoj6QzGyJ6XM7kqm0n7Q1BIyEXTG-QBiINSWf1zAlhbkeSBjBk2d7jiUynoUj0IM0+CY0sZ+uR9IZVBhRPZsthBBQKDxaMgAPT5wh8Xr8ZRsTp8HD4bRsFj5sQSfC0fMQNiIPQl-MARgAHPnpgA2bF9-N8KCNji0bHqCAIacAVl7AE4AMyTbQAKx4CFZ8nwAR8FEIEFQs-ne-I7WFAEl0wAKdgcAC8AHIszm84Xi6W+OXK9Wtb1o2kgtm2HZQF2o5DiO-bjpO07nouK7rluO6vgAlKgAAqB4UPeqRvsep5IZhJj+kAA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'text': 'one cat',
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspChVX3bPyEiQVAB5GIGa+Fj6aFDp6BoGmaorKPjaE2v4xALrB8ZZqSdoccLQxwTwcLAh69KrM2Bx8ChCGHiAA1nrqPrRgbBAcXEFxfLTNAOpw6t6qAOwADNPa07HYUBAUcPBgAnDQlWjV4NBugVYggPgggKwggAIgZ4AsIKiATCCA0iCA-CCAfCCA3CCAvCBnH4AcIGeAPCCoJ4XF53S6AGRBAEIgZ1kgHEQSEve6AQRAzqh-jcfoAGEAAtIBZEDeAO+kIeqEA7CCYwDMIBdAMIgpJ+bx+SPB2hkcVCqmsBGSqUcqGcB3w7g5IEAqCBIhmoL6Q1CAURAXpDAPIgqEAjCAkl7XD4vCmI9HXLF4gnoj6QzGyJ6XM7kqm0n7Q1BIyEXTG-QBiINSWf1zAlhbkeSBjBk2d7jiUynoUj0IM0+CY0sZ+uR9IZVBhRPZsthBBQKDxaMgAPT5gBGiB4cDAFHY+G0bBY+cIPGxLkO+ZYJQgfHUtHzACZpgBGAAs+f7-fzGwoRbY+HwXYH2gAVjwEKz5PgAj5oPhUBPV+R2sKAJLpgAU7A4AF4AORZnN5wslhBlitVmt1htNgWuVvtzvdvtDiOY4TlOM5zv2i7LleACUqAACrrhQJ6pNeW47gIMEmP6QA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                ],
            ),
            (
                results_with_weights.worker_labels(),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'evaluator_weight': 0.2,
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'evaluator_weight': 0.8,
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'carl',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'evaluator_weight': 0.2,
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': 'two dogs',
                        'annotation_overlap': 3,
                        'annotator': 'carl',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'evaluator_weight': 0.8,
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'text': np.nan,
                        'annotation_overlap': 3,
                        'annotator': 'alice',
                        'confidence': 0.1,
                        'eval': False,
                        'evaluation_overlap': 1,
                        'evaluator': 'bob',
                        'evaluator_weight': 0.9,
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'text': 'one cat',
                        'annotation_overlap': 1,
                        'annotator': 'bob',
                        'confidence': np.nan,
                        'eval': np.nan,
                        'evaluation_overlap': 0,
                        'evaluator': np.nan,
                        'evaluator_weight': np.nan,
                    },
                ],
            ),
        ):
            # assert actual_df.reset_index(drop=True).to_dict('records') == expected_dict
            np.testing.assert_equal(actual_df.reset_index(drop=True).to_dict('records'), expected_dict)

    def test_image_annotation_results(self, image_annotation_task_spec: spec.AnnotationTaskSpec):
        input_objects = [
            (objects.Image(url='https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg'),),
            (objects.Image(url='https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg'),),
        ]
        bob, alice, john, carl = (
            worker.Human(toloka.Assignment(user_id=user_id)) for user_id in ('bob', 'alice', 'john', 'carl')
        )
        false, true = base.BinaryEvaluation(ok=False), base.BinaryEvaluation(ok=True)
        results = [
            [
                feedback_loop.Solution(
                    solution=(
                        base.ImageAnnotation(
                            [
                                {
                                    'shape': 'polygon',
                                    'points': [
                                        {'left': 0.3, 'top': 0.5},
                                        {'left': 0.4, 'top': 0.2},
                                        {'left': 0.8, 'top': 0.6},
                                    ],
                                }
                            ]
                        ),
                    ),
                    verdict=feedback_loop.SolutionVerdict.OK,
                    worker=bob,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=True,
                        confidence=0.9,
                        worker_labels=[(true, alice), (true, john)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),  # noqa
                feedback_loop.Solution(
                    solution=(
                        base.ImageAnnotation(
                            [
                                {
                                    'shape': 'polygon',
                                    'points': [
                                        {'left': 0.3, 'top': 0.5},
                                        {'left': 0.33, 'top': 0.45},
                                        {'left': 0.44, 'top': 0.23},
                                        {'left': 0.85, 'top': 0.66},
                                    ],
                                }
                            ]
                        ),
                    ),
                    verdict=feedback_loop.SolutionVerdict.OK,
                    worker=carl,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=True,
                        confidence=0.8,
                        worker_labels=[(true, alice), (true, john)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),  # noqa
            ],
            [
                feedback_loop.Solution(
                    solution=(
                        base.ImageAnnotation(
                            [
                                {
                                    'shape': 'polygon',
                                    'points': [
                                        {'left': 0.35, 'top': 0.55},
                                        {'left': 0.3, 'top': 0.4},
                                        {'left': 0.4, 'top': 0.2},
                                        {'left': 0.2, 'top': 0.4},
                                    ],
                                }
                            ]
                        ),
                    ),
                    verdict=feedback_loop.SolutionVerdict.OK,
                    worker=bob,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=True,
                        confidence=0.75,
                        worker_labels=[(true, alice), (false, john)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),
                feedback_loop.Solution(
                    solution=(base.ImageAnnotation([{'shape': 'point', 'left': 0.3, 'top': 0.5}]),),
                    verdict=feedback_loop.SolutionVerdict.BAD,
                    worker=carl,
                    evaluation=evaluation.SolutionEvaluation(
                        ok=False,
                        confidence=0.1,
                        worker_labels=[(false, alice), (false, john)],
                    ),
                    assignment_accuracy=None,  # noqa
                    assignment_evaluation_recall=None,  # noqa
                ),  # noqa
            ],
        ]
        worker_weights = {bob.id: 0.9, alice.id: 0.2, john.id: 0.8}

        annotation_1 = [
            {
                'points': [
                    {'left': Decimal(0.3), 'top': Decimal(0.5)},
                    {'left': Decimal(0.4), 'top': Decimal(0.2)},
                    {'left': Decimal(0.8), 'top': Decimal(0.6)},
                ],
                'shape': 'polygon',
            }
        ]
        annotation_2 = [
            {
                'points': [
                    {'left': Decimal(0.3), 'top': Decimal(0.5)},
                    {'left': Decimal(0.33), 'top': Decimal(0.45)},
                    {'left': Decimal(0.44), 'top': Decimal(0.23)},
                    {'left': Decimal(0.85), 'top': Decimal(0.66)},
                ],
                'shape': 'polygon',
            }
        ]

        annotation_3 = [
            {
                'points': [
                    {'left': Decimal(0.35), 'top': Decimal(0.55)},
                    {'left': Decimal(0.3), 'top': Decimal(0.4)},
                    {'left': Decimal(0.4), 'top': Decimal(0.2)},
                    {'left': Decimal(0.2), 'top': Decimal(0.4)},
                ],
                'shape': 'polygon',
            }
        ]

        annotation_4 = [{'left': Decimal(0.3), 'shape': 'point', 'top': Decimal(0.5)}]

        results_w = client.AnnotationResults(input_objects, results, image_annotation_task_spec)
        results_with_weights = client.AnnotationResults(
            input_objects, results, image_annotation_task_spec, worker_weights
        )
        for actual_df, expected_dict in (
            (
                results_w.predict(),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                    },
                ],
            ),
            (
                results_w.predict_proba(),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                        'confidence': 0.9,
                    },
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_2,
                        'confidence': 0.8,
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                        'confidence': 0.75,
                    },
                    {
                        'confidence': 0.1,
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_4,
                    },
                ],
            ),
            (
                results_w.worker_labels(),
                [
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.8,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_2,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.8,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_2,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.75,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.75,
                        'eval': False,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.1,
                        'eval': False,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_4,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.1,
                        'eval': False,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_4,
                    },
                ],
            ),
            (
                results_w._add_task_previews(results_w.predict()),
                [
                    {
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgEwEMK2GyAHDgCwbY41NgnwB9NlCgROFONGwAaVNhb4YbAK4AbCt2x8KglGvKjxUmXI6KoK8xQCePfEJDtOAOjhQe2gYgAL6q2C5uHl5svlBUAE5QbLrYoeYiYu5mvAIeGeKO4a5ZaOocMX4BQWnqcLRsAEa6+CwMFPHa+GEgMHq6ABL4iPxBaO2d3REl5vD4uiy+lvgAtNKy8vapALqTxR54RN66ddXdPLraCH70ZsxFkWZGF1dQ3rPzi5mrNhvQ3vxyADW+GcNzSZF0bGcEEChhAgL8rUeID44niqW66zg8DAdmgNzQd3A0CocQ8gHwQQCsIIABEEpgBYQVCAJhBANIggH4QQB8IIBuEEAvCCU7mADhBKYAeEFQrOp7MZNMAMiCAIRBKapAOIgMvZTMAgiCU1BC+n8wAMIMtALIgnOFfJlzNQgHYQHWAZhBqYBhEHN-M5-NVUu8hRAU32BEI3ioAA9TqgyJA4vgycjAKggqqdqF5MtQgFEQdkywDyIKhAIwgZvZdO57KtKq1dN1BqNWu5Mp1qlZNMplpt9v5ctQqpl1J1AsAYiC2t0gXYPUq4b2+-AB7Z96ZPS5+X0QXQQQFcEJbYK99CVQJmDDCJYeEYUHi0ZAAeiPhGSuj4bnitFxOHw3g6R-y+FoR4g8UQfmSR4AjAAOI8AAYADZln-I9pAyXRaGWFgIAQGCAFY-wATgAZgAdm8AArHgEHdZ9rHWPEHFuMhaH4Nh+3MHhZ2cBAlFXIwID8CgCSYCFNFGVBAO8NDJggHgGF4xDwWwZoYG43iABYBKEsxeIAJjEkAJKk7w-zk4TvGA4Jlx2dIkQHABJJYAAptHiXQAF4AHI9wPY9T3PS98GvW970fZ9X3fT8kl0X8AJAsCAMg0RoNg+CkNQzCcLw2yAEpUFMzIAEEfhIszoms5hbIoqj8FstBbNo3R6OgWzVBKli4loIqONstT6oAEXwMAoLM2zeLQwDer6vrEqqihBJatqOq67xEP66bEvBRquNG9rws6mTpv6wbUFs4aeEW8alLWgaErmpq0FapbkhWjSDt6jatpG06xuWibgOuwDZv0hLUhCIA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                    {
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgEwEMK2GyAHDgCwbY41NgnwB9NlCgROFONGwAaVNhb4YbAK4AbCt2x8KglGvKjxUmXI6KoK8xQCePfEJDtOAOjhQe2gYgAL6q2C5uHl5svlBUAE5QbLrYoeYiYu5mvAIeGeKO4a5ZaOocMX4BQWnqcLRsAEa6+CwMFPHa+GEgMHq6ABL4iPxBaO2d3REl5vD4uiy+lvgAtNKy8vapALqTxR54RN66ddXdPLraCH70ZsxFkWZGF1dQ3rPzi5mrNhvQ3vxyADW+GcNzSZF0bGcEEChhAgL8rUeID44niqW66zg8DAdmgNzQd3A0CocQ8gHwQQCsIIABEEpgBYQVCAJhBANIggH4QQB8IIBuEEAvCCU7mADhBKYAeEFQrOp7MZNMAMiCAIRBKapAOIgMvZTMAgiCU1BC+n8wAMIMtALIgnOFfJlzNQgHYQHWAZhBqYBhEHN-M5-NVUu8hRAU32BEI3ioAA9TqgyJA4vgycjAKggqqdqF5MtQgFEQdkywDyIKhAIwgZvZdO57KtKq1dN1BqNWu5Mp1qlZNMplpt9v5ctQqpl1J1AsAYiC2t0gXYPUq4b2+-AB7Z96ZPS5+X0QXQQQFcEJbYK99CVQJmDDCJYeEYUHi0ZAAeiPDUQPDgYAo2ni+G8HSPhB4yxDpIoR+05wgbBYtCPACYAAYAEYABYj2A4Cj1xCgGlvFpaBA7wACseAQd18kkNZbAUJRbjIWh+DYftzB4WdnAQPCzggPwKAJJgIU0UZUEA7wAGYAFZJggHgGFYjiOPBbBmhgZjWLY7jeLMVjQKEkARLE7xQMkvjvH-OSFNU-8VOkpTgmXHZ0iRAcAEklgAChvXQAF4AHI9wPY9T3PS9r1ve9tEfZ9XzDd9PznH8-yAsCIKgmC4PwBCkNQhBbIASlQMzMgAQR+PEoHM6JrOYWzCOI-BbLQWyyN0CjoFs1RipouJaEKhjbIUuqABF8DADJdHM2zxI4wDer63r4sqigeOa1r2s6-iev6vr4vBBqmNGtrRA6rr2Om-rBtQWzhp4RbxtW0D1pmuK5satAWqW5IJqUo6BrioaRvOsbluuoDbtm1RgHm0S9pe1a3qOzbtse1ALv2mTbsA2aDLi1IQiAA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                ],
            ),
            (
                results_with_weights.worker_labels(),
                [
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'evaluator_weight': 0.2,
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.9,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'evaluator_weight': 0.8,
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_1,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.8,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'evaluator_weight': 0.2,
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_2,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.8,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'evaluator_weight': 0.8,
                        'image': 'https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg',
                        'image_annotation': annotation_2,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.75,
                        'eval': True,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'evaluator_weight': 0.2,
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'bob',
                        'confidence': 0.75,
                        'eval': False,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'evaluator_weight': 0.8,
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_3,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.1,
                        'eval': False,
                        'evaluation_overlap': 2,
                        'evaluator': 'alice',
                        'evaluator_weight': 0.2,
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_4,
                    },
                    {
                        'annotation_overlap': 2,
                        'annotator': 'carl',
                        'confidence': 0.1,
                        'eval': False,
                        'evaluation_overlap': 2,
                        'evaluator': 'john',
                        'evaluator_weight': 0.8,
                        'image': 'https://bigpicture.ru/wp-content/uploads/2014/11/catbreeds01.jpg',
                        'image_annotation': annotation_4,
                    },
                ],
            ),
        ):
            assert actual_df.reset_index(drop=True).to_dict('records') == expected_dict

    def test_expert_classification_results(
        self,
        expert_solution_task_spec: spec.PreparedTaskSpec,
        expert_task_task_spec: spec.PreparedTaskSpec,
        results_task: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
        results_solution: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
    ):

        worker_ids = {'bob': '@bob', 'john': '@jonny', 'paul': '@paul'}
        results_task_w = client.ExpertLabelingResults(results_task, expert_task_task_spec)
        results_task_with_ids = client.ExpertLabelingResults(results_task, expert_task_task_spec, worker_ids)

        results_solution_w = client.ExpertLabelingResults(results_solution, expert_solution_task_spec)
        results_solution_with_ids = client.ExpertLabelingResults(
            results_solution, expert_solution_task_spec, worker_ids
        )
        basic_results = [
            {
                'image': 'https://storage.net/0.jpg',
                'choice': 'cat',
                '_ok': True,
                '_comment': '',
                'duration': pd.Timedelta(datetime.timedelta(seconds=30)),
            },
            {
                'image': 'https://storage.net/1.jpg',
                'choice': 'dog',
                '_ok': False,
                '_comment': 'may be cat',
                'duration': pd.Timedelta(datetime.timedelta(seconds=30)),
            },
            {
                'image': 'https://storage.net/2.jpg',
                'choice': 'cat',
                '_ok': True,
                '_comment': 'persian cat',
                'duration': pd.Timedelta(datetime.timedelta(seconds=60)),
            },
            {
                'image': 'https://storage.net/3.jpg',
                'choice': 'dog',
                '_ok': False,
                '_comment': 'not sure',
                'duration': pd.Timedelta(datetime.timedelta(seconds=60)),
            },
            {
                'image': 'https://storage.net/4.jpg',
                'choice': 'crow',
                '_ok': True,
                '_comment': 'may be pigeon',
                'duration': pd.Timedelta(datetime.timedelta(seconds=90)),
            },
            {
                'image': 'https://storage.net/5.jpg',
                'choice': 'crow',
                '_ok': True,
                '_comment': '',
                'duration': pd.Timedelta(datetime.timedelta(seconds=90)),
            },
        ]
        no_ids_results = [
            {**basic_result, 'worker': worker}
            for basic_result, worker in zip(basic_results, ['bob', 'bob', 'mary', 'mary', 'john', 'john'])
        ]
        ids_results = [
            {**basic_result, 'worker': worker}
            for basic_result, worker in zip(basic_results, ['@bob', '@bob', 'mary', 'mary', '@jonny', '@jonny'])
        ]
        for actual_df, expected_dict in (
            (results_task_w.get_results(), no_ids_results),
            (
                results_task_w._add_task_previews(results_task_w.get_results().take([0, 1])),
                [
                    {
                        **no_ids_results[0],
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB44zIkGK+GK3iBCPmIA+3hshG04jYAGtOoQoJD4tAqHCoqIqHQGM1wETYZERoAsEEAfCCAARBmYBWEEAXCCAIRBALwgjNQgG4QQAcIKhAOwggAYQQAsIOKeUK2agABQi9mACRA2bK2bJAPwgzJFPPFwsA4iBCoUASgA-EiUXFcAR0VQAB45DYaLTuECeWIjAD6ECxSPUITCEXdnu8vv9hzyaRtGSK2XG5hjIzjehKZQqVRANTqDUpk2mz1e+COAxONsAKCDigm4QuqUIcWgl3pl5bYQC4IGyuSYrh1bvdHkW3tHPt8OL9-oCQWCIZVe0nPmjtBxbs6R6i7dpQRBwTXocS6RMPDFw5BqNRaVb8rHCllDInkdeRkvHTl54-k2olyvaGuPFsED0Ro0CpPoFB3Q8yCxPQnhtWhdggDgKnePhaCxAB1OB1C8VQAHYAAZ8O0fCsygCA6ngVZcygYCmChGkSRGQB8EDZdlJVQQAmEEAaRAtUZAUeXVOVAB4QVAdUZDjWMAGRAuU1VBDS5fkOMAQRB5SEtlJSFcUgUAWRABTZNSeS5LixXFQBmEGZQBhEFFIVhSUyTtCvT9rE3V89wYw9sEAVBAlOFVABK5VBAFEQRkuUAeRBUEARhBjMZSU+VM-k1I0rTdP09UuXFbVWLZCVzKsoUZNQJSuWZGUhUAMRALIcqMFw3WxXLnd4nzUHgAL0bQKEQv03DnYwo3IfRDFUDBRHsT5BAoCgeFoZAAHoZt-CB-kkbQoHwCgZqIgArHhumqnw-ACHY1iCCMh2bbBvTPC9GLUJEsO8ABJUaFXYDgAF4AHJxsm6a5oWpb8BWtaNu0baEA+01UAAHieiR8AAYT6WhaG0eGAEEABU0A+qiPoAPlQAAhPQ+DYBQAFEpi2AR6igBU-TejHi0hjH8CdBVX0+iGTEqIA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                    {
                        **no_ids_results[1],
                        'worker': 'bob',
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB44zIkGK+GK3iBCPmIA+3hshG04jYAGtOoQoJD4tAqHCoqIqHQGM1wETYZERoAsEEAfCCAARBmYBWEEAXCCAIRBALwgjNQgG4QQAcIKhAOwggAYQQAsIOKeUK2agABQi9mACRA2bK2bJAPwgzJFPPFwsA4iBCoUASgA-EiUXFcAR0VQAB45DYaLTuECeWIjAD6ECxSPUITCEXdnu8vv9hzyaRtGSK2XG5hjIzjehKZQqVRANTqDUpk2mz1e+COAxONsAKCDigm4QuqUIcWgl3pl5bYQC4IGyuSYrh1bvdHkW3tHPt8OL9-oCQWCIZVe0nPmjtBxbs6R6i7dpQRBwTXocS6RMPDFw5BqNRaVb8rHCllDInkdeRkvHTl54-k2olyvaGuPFsED0Ro0CpPoFB3Q8yCxPQnhtWhdggDgKnePhaCxAB1OB1C8VQAHYAAZ8O0fCsygCA6ngVZcygYCmChGkSRGQB8EDZdlJVQQAmEEAaRAtUZAUeXVOVAB4QVAdUZDjWMAGRAuU1VBDS5fkOMAQRB5SEtlJSFcUgUAWRABTZNSeS5LixXFQBmEGZQBhEFFIVhSUyTtCvT9rE3V89wYw9sEAVBAlOFVABK5VBAFEQRkuUAeRBUEARhBjMZSU+VM-k1I0rTdP09UuXFbVWLZCVzKsoUZNQJSuWZGUhUAMRALIcqMFw3WxXLnd4nzUHgAL0bQKEQv03DnYwo3IfRDFUDBRHsT5BAoCgeFoZAAHoZt-CB-kkbQoHwCgZoARm0AArHhumqnw-ACdIxgOiMGAbJsgm9M8L0YtRxAUVBBlQKikSw7wAElRoVdgOAAXgAcnGybprmhalvwFa1s2na9sB01UAAHm+iR8AAYT6WhaG0AARAB5ABxNBAc6BBAYAPlQAAhPQ+DYBQAFEpi2AR6igBU-X+gAxcom0RgAVfAnQVV8gce578FegQEZMSogA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                ],
            ),
            (results_task_with_ids.get_results(), ids_results),
            (results_solution_w.get_results(), no_ids_results),
            (
                results_solution_w._add_task_previews(results_solution_w.get_results().take([0, 1])),
                [
                    {
                        **no_ids_results[0],
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB44zIkGK+GK3iBCPmIA+3hshG04jYAGtOoQoJD4tAqHCoqIqHQGM1wETYZERoAsEEAfCCAARBmYBWEEAXCCAIRBALwgjNQgG4QQAcIKhAOwggAYQQAsIOKeUK2agABQi9mACRA2bK2bJAPwgzJFPPFwsA4iBCoUASgA-EiUXFcAR0VQAB45DYaLTuECeWIjAD6ECxSPUITCEXdnu8vv9hzyaRtGSK2XG5hjIzjehKZQqVRANTqDUpk2mz1e+COAxONsAKCDigm4QuqUIcWgl3pl5bYQC4IGyuSYrh1bvdHkW3tHPt8OL9-oCQWCIZVe0nPmjtBxbs6R6i7dpQRBwTXocS6RMPDFw5BqNRaVb8rHCllDInkdeRkvHTl54-k2olyvaGuPFsED0Ro0CpPoFB3Q8yCxPQnhtWhdggDgKnePhaCxAB1OB1C8VQAHYAAZ8O0fCsygCA6ngVZcygYCmChGkSRGQB8EDZdlJVQQAmEEAaRAtUZAUeXVOVAB4QVAdUZDjWMAGRAuU1VBDS5fkOMAQRB5SEtlJSFcUgUAWRABTZNSeS5LixXFQBmEGZQBhEFFIVhSUyTtCvT9rE3V89wYw9sEAVBAlOFVABK5VBAFEQRkuUAeRBUEARhBjMZSU+VM-k1I0rTdP09UuXFbVWLZCVzKsoUZNQJSuWZGUhUAMRALIcqMFw3WxXLnd4nzUHgAL0bQKEQv03DnYwo3IfRDFUDBRHsT5BAoCgeFoZAAHoZt-CB-kkbQoHwCgZqIgArHhumqnw-ACHY1iCCMh2bbBvTPC9GLUJEsO8ABJUaFXYDgAF4AHJxsm6a5oWpb8BWtaNu0baEA+01UAAHieiR8AAYT6WhaG0eGAEEABU0A+qiPoAPlQAAhPQ+DYBQAFEpi2AR6igBU-TejHi0hjH8CdBVX0+iGTEqIA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                    {
                        **no_ids_results[1],
                        'preview': '<a href="https://tb.yandex.net/editor?config=N4Igxg9gdgZglgcxALgAQmAHRANzgUwHds0sQ4AXfAWwGcTUBtMgVwCcAbBsgBwEMKACwbY41PgnzYANKmwUAnjyko5IACYC+AOjhQeLCtgC+s+UpVpseIrvGSTsspop9u2fkJHhBEOGBUzDXwYPhYOI1VeAWFVbDBff0C1RWVvFx09A0jTFIt0rV0oKjYoPi4QXOwIHgo4aHpVZmtylks1dQgEGTUOPgAjfAqrDS7HVDIcVvb4gR7sPsHhtTA5yqcWjjbvMDYIYhAgxaGdvYPjAF0g9ThaAY58dQYKNjag1JmQeCH1bTY+G4QAC0CD2LB44zIkGK+GK3iBCPmIA+3hshG04jYAGtOoQoJD4tAqHCoqIqHQGM1wETYZERoAsEEAfCCAARBmYBWEEAXCCAIRBALwgjNQgG4QQAcIKhAOwggAYQQAsIOKeUK2agABQi9mACRA2bK2bJAPwgzJFPPFwsA4iBCoUASgA-EiUXFcAR0VQAB45DYaLTuECeWIjAD6ECxSPUITCEXdnu8vv9hzyaRtGSK2XG5hjIzjehKZQqVRANTqDUpk2mz1e+COAxONsAKCDigm4QuqUIcWgl3pl5bYQC4IGyuSYrh1bvdHkW3tHPt8OL9-oCQWCIZVe0nPmjtBxbs6R6i7dpQRBwTXocS6RMPDFw5BqNRaVb8rHCllDInkdeRkvHTl54-k2olyvaGuPFsED0Ro0CpPoFB3Q8yCxPQnhtWhdggDgKnePhaCxAB1OB1C8VQAHYAAZ8O0fCsygCA6ngVZcygYCmChGkSRGQB8EDZdlJVQQAmEEAaRAtUZAUeXVOVAB4QVAdUZDjWMAGRAuU1VBDS5fkOMAQRB5SEtlJSFcUgUAWRABTZNSeS5LixXFQBmEGZQBhEFFIVhSUyTtCvT9rE3V89wYw9sEAVBAlOFVABK5VBAFEQRkuUAeRBUEARhBjMZSU+VM-k1I0rTdP09UuXFbVWLZCVzKsoUZNQJSuWZGUhUAMRALIcqMFw3WxXLnd4nzUHgAL0bQKEQv03DnYwo3IfRDFUDBRHsT5BAoCgeFoZAAHoZt-CB-kkbQoHwCgZoARm0AArHhumqnw-ACdIxgOiMGAbJsgm9M8L0YtRxAUVBBlQKikSw7wAElRoVdgOAAXgAcnGybprmhalvwFa1s2na9sB01UAAHm+iR8AAYT6WhaG0AARAB5ABxNBAc6BBAYAPlQAAhPQ+DYBQAFEpi2AR6igBU-X+gAxcom0RgAVfAnQVV8gce578FegQEZMSogA" target="_blank" rel="noopener noreferrer">task preview</a>',  # noqa
                    },
                ],
            ),
            (results_solution_with_ids.get_results(), ids_results),
        ):
            assert actual_df.reset_index(drop=True).to_dict('records') == expected_dict

    def test_expert_classification_results_accuracy(
        self,
        expert_solution_task_spec: spec.PreparedTaskSpec,
        results_solution: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
    ):
        results_solution_w = client.ExpertLabelingResults(results_solution, expert_solution_task_spec)
        assert results_solution_w.get_accuracy() == 2 / 3

    def test_expert_classification_results_get_correct_objects(
        self,
        images: List[objects.Image],
        expert_solution_task_spec: spec.PreparedTaskSpec,
        results_solution: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
    ):
        cat, crow = lib.cat, lib.crow

        results_solution_w = client.ExpertLabelingResults(results_solution, expert_solution_task_spec)
        assert results_solution_w.get_correct_objects(application=client.ExpertLabelingApplication.CONTROL_TASKS) == (
            [((images[0],), (cat,)), ((images[2],), (cat,)), ((images[4],), (crow,)), ((images[5],), (crow,))],
            [Text(''), Text('persian cat'), Text('may be pigeon'), Text('')],
        )
        assert results_solution_w.get_correct_objects(application=client.ExpertLabelingApplication.TRAINING) == (
            [((images[2],), (cat,)), ((images[4],), (crow,))],
            [Text('persian cat'), Text('may be pigeon')],
        )

    def test_expert_annotation_results(
        self,
        images: List[objects.Image],
        expert_task_annotation_task_spec: spec.AnnotationTaskSpec,
        annotation_results_task: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
        annotation_results_solution: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
    ):
        results_task_w = client.ExpertLabelingResults(annotation_results_task, expert_task_annotation_task_spec)

        results_solution_w = client.ExpertLabelingResults(
            annotation_results_solution, expert_task_annotation_task_spec.check
        )

        basic_results = [
            {
                'image': 'https://storage.net/0.jpg',
                'text': '0',
                'eval': False,
                '_ok': False,
                '_comment': 'c-0',
                'duration': pd.Timedelta(datetime.timedelta(seconds=30)),
                'worker': 'bob',
            },
            {
                'image': 'https://storage.net/1.jpg',
                'text': '1',
                'eval': False,
                '_ok': True,
                '_comment': 'c-1',
                'duration': pd.Timedelta(datetime.timedelta(seconds=30)),
                'worker': 'bob',
            },
            {
                'image': 'https://storage.net/2.jpg',
                'text': '2',
                'eval': True,
                '_ok': False,
                '_comment': 'c-2',
                'duration': pd.Timedelta(datetime.timedelta(seconds=60)),
                'worker': 'mary',
            },
            {
                'image': 'https://storage.net/3.jpg',
                'text': '3',
                'eval': True,
                '_ok': True,
                '_comment': 'c-3',
                'duration': pd.Timedelta(datetime.timedelta(seconds=60)),
                'worker': 'mary',
            },
            {
                'image': 'https://storage.net/4.jpg',
                'text': '4',
                'eval': False,
                '_ok': False,
                '_comment': '',
                'duration': pd.Timedelta(datetime.timedelta(seconds=90)),
                'worker': 'john',
            },
            {
                'image': 'https://storage.net/5.jpg',
                'text': '5',
                'eval': False,
                '_ok': True,
                '_comment': '',
                'duration': pd.Timedelta(datetime.timedelta(seconds=90)),
                'worker': 'john',
            },
            {
                'image': 'https://storage.net/6.jpg',
                'text': '6',
                'eval': True,
                '_ok': False,
                '_comment': '',
                'duration': pd.Timedelta(datetime.timedelta(seconds=120)),
                'worker': 'cate',
            },
            {
                'image': 'https://storage.net/7.jpg',
                'text': '7',
                'eval': True,
                '_ok': True,
                '_comment': '',
                'duration': pd.Timedelta(datetime.timedelta(seconds=120)),
                'worker': 'cate',
            },
        ]
        assert results_task_w.get_results().reset_index(drop=True).to_dict('records') == basic_results
        assert results_solution_w.get_results().reset_index(drop=True).to_dict('records') == basic_results

    def test_expert_annotation_results_get_correct_objects(
        self,
        images: List[objects.Image],
        expert_task_annotation_task_spec: spec.AnnotationTaskSpec,
        annotation_results_task: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
        annotation_results_solution: List[Tuple[mapping.Objects, mapping.TaskMultipleSolutions]],
    ):
        true, false = base.BinaryEvaluation(ok=True), base.BinaryEvaluation(ok=False)

        results_task_w = client.ExpertLabelingResults(annotation_results_task, expert_task_annotation_task_spec)

        results_solution_w = client.ExpertLabelingResults(
            annotation_results_solution, expert_task_annotation_task_spec.check
        )

        control_tasks = (
            [
                ((images[1], Text('1')), (false,)),
                ((images[3], Text('3')), (true,)),
                ((images[5], Text('5')), (false,)),
                ((images[7], Text('7')), (true,)),
            ],
            [Text('c-1'), Text('c-3'), Text(''), Text('')],
        )

        check_training = (
            [((images[1], Text('1')), (false,)), ((images[3], Text('3')), (true,))],
            [Text('c-1'), Text('c-3')],
        )

        annotation_training = ([((images[3],), (Text('3'),))], [Text('c-3')])

        for application, expected_results in (
            (client.ExpertLabelingApplication.CONTROL_TASKS, control_tasks),
            (client.ExpertLabelingApplication.TRAINING, annotation_training),
            (client.ExpertLabelingApplication.ANNOTATION_CHECK_TRAINING, check_training),
        ):
            assert (
                results_task_w.get_correct_objects(application)
                == results_solution_w.get_correct_objects(application)
                == expected_results
            )

    def test_validation(self, task_spec: spec.PreparedTaskSpec):
        bob = worker.Human(toloka.Assignment(user_id='bob'))

        for input_objects, results, expected_err in (
            (
                [
                    (objects.Image(url='https://wallpaperscave.ru/images/original/18/06-18/animals-dogs-58937.jpg'),),
                ],
                [
                    (None, []),
                ],
                "expected type <enum 'ImageClass'>, got <class 'NoneType'>",
            ),
            (
                [
                    (objects.Text(text='hello'),),
                ],
                [
                    ({lib.cat: 1.0}, [(lib.cat, bob)]),
                ],
                "passed <class 'crowdom.objects.std.Text'> does not "
                "correspond to mapping <class 'crowdom.objects.std.Image'>",
            ),
        ):
            with pytest.raises(AssertionError) as e:
                results = client.ClassificationResults(input_objects, results, task_spec)
                results.html_with_task_previews(results.predict())
            assert str(e.value) == expected_err
