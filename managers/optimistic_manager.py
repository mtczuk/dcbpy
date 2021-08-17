from time import time
from typing import Any, List, Set

from component_manager import ComponentManager
from message_queue import MessageQueue
from rollback_manager import RollbackManager
from structs import Message
from tabulate import tabulate


class OptimisticManager(ComponentManager):
    counter = 0
    exec_messages: Set[str] = set()
    debug: List[Any] = []

    def add_debug(self, m: Message, label: str):
        self.debug.append(
            [
                label,
                m.exec_ts,
                m.sent_ts,
                m.sender,
                m.receiver,
                m.is_anti,
                m.id,
                self.rollback_manager.checkpoints[-1].timestamp,
                None,
            ]
        )

    def add_checkpoints(self):
        self.debug.append(
            [
                "CHECKPOINTS",
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                [c.timestamp for c in self.rollback_manager.checkpoints[-15:]],
            ]
        )

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
        return self.counter > 300

    def on_message(self, message: Message) -> None:
        self.counter += 1
        self.print(
            "on_message", len(self.queue.messages), len(self.queue.anti_messages)
        )
        self.print(f"LVT[{self.rollback_manager.lvt}] > MSG[{message.exec_ts}]")
        if self.rollback_manager.lvt > message.exec_ts:
            self.print("rollback")
            self.add_debug(message, "rollback")
            to_send = self.rollback_manager.rollback(message.exec_ts)
            for m in to_send:
                self.send(m)
                self.add_debug(m, "resend")
        self.queue.save_message(message)

    def step(self) -> None:
        if not self.queue.has_regular_messages():
            return

        self.print("step")
        self.add_checkpoints()

        if self.queue.has_regular_messages():
            current_message = self.queue.pop_next_regular_message()
            self.print("msg", (current_message.exec_ts, current_message.id))
            self.add_debug(
                current_message,
                "exec old" if current_message.id in self.exec_messages else "exec new",
            )
            if current_message.id in self.exec_messages:
                self.print("exec old", current_message.exec_ts)
            else:
                self.print("exec new")
            self.exec_messages.add(current_message.id)
            if current_message.exec_ts > self.rollback_manager.lvt:
                self.rollback_manager.take_checkpoint()
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
                self.add_debug(m, "send new")
                self.rollback_manager.save_message(m)
            self.rollback_manager.update(state=state, lvt=current_message.exec_ts)
            self.rollback_manager.state = state

            for m in translated_messages:
                self.send(m)

        self.data.append(self.rollback_manager.lvt)

    def on_exit(self) -> None:
        with open(f"outputs/debug_{self.id}.txt", "w") as file:
            file.write(
                tabulate(
                    self.debug,
                    headers=[
                        "type",
                        "exec_ts",
                        "sent_ts",
                        "sender",
                        "receiver",
                        "is_anti",
                        "id",
                        "last checkpoint",
                        "checkpoints",
                    ],
                )
            )
        with open(f"outputs/{time()}_testing_{self.id}.txt", "w") as file:
            for d in self.data:
                file.write(f"{d}\n")
