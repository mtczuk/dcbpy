from dataclasses import dataclass
from structs import BehaviorMessage, Message, Port, PortConfig
from typing import Callable


@dataclass
class Translator:
    config: PortConfig
    id_generator: Callable[[], str]
    sender: int

    def translate(
        self,
        message: BehaviorMessage,
        lvt: int,
    ) -> Message:
        sender_port = Port(component=self.sender, route=message.route)
        receiver_port = self.config[sender_port]
        translated = Message(
            id=self.id_generator(),
            route=receiver_port.route,
            sent_ts=lvt,
            exec_ts=message.exec_ts,
            content=message.content,
            sender=self.sender,
            receiver=receiver_port.component,
            is_anti=False
        )
        return translated

    def to_behavior(self, message: Message) -> BehaviorMessage:
        return BehaviorMessage(
            content=message.content, exec_ts=message.exec_ts, route=message.route
        )
