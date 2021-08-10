from typing import Callable, List
from structs import Behavior, BehaviorMessage, Message
from translator import Translator


class ComponentManager:
    def __init__(
        self,
        id: int,
        send: Callable[[Message], None],
        behavior: Behavior,
        translator: Translator,
    ) -> None:
        self.id = id
        self.send = send
        self.behavior = behavior
        self.translator = translator

    def send_list(self, messages: List[BehaviorMessage], lvt: int):
        for m in messages:
            self.send(self.translator.translate(message=m, lvt=lvt))

    def init(self) -> None:
        raise NotImplemented

    def on_message(self, message: Message) -> None:
        raise NotImplemented

    def on_exit(self) -> None:
        pass
