import uuid
from random import randint
from typing import List, Tuple

from managers.optimistic_manager import OptimisticManager
from runner import ComponentConfig, run_simulation
from structs import Behavior, BehaviorMessage, Port, PortConfig, State


class SimpleBehavior(Behavior):
    def init(self) -> Tuple[State, List[BehaviorMessage]]:
        self.counter = 0
        return (str(uuid.uuid4()), [BehaviorMessage("content", 10, "out")])

    def on_message(
        self, state: State, message: BehaviorMessage
    ) -> Tuple[State, List[BehaviorMessage]]:
        self.counter += 1
        to_send: List[BehaviorMessage] = []
        if self.counter < 2000000:
            to_send.append(
                BehaviorMessage("content", message.exec_ts + randint(10, 10000), "out")
            )
        return str(uuid.uuid4()), to_send


def main():
    component_configs = [
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(), id=1
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(), id=2
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=SimpleBehavior(), id=3
        ),
    ]
    port_config: PortConfig = {
        Port(component=1, route="out"): Port(component=2, route="in"),
        Port(component=2, route="out"): Port(component=3, route="in"),
        Port(component=3, route="out"): Port(component=1, route="in"),
    }
    run_simulation(port_config=port_config, component_configs=component_configs)


if __name__ == "__main__":
    main()
