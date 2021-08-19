from translator import Translator
from typing import Callable, List

from component_manager import ComponentManager
from message_queue import MessageQueue
from rollback_manager import RollbackManager
from structs import Behavior, Message


class OptimisticManager(ComponentManager):
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
        super().__init__(id, send, behavior, translator)

    def print(self, *args: object):
        if self.id == 1:
            print(*args)

    def init(self) -> None:
        self.print(f"{self.id} starting")
        self.queue = MessageQueue()
        state, messages = self.behavior.init()
        self.rollback_manager = RollbackManager(id=self.id, state=state)
        self.rollback_manager.start()
        self.send_list(messages, lvt=self.rollback_manager.lvt)
        self.data: List[int] = []

    def can_run_without_new_messages(self) -> bool:
        res = self.queue.has_regular_messages()
        return res

    def refuses_to_continue(self) -> bool:
        return self.counter > 1000

    def on_message(self, message: Message) -> None:
        self.counter += 1
        self.print(
            "on_message", len(self.queue.messages), len(self.queue.anti_messages)
        )
        self.print(f"LVT[{self.rollback_manager.lvt}] > MSG[{message.exec_ts}]")
        if self.rollback_manager.lvt > message.exec_ts:
            to_send = self.rollback_manager.rollback(message.exec_ts)
            self.checkpoints = len(self.rollback_manager.checkpoints)
            for m in to_send:
                self.send(m)
        self.queue.save_message(message)

    def step(self) -> None:
        if not self.queue.has_regular_messages():
            return

        if self.queue.has_regular_messages():
            current_message = self.queue.pop_next_regular_message()
            if current_message.exec_ts > self.rollback_manager.lvt:
                self.rollback_manager.take_checkpoint()
                self.checkpoints += 1
            self.checkpoint_list.append(self.checkpoints)
            self.rollback_manager.save_message(current_message)
            state, messages = self.behavior.on_message(
                state=self.rollback_manager.state,
                message=self.translator.to_behavior(current_message),
            )
            translated_messages = [
                self.translator.translate(message=m, lvt=self.rollback_manager.lvt)
                for m in messages
            ]
            for m in translated_messages:
                self.rollback_manager.save_message(m)
            self.rollback_manager.update(state=state, lvt=current_message.exec_ts)

            for m in translated_messages:
                self.send(m)

        self.data.append(self.rollback_manager.lvt)

    def on_exit(self) -> None:
        with open(f"outputs/checkpoints_{self.id}", "w") as file:
            for c in self.checkpoint_list:
                file.write(f"{c}\n")
        with open(f"outputs/messages_{self.id}.txt", "w") as file:
            for d in self.data:
                file.write(f"{d}\n")
