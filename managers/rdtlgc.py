from collections import defaultdict
from dataclasses import replace
from structs import Message
from managers.rdtlgc_manager import CheckpointControlBlock
from typing import Dict, Union


class RdtLgc:
    def __init__(self, id: int) -> None:
        self.dependency_vector: Dict[int, int] = defaultdict(int)
        self.uncollected_checkpoints: Dict[int, CheckpointControlBlock] = {}
        self.id = id

    def release(self, other_id: int) -> Union[None, int]:
        checkpoint_to_remove: Union[None, int] = None
        if other_id in self.uncollected_checkpoints:
            self.uncollected_checkpoints[other_id].reference_counter -= 1
            if self.uncollected_checkpoints[other_id].reference_counter == 0:
                checkpoint_to_remove = self.uncollected_checkpoints[
                    other_id
                ].checkpoint_index
            del self.uncollected_checkpoints[other_id]
        return checkpoint_to_remove

    def link(self, other_id: int):
        self.uncollected_checkpoints[other_id] = replace(
            self.uncollected_checkpoints[self.id]
        )
        self.uncollected_checkpoints[other_id].reference_counter += 1

    def new_checkpoint_control_block(self):
        self.uncollected_checkpoints[self.id] = CheckpointControlBlock(
            checkpoint_index=self.dependency_vector[self.id], reference_counter=1
        )

    def on_message(self, message: Message):
        incoming_dependency_vector: Dict[int, int] = defaultdict(int, message.extra)
        component_ids = set(
            list(self.dependency_vector.keys())
            + list(incoming_dependency_vector.keys())
        )
        for id in component_ids:
            if incoming_dependency_vector[id] > self.dependency_vector[id]:
                self.dependency_vector[id] = incoming_dependency_vector[id]
                self.release(id)
                self.link(id)

    # called AFTER saving checkpoint
    # must save dependency vector in the checkpoint
    def on_checkpoint_taken(self):
        self.release(self.id)
        self.new_checkpoint_control_block()
        self.dependency_vector[self.id] += 1
