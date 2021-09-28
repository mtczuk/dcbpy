import os
from typing import Callable, List

from component_manager import ComponentManager
from message_queue import MessageQueue
from rollback_manager import RollbackManager
from structs import Behavior, Chart, Message
from translator import Translator

COLLECT_DATA = (
    True
    if "COLLECT_DATA" not in os.environ
    else os.environ["COLLECT_DATA"].lower() != "false"
)
GC_ACTIVE = (
    False
    if "GC_ACTIVE" not in os.environ
    else os.environ["GC_ACTIVE"].lower() != "false"
)

SIM_DURATION = (
    100000 if "SIM_DURATION" not in os.environ else int(os.environ["SIM_DURATION"])
)


MIN_CHECKPOINTS = 10
SECURITY_MULT = 10
SECURITY_MULT_MIN = 3
SECURITY_DECREASE = 10000
GC_WAIT = 50


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
        self.data: List[int] = []
        self.max_rollback = 1
        self.rollback_sizes: List[int] = []
        self.max_checkpoints = 0
        self.rollback_average = -1.0
        self.max_rollback_stdev: float = 1
        super().__init__(id, send, behavior, translator)

    def checkpoint_limit(self):
        return max(
            MIN_CHECKPOINTS,
            int(
                self.max_rollback
                + (self.max_rollback - int(self.rollback_average))
                * max(
                    SECURITY_MULT - int(self.counter / SECURITY_DECREASE),
                    SECURITY_MULT_MIN,
                )
            ),
        )

    def init(self) -> None:
        self.queue = MessageQueue()
        state, messages = self.behavior.init()
        self.rollback_manager = RollbackManager(id=self.id, state=state)
        self.rollback_manager.start()
        self.send_list(messages, lvt=self.rollback_manager.lvt)

    def can_run_without_new_messages(self) -> bool:
        res = self.queue.has_regular_messages()
        return res

    def refuses_to_continue(self) -> bool:
        return self.counter > SIM_DURATION

    def on_message(self, message: Message) -> None:
        self.max_checkpoints = max(
            self.max_checkpoints, len(self.rollback_manager.checkpoints)
        )
        self.counter += 1
        if self.counter % 1000 == 0:
            print(self.id, "\t", self.counter)
        if self.rollback_manager.lvt > message.exec_ts:
            checkpoints_before = len(self.rollback_manager.checkpoints)
            to_send = self.rollback_manager.rollback(message.exec_ts)
            self.checkpoints = len(self.rollback_manager.checkpoints)

            rollback_len = checkpoints_before - self.checkpoints
            self.rollback_sizes.append(rollback_len)

            self.max_rollback = max(self.max_rollback, rollback_len)

            if self.rollback_average < 0:
                self.rollback_average = float(rollback_len)
            else:
                self.rollback_average = (
                    self.rollback_average * 0.95 + rollback_len * 0.05
                )

            for m in to_send:
                self.send(m)
        else:
            self.rollback_sizes.append(0)
        self.queue.save_message(message)

    def step(self) -> None:
        if not self.queue.has_regular_messages():
            return

        if self.queue.has_regular_messages():
            current_message = self.queue.pop_next_regular_message()

            if self.counter > GC_WAIT and GC_ACTIVE:
                self.rollback_manager.checkpoints = self.rollback_manager.checkpoints[
                    -self.checkpoint_limit() :
                ]
                lower_bound = self.rollback_manager.checkpoints[0].timestamp
                self.rollback_manager.received_messages = [
                    m
                    for m in self.rollback_manager.received_messages
                    if m.exec_ts >= lower_bound
                ]
                self.rollback_manager.sent_messages = [
                    m
                    for m in self.rollback_manager.sent_messages
                    if m.sent_ts >= lower_bound
                ]
            if current_message.exec_ts > self.rollback_manager.lvt:
                self.rollback_manager.take_checkpoint()
            if COLLECT_DATA:
                self.checkpoint_list.append(len(self.rollback_manager.checkpoints))
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

        if COLLECT_DATA:
            self.data.append(self.rollback_manager.lvt)

    def get_charts(self) -> List[Chart]:
        return [
            Chart(name="checkpoints", ys=self.checkpoint_list),
            Chart(name="messages", ys=self.data),
        ]

    def on_exit(self) -> None:
        print(self.id, "max checkpoints", self.max_checkpoints)
        with open(f"outputs/checkpoints_{self.id}", "w") as file:
            for c in self.checkpoint_list:
                file.write(f"{c}\n")
        with open(f"outputs/messages_{self.id}.txt", "w") as file:
            for d in self.data:
                file.write(f"{d}\n")
        with open(f"outputs/rollbacks_{self.id}", "w") as file:
            for d in self.rollback_sizes:
                file.write(f"{d}\n")
