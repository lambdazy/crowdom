import json
from random import choice
from typing import Optional, List

from .. import mapping


def get_swaps(name: Optional[str], input_objects: List[mapping.Objects]) -> List[bool]:
    if name is not None:
        try:
            with open(f'{name}-swaps.json', 'r') as file:
                return json.load(file)
        except (TypeError, FileNotFoundError, KeyError, ValueError):
            pass
    swaps = [choice((True, False)) for _ in input_objects]

    if name is not None:
        with open(f'{name}-swaps.json', 'w') as file:
            json.dump(swaps, file)

    return swaps
