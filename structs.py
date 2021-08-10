from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

State = Any


@dataclass
class Message:
    id: str
    route: str
    sent_ts: int
    exec_ts: int
    content: str
    sender: int
    receiver: int
    is_anti: bool


@dataclass
class BehaviorMessage:
    content: str
    exec_ts: int
    route: str


@dataclass(frozen=True)
class Port:
    component: int
    route: str


PortConfig = Dict[Port, Port]


class Behavior:
    def init(
        self,
    ) -> Tuple[State, List[BehaviorMessage]]:
        raise NotImplemented

    def on_message(
        self, state: State, message: BehaviorMessage
    ) -> Tuple[State, List[BehaviorMessage]]:
        raise NotImplemented
