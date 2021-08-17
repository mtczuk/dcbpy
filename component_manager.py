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

    def can_run_without_new_messages(self) -> bool:
        return True

    def init(self) -> None:
        raise NotImplementedError

    def on_message(self, message: Message) -> None:
        raise NotImplementedError

    def step(self) -> None:
        raise NotImplementedError

    def refuses_to_continue(self) -> bool:
        return False

    def on_exit(self) -> None:
        pass
