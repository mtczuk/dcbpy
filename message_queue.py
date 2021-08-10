from typing import List
from structs import Message
from dataclasses import dataclass


@dataclass
class MessageQueue:
    def __init__(self) -> None:
        self.messages: List[Message] = []
        self.anti_messages: List[Message] = []

    def save_message(self, message: Message) -> None:
        if message.is_anti:
            same_id = [m for m in self.messages if m.id == message.id]
            if len(same_id) > 0:
                print("killing incoming message")
                self.messages = [m for m in self.messages if m.id != message.id]
            else:
                self.anti_messages.append(message)
        else:
            same_id = [m for m in self.anti_messages if m.id == message.id]
            if len(same_id) > 0:
                print("killing incoming antimessage")
                self.anti_messages = [
                    m for m in self.anti_messages if m.id != message.id
                ]
            else:
                self.messages.append(message)

    def pop_next_regular_message(self) -> Message:
        self.messages.sort(key=lambda m: m.exec_ts, reverse=True)
        return self.messages.pop()

    def has_regular_messages(self) -> bool:
        return len(self.messages) > 0

    def smallest_exec_ts(self) -> int:
        self.messages.sort(key=lambda m: m.exec_ts)
        self.anti_messages.sort(key=lambda m: m.exec_ts)
        if len(self.messages) == 0 and len(self.anti_messages) == 0:
            raise Exception(
                "tried to get smallest timestamp of a queue without messages"
            )
        elif len(self.messages) == 0:
            return self.anti_messages[0].exec_ts
        elif len(self.anti_messages) == 0:
            return self.messages[0].exec_ts
        else:
            return min(self.messages[0].exec_ts, self.anti_messages[0].exec_ts)
