from time import time
from typing import List

from component_manager import ComponentManager
from message_queue import MessageQueue
from rollback_manager import RollbackManager
from structs import Message


class OptimisticManager(ComponentManager):
    def init(self) -> None:
        print(f"{self.id} starting")
        self.queue = MessageQueue()
        state, messages = self.behavior.init()
        self.rollback_manager = RollbackManager(id=self.id, state=state)
        self.rollback_manager.start()
        self.send_list(messages, lvt=self.rollback_manager.lvt)
        self.data: List[int] = []

    def on_message(self, message: Message) -> None:
        print("I received an antimessage")
        self.queue.save_message(message)
        #         print(
        #             f"""
        # {self.id} got message {message}
        # current lvt={self.rollback_manager.lvt}
        # message lvt={message.exec_ts}
        # queue regular={self.queue.messages}
        # queue anti={self.queue.anti_messages}
        # queue lvt={self.queue.smallest_exec_ts()}
        # """
        #         )

        if self.rollback_manager.lvt > self.queue.smallest_exec_ts():
            print(self.id, "ROLLBACK!!!")
            to_send = self.rollback_manager.rollback(self.queue.smallest_exec_ts())
            for m in to_send:
                print("m is", m)
                self.send(m)
        elif self.queue.has_regular_messages():
            print(self.id, "NOT ROLLBACK")
            current_message = self.queue.pop_next_regular_message()
            self.rollback_manager.save_message(current_message)
            state, messages = self.behavior.on_message(
                state=self.rollback_manager.state,
                message=self.translator.to_behavior(current_message),
            )
            for m in messages:
                self.rollback_manager.save_message(
                    self.translator.translate(message=m, lvt=self.rollback_manager.lvt)
                )
            self.rollback_manager.update(state=state, lvt=current_message.exec_ts)
            self.rollback_manager.state = state
            self.send_list(messages=messages, lvt=self.rollback_manager.lvt)

        self.data.append(self.rollback_manager.lvt)

    def on_exit(self) -> None:
        with open(f"outputs/{time()}_testing_{self.id}.txt", "w") as file:
            for d in self.data:
                file.write(f"{d}\n")
