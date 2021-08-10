from dataclasses import dataclass
from queue import Queue
from structs import Message
from typing import Dict


@dataclass
class Messenger:
    queues: Dict[int, Queue[Message]]

    def send(self, message: Message):
        queue = self.queues[message.receiver]
        queue.put(message)
