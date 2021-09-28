from collections import defaultdict
from typing import Dict


class DependencyVector:
    def __init__(self, id: int) -> None:
        self.id = id
        self.dict: Dict[int, int] = defaultdict(int)

    def on_checkpoint_taken(self):
        self.dict[self.id] += 1

    def merge(self, dependency_vector: Dict[int, int]):
        if type(dependency_vector) != dict:
            raise Exception("Merging invalid dependency vector: not a dict")
        for key in dependency_vector:
            if type(key) != int:
                raise Exception("Mergin invalid dependency vector: key not int", key)
            if type(dependency_vector[key]) != int:
                raise Exception(
                    "Mergin invalid dependency vector: value not int",
                    dependency_vector[key],
                )
            self.dict[key] = max(self.dict[key], dependency_vector[key])

    def as_dict(self) -> Dict[int, int]:
        return dict(self.dict)

    def get(self, i: int) -> int:
        return self.dict[i]