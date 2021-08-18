from collections import defaultdict
from typing import Dict


class DependencyVector:
    def __init__(self, id: int) -> None:
        self.id = id
        self.dict: Dict[int, int] = defaultdict(int)

    def on_checkpoint_taken(self):
        self.dict[self.id] += 1

    def merge(self, dependency_vector: Dict[int, int]):
        for key in dependency_vector:
            self.dict[key] = max(self.dict[key], dependency_vector[key])

    def as_dict(self) -> Dict[int, int]:
        return dict(self.dict)
