from dataclasses import dataclass
from typing import Dict

from crowdom import base, mapping, objects


@dataclass
class MOS(base.Object):
    mos: float


@dataclass
class Score(base.Object):
    score: int


class AudioClass(base.Class):
    SILENCE = 'sil'
    SPEECH = 'sp'


class ImageClass(base.Class):
    DOG = 'dog'
    CAT = 'cat'
    CROW = 'crow'


class Dictor(objects.Question):
    SAME = 'same'
    DIFFERENT = 'different'
    OTHER = 'other'

    @classmethod
    def question_label(cls) -> Dict[str, str]:
        return {'EN': 'Is dictor the same for both audios?'}


class Noise(objects.Question):
    YES = 'yes'
    NO = 'no'

    @classmethod
    def question_label(cls) -> Dict[str, str]:
        return {'EN': 'Is there any noise in the audio?'}


Question, Answer, question_answers_list = objects.get_combined_classes([Dictor, Noise])

sil, sp = AudioClass.SILENCE, AudioClass.SPEECH
dog, cat, crow = ImageClass.DOG, ImageClass.CAT, ImageClass.CROW
ok, bad = base.BinaryEvaluation(True), base.BinaryEvaluation(False)

audio_mapping = mapping.ObjectMapping(obj_meta=base.ObjectMeta(objects.Audio), obj_task_fields=(('url', 'audio_link'),))

text_mapping = mapping.ObjectMapping(
    obj_meta=base.ObjectMeta(objects.Text, required=False), obj_task_fields=(('text', 'output'),)
)

image_mapping = mapping.ObjectMapping(obj_meta=base.ObjectMeta(objects.Image), obj_task_fields=(('url', 'image_url'),))

# doesn't contain all correct properties - e.g. title, title format, etc. they are not needed for current tests
question_mapping = mapping.ObjectMapping(obj_meta=base.ClassMeta(Question), obj_task_fields=(('value', 'question'),))
answer_mapping = mapping.ObjectMapping(obj_meta=base.ClassMeta(Answer), obj_task_fields=(('value', 'answer'),))

mos_mapping = mapping.ObjectMapping(obj_meta=base.ObjectMeta(MOS), obj_task_fields=(('mos', 'mos'),))

score_mapping = mapping.ObjectMapping(obj_meta=base.ObjectMeta(Score), obj_task_fields=(('score', 'score'),))

metadata_mapping = mapping.ObjectMapping(
    obj_meta=base.ObjectMeta(base.Metadata), obj_task_fields=(('metadata', 'extra'),)
)

audio_class_mapping = mapping.ObjectMapping(
    obj_meta=base.ObjectMeta(AudioClass), obj_task_fields=((base.CLASS_OBJ_FIELD, base.CLASS_TASK_FIELD),)
)

image_class_mapping = mapping.ObjectMapping(
    obj_meta=base.ObjectMeta(ImageClass), obj_task_fields=((base.CLASS_OBJ_FIELD, base.CLASS_TASK_FIELD),)
)

binary_evaluation_mapping = mapping.ObjectMapping(
    obj_meta=base.ObjectMeta(base.BinaryEvaluation), obj_task_fields=(('ok', 'ok'),)
)

audio_transcript_mapping, audio_transcript_check_mapping = mapping.generate_feedback_loop_mapping(
    input_objects_mapping=(audio_mapping,),
    markup_objects_mapping=(text_mapping,),
    check_objects_mapping=(binary_evaluation_mapping,),
)

audio_transcript_ext_mapping = mapping.TaskMapping(
    input_mapping=(audio_mapping,), output_mapping=(text_mapping, audio_class_mapping)
)

image_classification_mapping = mapping.TaskMapping(
    input_mapping=(image_mapping,), output_mapping=(image_class_mapping,)
)

comment_mapping = mapping.ObjectMapping(
    obj_meta=base.ObjectMeta(objects.Text, required=False), obj_task_fields=(('text', '_comment'),)
)

ok_mapping = mapping.ObjectMapping(obj_meta=base.ObjectMeta(base.BinaryEvaluation), obj_task_fields=(('ok', '_ok'),))

eval_mapping = mapping.ObjectMapping(obj_meta=base.ObjectMeta(base.BinaryEvaluation), obj_task_fields=(('ok', 'eval'),))

image_classification_expert_task_mapping = mapping.TaskMapping(
    input_mapping=(image_mapping,), output_mapping=(image_class_mapping, ok_mapping, comment_mapping)
)

image_classification_expert_solution_mapping = mapping.TaskMapping(
    input_mapping=(image_mapping, image_class_mapping), output_mapping=(ok_mapping, comment_mapping)
)

audio_transcription_expert_task_mapping = mapping.TaskMapping(
    input_mapping=(audio_mapping,), output_mapping=(text_mapping, eval_mapping, ok_mapping, comment_mapping)
)

audio_transcription_expert_solution_mapping = mapping.TaskMapping(
    input_mapping=(audio_mapping, text_mapping), output_mapping=(eval_mapping, ok_mapping, comment_mapping)
)

question_answer_mapping = mapping.TaskMapping(input_mapping=(question_mapping,), output_mapping=(answer_mapping,))
