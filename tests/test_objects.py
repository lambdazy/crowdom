from typing import Dict

from crowdom import base, objects


def test_question_answers():
    class Dictor(objects.Question):
        SAME = 'same'
        DIFFERENT = 'different'
        OTHER = 'other'

        @classmethod
        def question_label(cls) -> Dict[str, str]:
            return {'EN': 'Is dictor the same for both audios?', 'RU': 'На записях звучит один и тот же голос?'}

        @classmethod
        def labels(cls) -> Dict['Dictor', Dict[str, str]]:
            return {
                cls.SAME: {'EN': 'same', 'RU': 'одинаковые'},
                cls.DIFFERENT: {'EN': 'different', 'RU': 'разные'},
                cls.OTHER: {'EN': 'other', 'RU': 'другое'},
            }

    class Noise(objects.Question):
        YES = 'yes'
        NO = 'no'

        @classmethod
        def question_label(cls) -> Dict[str, str]:
            return {'EN': 'Is there any noise in the audio?', 'RU': 'На записи присутствует шум?'}

    Question, Answer, question_answers = objects.get_combined_classes([Dictor, Noise])
    assert issubclass(Answer, objects.CombinedAnswer)
    assert issubclass(Answer, base.Class)

    assert len(Answer) == 5
    assert {answer.name: answer.value for answer in Answer} == {
        'DICTOR__DIFFERENT': 'dictor__different',
        'DICTOR__OTHER': 'dictor__other',
        'DICTOR__SAME': 'dictor__same',
        'NOISE__NO': 'noise__no',
        'NOISE__YES': 'noise__yes',
    }
    assert Answer.labels() == {
        Answer.DICTOR__DIFFERENT: {'EN': 'different', 'RU': 'разные'},
        Answer.DICTOR__OTHER: {'EN': 'other', 'RU': 'другое'},
        Answer.DICTOR__SAME: {'EN': 'same', 'RU': 'одинаковые'},
        Answer.NOISE__NO: {'EN': 'no'},
        Answer.NOISE__YES: {'EN': 'yes'},
    }

    assert Answer.DICTOR__DIFFERENT.get_original_answer() == Dictor.DIFFERENT
    assert Answer.DICTOR__OTHER.get_original_answer() == Dictor.OTHER
    assert Answer.DICTOR__SAME.get_original_answer() == Dictor.SAME
    assert Answer.NOISE__NO.get_original_answer() == Noise.NO
    assert Answer.NOISE__YES.get_original_answer() == Noise.YES

    assert issubclass(Question, base.Class)

    assert len(Question) == 2
    assert {Question.name: Question.value for Question in Question} == {
        'DICTOR': 'dictor',
        'NOISE': 'noise',
    }
    assert Question.labels() == {
        Question.DICTOR: {'EN': 'Is dictor the same for both audios?', 'RU': 'На записях звучит один и тот же голос?'},
        Question.NOISE: {'EN': 'Is there any noise in the audio?', 'RU': 'На записи присутствует шум?'},
    }

    assert question_answers == [
        (Question.DICTOR, [Answer.DICTOR__SAME, Answer.DICTOR__DIFFERENT, Answer.DICTOR__OTHER]),
        (Question.NOISE, [Answer.NOISE__YES, Answer.NOISE__NO]),
    ]
