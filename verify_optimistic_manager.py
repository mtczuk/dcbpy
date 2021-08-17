from typing import Any, List, Tuple

from managers.optimistic_manager import OptimisticManager
from structs import Behavior, BehaviorMessage, Message, State
from translator import Translator
from tabulate import tabulate
import uuid


sent: List[Message] = []


def send_fn(m: Message):
    global sent
    sent.append(m)


def print_messages(messages: List[Message], title: str):
    print(
        tabulate(
            [["", m.id, m.exec_ts, m.sent_ts, m.is_anti] for m in messages],
            headers=[title, "ID", "Exec TS", "Sent TS", "is anti"],
        )
    )


def print_sent():
    global sent
    if len(sent) > 0:
        print_messages(sent, "SENDING")
    sent.clear()


class MockTranslator(Translator):
    def __init__(self):
        pass

    def translate(self, message: BehaviorMessage, lvt: int) -> Message:
        return Message(
            id=str(uuid.uuid4()),
            route=message.route,
            sent_ts=lvt,
            exec_ts=message.exec_ts,
            content=message.content,
            sender=1,
            receiver=3,
            is_anti=False,
        )


next_state = None
next_messages: List[BehaviorMessage] = []


class MockBehavior(Behavior):
    def init(self) -> Tuple[State, List[BehaviorMessage]]:
        return (next_state, next_messages)

    def on_message(
        self, state: State, message: BehaviorMessage
    ) -> Tuple[State, List[BehaviorMessage]]:
        return (next_state, next_messages)


def simple_test():
    global next_messages
    manager = OptimisticManager(
        id=1, send=send_fn, behavior=MockBehavior(), translator=MockTranslator()
    )
    next_messages = [BehaviorMessage(content="first", exec_ts=10, route="out")]
    manager.init()
    next_messages = [BehaviorMessage(content="first", exec_ts=30, route="out")]
    manager.on_message(
        Message(
            id="one",
            route="",
            sent_ts=10,
            exec_ts=20,
            content="content",
            sender=2,
            receiver=1,
            is_anti=False,
        )
    )
    manager.on_message(
        Message(
            id="two",
            route="",
            sent_ts=10,
            exec_ts=40,
            content="content",
            sender=2,
            receiver=1,
            is_anti=False,
        )
    )
    manager.on_message(
        Message(
            id="three",
            route="",
            sent_ts=10,
            exec_ts=12,
            content="content",
            sender=2,
            receiver=1,
            is_anti=False,
        )
    )
    manager.step()


must_send: List[BehaviorMessage] = []


def run_test(description: List[Any]):
    global must_send

    class NoneBehavior(Behavior):
        def init(self) -> Tuple[State, List[BehaviorMessage]]:
            global must_send
            value = ("state", must_send)
            must_send = []
            return value

        def on_message(
            self, state: State, message: BehaviorMessage
        ) -> Tuple[State, List[BehaviorMessage]]:
            global must_send
            value = ("state", must_send)
            must_send = []
            return value

    manager = OptimisticManager(
        id=1, send=send_fn, behavior=NoneBehavior(), translator=MockTranslator()
    )
    manager.init()
    for action in description:
        if action == "step":
            manager.step()
            print_sent()
        elif action == "checkpoints":
            print("lvt:", manager.rollback_manager.lvt)
            print(
                "checkpoints:",
                [c.timestamp for c in manager.rollback_manager.checkpoints],
            )
            print_messages(
                manager.rollback_manager.received_messages, "RECEIVED MESSAGES"
            )
            print_messages(manager.rollback_manager.sent_messages, "SENT MESSAGES")
        elif action == "queue":
            print_messages(manager.queue.messages, "QUEUE REGULAR")
            print_messages(manager.queue.anti_messages, "QUEUE ANTI")
        elif type(action) is tuple:
            timestamp = abs(int(action[0]))
            is_anti = int(action[0]) < 0
            id = str(action[1])
            message = Message(
                id=id,
                route="route",
                sent_ts=0,
                exec_ts=timestamp,
                content="content",
                sender=2,
                receiver=1,
                is_anti=is_anti,
            )
            manager.on_message(message)
        elif type(action) is list:
            for timestamp in action:
                must_send.append(
                    BehaviorMessage(content="content", exec_ts=timestamp, route="out")
                )
        else:
            print("______DEBUG:", action)


# (10, "a") send message to queue
# "queue" show queue
# "checkpoints" show checkpoints
# "step"
# [1,2,3] send these messages next
# print anything else

run_test(
    [
        (10, "a"),
        (30, "b"),
        "checkpoints",
        "step",
        "step",
        "checkpoints",
        (20, "c"),
        "queue",
        "checkpoints",
    ]
)
