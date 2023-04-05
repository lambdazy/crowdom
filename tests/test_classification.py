from collections import defaultdict

from pytest import approx
import toloka.client as toloka

from crowdom import classification, objects, worker
from . import lib

bob, alice, john, mary = (
    worker.Human(toloka.Assignment(user_id=user_id)) for user_id in ('bob', 'alice', 'john', 'mary')
)


def test_label_prediction_empty_labels():
    # it should not raise any Exceptions
    for aggregation_algorithm in list(classification.AggregationAlgorithm):
        assert classification.predict_labels_probas_for_class(
            labels=[[], []], aggregation_algorithm=aggregation_algorithm, worker_weights_and_classes=({}, [])
        ) == [None, None]


def test_label_prediction():
    cat, dog = lib.cat, lib.dog

    expected = [None, {cat: 1 / 3, dog: 2 / 3}, {cat: 1, dog: 0}]
    actual = classification.predict_labels_probas(
        labels=[
            [],
            [
                (dog, bob),
                (dog, alice),
                (cat, john),
            ],
            [
                (cat, john),
                (cat, bob),
                (cat, alice),
            ],
        ],
        aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
        task_mapping=lib.image_classification_mapping,
    )
    assert actual == expected


def test_label_prediction_with_same_weights():
    cat, dog, crow = lib.ImageClass.possible_instances()

    expected = [
        None,
        {cat: approx(2 / 7), dog: approx(4 / 7), crow: approx(1 / 7)},
        {cat: approx(8 / 10), dog: approx(1 / 10), crow: approx(1 / 10)},
    ]
    actual = classification.predict_labels_probas(
        labels=[
            [],
            [
                (dog, bob),
                (dog, alice),
                (cat, john),
            ],
            [
                (cat, john),
                (cat, bob),
                (cat, alice),
            ],
        ],
        aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
        task_mapping=lib.image_classification_mapping,
        worker_weights=defaultdict(lambda: 0.5),
    )
    assert actual == expected


def test_label_prediction_with_different_weights():
    cat, dog, crow = lib.ImageClass.possible_instances()

    expected = [
        {cat: approx(486 / 521), dog: approx(8 / 521), crow: approx(27 / 521)},
        {cat: approx(648 / 681), dog: approx(6 / 681), crow: approx(27 / 681)},
    ]
    actual = classification.predict_labels_probas(
        labels=[
            [
                (dog, bob),
                (dog, john),
                (cat, alice),
            ],
            [
                (dog, bob),
                (cat, john),
                (cat, alice),
            ],
        ],
        aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
        task_mapping=lib.image_classification_mapping,
        worker_weights={bob.id: 0.1, alice.id: 0.9, john.id: 0.4},
    )
    assert actual == expected


def test_combined_class_label_prediction():
    dictor_same, dictor_different, dictor_other, noise_yes, noise_no = lib.Answer.possible_instances()

    expected = [
        {dictor_different: approx(3 / 19), dictor_other: approx(4 / 19), dictor_same: approx(12 / 19)},
        {noise_no: approx(0.4), noise_yes: approx(0.6)},
    ]
    actual = classification.predict_labels_probas(
        labels=[
            [
                (dictor_same, bob),
                (dictor_other, john),
                (dictor_same, alice),
            ],
            [
                (noise_yes, bob),
                (noise_no, john),
                (noise_yes, alice),
            ],
        ],
        aggregation_algorithm=classification.AggregationAlgorithm.MAX_LIKELIHOOD,
        task_mapping=lib.question_answer_mapping,
        worker_weights={bob.id: 0.1, alice.id: 0.9, john.id: 0.4},
    )
    assert actual == expected


def test_most_probable_label():
    cat, dog, crow = lib.cat, lib.dog, lib.crow
    assert classification.get_most_probable_label({cat: 0.1, dog: 0.5, crow: 0.4}) == (dog, 0.5)
    assert classification.get_most_probable_label(None) is None


# TODO: test Class-valued rows in df with Dawid Skene crowdkit implementation
def test_labels_probas_from_assignments():
    images = [objects.Image(url=f'https://storage.net/{i + 1}.jpg') for i in range(5)]
    control_image = objects.Image(url='https://storage.net/42.jpg')
    cat, dog, crow = lib.cat, lib.dog, lib.crow
    image_class_controls = [(control_image, cat)]

    bob_a, john_a, mary_a, alice_a = (
        lib.create_classification_assignment(image_class_pairs, image_class_controls, user_id=user_id)[0]
        for image_class_pairs, user_id in (
            ([(images[4], dog), (images[0], cat), (control_image, dog), (images[2], cat), (images[1], cat)], 'bob'),
            ([(images[2], dog), (images[1], cat), (images[4], dog), (images[3], crow)], 'john'),
            ([(images[0], cat), (images[2], crow), (images[4], crow), (images[1], cat)], 'mary'),
            ([(control_image, cat), (images[3], dog), (images[1], cat), (images[0], dog)], 'alice'),
        )
    )

    bob_, john_, mary_, alice_ = (worker.Human(assignment) for assignment in (bob_a, john_a, mary_a, alice_a))

    expected = [
        ({dog: 1 / 3, cat: 2 / 3, crow: 0.0}, [(cat, bob_), (cat, mary_), (dog, alice_)]),
        ({dog: 0.0, cat: 4 / 4, crow: 0.0}, [(cat, bob_), (cat, john_), (cat, mary_), (cat, alice_)]),
        ({dog: 1 / 3, cat: 1 / 3, crow: 1 / 3}, [(cat, bob_), (dog, john_), (crow, mary_)]),
        ({dog: 1 / 2, cat: 0.0, crow: 1 / 2}, [(crow, john_), (dog, alice_)]),
        ({dog: 2 / 3, cat: 0.0, crow: 1 / 3}, [(dog, bob_), (dog, john_), (crow, mary_)]),
    ]

    assert (
        classification.collect_labels_probas_from_assignments(
            assignments=[bob_a, john_a, mary_a, alice_a],
            task_mapping=lib.image_classification_mapping,
            pool_input_objects=[(image,) for image in images],
            aggregation_algorithm=classification.AggregationAlgorithm.MAJORITY_VOTE,
        )
        == expected
    )
