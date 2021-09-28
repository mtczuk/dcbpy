from typing import List
from structs import Message


class MessageQueue:
    def __init__(self) -> None:
        self.messages: List[Message] = []
        self.anti_messages: List[Message] = []

    def save_message(self, message: Message) -> None:
        if message.is_anti:
            same_id = [m for m in self.messages if m.id == message.id]
            if len(same_id) > 0:
                self.messages = [m for m in self.messages if m.id != message.id]
            else:
                self.anti_messages.append(message)
        else:
            same_id = [m for m in self.anti_messages if m.id == message.id]
            if len(same_id) > 0:
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
