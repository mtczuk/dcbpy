from dataclasses import dataclass, replace
from structs import Message
from typing import Any, List


@dataclass
class Checkpoint:
    timestamp: int
    state: Any


class RollbackManager:
    checkpoints: List[Checkpoint] = []
    received_messages: List[Message] = []
    sent_messages: List[Message] = []
    lvt: int = 0

    def __init__(self, id: int, state: Any) -> None:
        self.id = id
        self.state = state

    def start(self) -> None:
        self.take_checkpoint()

    def save_message(self, message: Message) -> None:
        if message.sender == self.id:
            self.sent_messages.append(message)
        else:
            self.received_messages.append(message)

    def rollback(self, timestamp: int) -> List[Message]:
        to_send: List[Message] = []
        to_send.extend(
            [
                replace(m, is_anti=True)
                for m in self.sent_messages
                if m.sent_ts >= timestamp
            ]
        )
        to_send.extend([m for m in self.received_messages if m.exec_ts >= timestamp])

        self.checkpoints = [c for c in self.checkpoints if c.timestamp < timestamp]
        self.sent_messages = [m for m in self.sent_messages if m.sent_ts < timestamp]
        self.received_messages = [
            m for m in self.received_messages if m.exec_ts < timestamp
        ]

        return to_send

    def free(self, timestamp: int) -> None:
        self.checkpoints = [c for c in self.checkpoints if c.timestamp <= timestamp]

    def take_checkpoint(self) -> None:
        self.checkpoints.append(Checkpoint(timestamp=self.lvt, state=self.state))
        self.lvt += 1

    def update(self, state: Any, lvt: int) -> None:
        self.state = state
        self.lvt = lvt