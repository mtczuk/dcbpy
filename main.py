import uuid
from random import randint
from typing import Any, List, Tuple

from managers.optimistic_manager import OptimisticManager
from runner import ComponentConfig, run_simulation
from structs import Behavior, BehaviorMessage, Port, PortConfig, State
from numpy.random import default_rng


class AnotherBehavior(Behavior):
    rng: Any = default_rng()

    def rand(self) -> int:
        return list(self.rng.integers(low=100, high=10000, size=1))[0]

    def init(self) -> Tuple[State, List[BehaviorMessage]]:
        return ("state", [BehaviorMessage("content", self.rand(), "out")])

    def on_message(
        self, state: State, message: BehaviorMessage
    ) -> Tuple[State, List[BehaviorMessage]]:
        return (
            "state",
            [BehaviorMessage("content", message.exec_ts + self.rand(), "out")],
        )


class SimpleBehavior(Behavior):
    def __init__(self, delta: int = 1) -> None:
        self.delta = delta

    def init(self) -> Tuple[State, List[BehaviorMessage]]:
        return (
            str(uuid.uuid4()),
            [BehaviorMessage("content", 10, "out1" if randint(0, 1) else "out2")],
        )

    def on_message(
        self, state: State, message: BehaviorMessage
    ) -> Tuple[State, List[BehaviorMessage]]:
        to_send: List[BehaviorMessage] = []
        for _ in range(randint(1, self.delta)):
            to_send.append(
                BehaviorMessage(
                    "content",
                    message.exec_ts + randint(10, 100 * self.delta),
                    "out1" if randint(0, 1) else "out2",
                )
            )
        return str(uuid.uuid4()), to_send


def main_old():
    component_configs = [
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(delta=2), id=1
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(delta=4), id=2
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(delta=7), id=3
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(delta=9), id=4
        ),
    ]
    port_config: PortConfig = {
        Port(component=1, route="out1"): Port(component=2, route="in"),
        Port(component=2, route="out1"): Port(component=4, route="in"),
        Port(component=3, route="out1"): Port(component=1, route="in"),
        Port(component=1, route="out2"): Port(component=3, route="in"),
        Port(component=2, route="out2"): Port(component=1, route="in"),
        Port(component=3, route="out2"): Port(component=4, route="in"),
        Port(component=4, route="out1"): Port(component=1, route="in"),
        Port(component=4, route="out2"): Port(component=2, route="in"),
    }
    run_simulation(port_config=port_config, component_configs=component_configs)


def main():
    component_configs = [
        ComponentConfig(
            manager_class=OptimisticManager, behavior=AnotherBehavior(), id=1
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=AnotherBehavior(), id=2
        ),
    ]
    port_config = {
        Port(component=1, route="out"): Port(component=2, route="in"),
        Port(component=2, route="out"): Port(component=1, route="in"),
    }
    run_simulation(port_config=port_config, component_configs=component_configs)


if __name__ == "__main__":
    main()
