from time import time
from typing import List

from component_manager import ComponentManager
from structs import Message


class DumbManager(ComponentManager):
    state = None
    data: List[int] = []

    def init(self) -> None:
        messages = self.behavior.init()[1]
        print(self.id, "init", messages)
        self.send_list(messages, 0)

    def on_message(self, message: Message) -> None:
        self.data.append(message.exec_ts)
        print(f"{self.id} got message {message}")
        behavior_msg = self.translator.to_behavior(message)
        r = self.behavior.on_message(state="state", message=behavior_msg)
        print(self.id, "on_message said", r)

        state, messages = self.behavior.on_message(state="state", message=behavior_msg)
        self.state = state
        self.send_list(messages, 0)

    def on_exit(self) -> None:
        with open(f"outputs/{time()}_testing_{self.id}.txt", "w") as file:
            for d in self.data:
                file.write(f"{d}\n")
