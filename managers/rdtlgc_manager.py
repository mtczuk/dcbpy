from collections import defaultdict
from dataclasses import dataclass, replace
from typing import Callable, Dict, List, Tuple, Union

from component_manager import ComponentManager
from dependency_vector import DependencyVector
from message_queue import MessageQueue
from rollback_manager import RollbackManager
from structs import Behavior, Message, State
from translator import Translator


@dataclass
class CheckpointControlBlock:
    checkpoint_index: int
    reference_counter: int


class UncollectedCheckpoints:
    def __init__(self, id: int) -> None:
        self.dict: Dict[int, CheckpointControlBlock] = {}
        self.id = id

    def release(self, other_id: int) -> Union[None, int]:
        checkpoint_to_remove: Union[None, int] = None
        if other_id in self.dict:
            self.dict[other_id].reference_counter -= 1
            if self.dict[other_id].reference_counter == 0:
                checkpoint_to_remove = self.dict[other_id].checkpoint_index
            del self.dict[other_id]
        return checkpoint_to_remove

    def link(self, other_id: int):
        self.dict[other_id] = replace(self.dict[self.id])
        self.dict[other_id].reference_counter += 1

    def new_checkpoint_control_block(self, dependency_vector: DependencyVector):
        self.dict[self.id] = CheckpointControlBlock(
            checkpoint_index=dependency_vector.get(self.id), reference_counter=1
        )


class RdtLgcManager(ComponentManager):
    def __init__(
        self,
        id: int,
        send: Callable[[Message], None],
        behavior: Behavior,
        translator: Translator,
    ) -> None:
        self.counter = 0
        self.checkpoints: int = 0
        self.checkpoint_list: List[int] = []
        self.data: List[int] = []
        self.uncollected_checkpoints = UncollectedCheckpoints(id)
        self.dependency_vector = DependencyVector(id)
        super().__init__(id, send, behavior, translator)

    def init(self) -> None:
        self.queue = MessageQueue()
        state, messages = self.behavior.init()
        self.rollback_manager = RollbackManager(id=self.id, state=state)
        self.rollback_manager.start()

        # TODO: remember to save these messages on rollback manager here and
        # on OptimisticManager

        for m in messages:
            translated = self.translator.translate(
                message=m, lvt=self.rollback_manager.lvt
            )
            self.rollback_manager.save_message(translated)
            self.send(replace(translated, extra=self.dependency_vector.as_dict()))

    def can_run_without_new_messages(self) -> bool:
        res = self.queue.has_regular_messages()
        return res

    def refuses_to_continue(self) -> bool:
        return self.counter > 1000

    def on_message(self, message: Message) -> None:
        self.counter += 1
        if self.rollback_manager.lvt > message.exec_ts:
            to_send = self.rollback_manager.rollback(message.exec_ts)
            self.checkpoints = len(self.rollback_manager.checkpoints)
            for m in to_send:
                self.send(m)
        self.queue.save_message(message)

    def attempt_to_take_checkpoint(self, message: Message):
        if message.exec_ts > self.rollback_manager.lvt:
            self.rollback_manager.take_checkpoint()
            self.dependency_vector.on_checkpoint_taken()
            self.uncollected_checkpoints.release(self.id)
            self.checkpoints += 1
        self.checkpoint_list.append(self.checkpoints)

    def get_result_from_behavior(self, message: Message) -> Tuple[State, List[Message]]:
        state, messages = self.behavior.on_message(
            state=self.rollback_manager.state,
            message=self.translator.to_behavior(message),
        )
        translated_messages = [
            self.translator.translate(message=m, lvt=self.rollback_manager.lvt)
            for m in messages
        ]
        return state, translated_messages

    def lgc_on_message(self, current_message: Message):
        incoming_dependency_vector: Dict[int, int] = defaultdict(
            int, current_message.extra
        )

        # set of all keys present in either dependency vector
        component_keys = set(
            list(self.dependency_vector.as_dict().keys())
            + list(incoming_dependency_vector.keys())
        )
        for component_key in component_keys:
            if incoming_dependency_vector[component_key] > self.dependency_vector.get(
                component_key
            ):
                self.uncollected_checkpoints.release(component_key)
                self.uncollected_checkpoints.link(
                    component_key,
                )
        pass

    def step(self) -> None:
        if not self.queue.has_regular_messages():
            return
        current_message = self.queue.pop_next_regular_message()
        self.rollback_manager.save_message(current_message)
        self.dependency_vector.merge(current_message.extra)
        self.attempt_to_take_checkpoint(current_message)
        state, translated_messages = self.get_result_from_behavior(current_message)
        for m in translated_messages:
            self.rollback_manager.save_message(m)
        self.rollback_manager.update(state=state, lvt=current_message.exec_ts)

        for m in translated_messages:
            self.send(replace(m, extra=self.dependency_vector.as_dict()))

        self.data.append(self.rollback_manager.lvt)

    def on_exit(self) -> None:
        with open(f"outputs/checkpoints_{self.id}", "w") as file:
            for c in self.checkpoint_list:
                file.write(f"{c}\n")
        with open(f"outputs/messages_{self.id}.txt", "w") as file:
            for d in self.data:
                file.write(f"{d}\n")
