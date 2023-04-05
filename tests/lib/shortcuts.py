import datetime
from typing import List, Optional, Tuple, Dict

import toloka.client as toloka

from crowdom import base, classification_loop, evaluation, mapping, objects, params, pricing, worker
from .objects import (
    audio_transcript_mapping,
    audio_transcript_check_mapping,
    image_classification_mapping,
    image_classification_expert_task_mapping,
    image_classification_expert_solution_mapping,
    audio_transcription_expert_task_mapping,
    audio_transcription_expert_solution_mapping,
)


def generate_evaluations(
    evaluations: List[Tuple[str, str, bool]]
) -> Dict[mapping.TaskID, evaluation.SolutionEvaluation]:
    return {
        audio_transcript_check_mapping.task_id(
            (objects.Audio(url=url), objects.Text(text=text))
        ): evaluation.SolutionEvaluation(
            ok=ok, confidence=None, worker_labels=[]
        )  # noqa
        for url, text, ok in evaluations
    }


def create_markup_assignment(
    audio_text_pairs: List[Tuple[objects.Audio, objects.Text]],
    id: str = 'fake',
    status: toloka.Assignment.Status = toloka.Assignment.SUBMITTED,
    user_id: str = 'fake',
    duration: datetime.timedelta = datetime.timedelta(seconds=0),
) -> mapping.AssignmentSolutions:
    tasks = []
    solutions = []
    created = datetime.datetime(year=2020, month=11, day=5)
    for audio, text in audio_text_pairs:
        tasks.append(audio_transcript_mapping.to_task((audio,)))
        solutions.append(audio_transcript_mapping.to_solution((text,)))
    return toloka.Assignment(
        id=id,
        tasks=tasks,
        solutions=solutions,
        status=status,
        user_id=user_id,
        created=created,
        submitted=created + duration,
    ), [((audio,), (text,)) for audio, text in audio_text_pairs]


def create_check_assignment(
    pool_input_objects: List[mapping.Objects],
    task_solutions: List[Tuple[Optional[int], bool]],
    worker_id: Optional[str] = None,
) -> toloka.Assignment:
    tasks = []
    solutions = []
    for input_objects_index, ok in task_solutions:
        if input_objects_index is None:
            tasks.append(
                toloka.Task(
                    input_values={'audio_link': 'https://storage.net/8.wav', 'output': 'seventeen'},
                    known_solutions=[toloka.Task.KnownSolution(output_values={'ok': True})],
                )
            )
        else:
            tasks.append(audio_transcript_check_mapping.to_task(pool_input_objects[input_objects_index]))
        solutions.append(audio_transcript_check_mapping.to_solution((base.BinaryEvaluation(ok=ok),)))
    return toloka.Assignment(tasks=tasks, solutions=solutions, user_id=worker_id)


def create_classification_assignment(
    image_class_solutions: List[Tuple[objects.Image, base.Class]],
    image_class_controls: List[Tuple[objects.Image, base.Class]],
    id: str = 'fake',
    user_id: str = 'fake',
    duration: datetime.timedelta = datetime.timedelta(seconds=40),
    assignment_start: datetime.datetime = datetime.datetime(year=2020, month=10, day=5, hour=10, minute=10),
    pool_id: Optional[str] = None,
    status: Optional[toloka.Assignment.Status] = None,
) -> mapping.AssignmentSolutions:
    task_id_to_control_class = {
        image_classification_mapping.task_id((image,)): cls for image, cls in image_class_controls
    }
    tasks = []
    solutions = []
    for image, cls in image_class_solutions:
        control_cls = task_id_to_control_class.get(image_classification_mapping.task_id((image,)))
        if control_cls:
            task = image_classification_mapping.to_control_task(((image,), (control_cls,)))
        else:
            task = image_classification_mapping.to_task((image,))
        solution = image_classification_mapping.to_solution((cls,))
        tasks.append(task)
        solutions.append(solution)
    return toloka.Assignment(
        id=id,
        status=status,
        tasks=tasks,
        solutions=solutions,
        user_id=user_id,
        created=assignment_start,
        submitted=assignment_start + duration,
        pool_id=pool_id,
    ), [((image,), (cls,)) for image, cls in image_class_solutions]


def create_expert_classification_assignment(
    expert_solutions: List[Tuple[objects.Image, base.Class, base.BinaryEvaluation, objects.Text]],
    task_annotation: bool = True,
    id: str = 'fake',
    user_id: str = 'fake',
    pool_id: Optional[str] = None,
) -> mapping.AssignmentSolutions:
    task_mapping = (
        image_classification_expert_task_mapping if task_annotation else image_classification_expert_solution_mapping
    )
    tasks = []
    solutions = []
    inputs = []
    outputs = []
    for image, cls, ok, comment in expert_solutions:
        input_objects = (image,) if task_annotation else (image, cls)
        output_objects = (cls, ok, comment) if task_annotation else (ok, comment)
        inputs.append(input_objects)
        outputs.append(output_objects)
        task = task_mapping.to_task(input_objects)
        solution = task_mapping.to_solution(output_objects)
        tasks.append(task)
        solutions.append(solution)
    return toloka.Assignment(
        id=id, status=toloka.Assignment.ACCEPTED, tasks=tasks, solutions=solutions, user_id=user_id, pool_id=pool_id
    ), [(input, output) for input, output in zip(inputs, outputs)]


def create_expert_annotation_assignment(
    expert_solutions: List[
        Tuple[objects.Audio, objects.Text, base.BinaryEvaluation, base.BinaryEvaluation, objects.Text]
    ],
    task_annotation: bool = True,
    id: str = 'fake',
    user_id: str = 'fake',
    pool_id: Optional[str] = None,
) -> mapping.AssignmentSolutions:
    task_mapping = (
        audio_transcription_expert_task_mapping if task_annotation else audio_transcription_expert_solution_mapping
    )
    tasks = []
    solutions = []
    inputs = []
    outputs = []
    for audio, text, eval, ok, comment in expert_solutions:
        input_objects = (audio,) if task_annotation else (audio, text)
        output_objects = (text, eval, ok, comment) if task_annotation else (eval, ok, comment)
        inputs.append(input_objects)
        outputs.append(output_objects)
        task = task_mapping.to_task(input_objects)
        solution = task_mapping.to_solution(output_objects)
        tasks.append(task)
        solutions.append(solution)
    return toloka.Assignment(
        id=id, status=toloka.Assignment.ACCEPTED, tasks=tasks, solutions=solutions, user_id=user_id, pool_id=pool_id
    ), [(input, output) for input, output in zip(inputs, outputs)]


def get_params(seconds: int = 6, training_score: Optional[int] = None) -> params.Params:
    return params.Params(
        worker_filter=worker.WorkerFilter(
            filters=[],
            training_score=training_score,
        ),
        task_duration_hint=datetime.timedelta(seconds=seconds),
        pricing_config=pricing.PoolPricingConfig(
            real_tasks_count=None,  # noqa
            control_tasks_count=None,  # noqa
            assignment_price=None,  # noqa
        ),
        aggregation_algorithm=None,  # noqa
        overlap=classification_loop.StaticOverlap(overlap=None),  # noqa
        control=None,  # noqa
    )
