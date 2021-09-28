import random
from typing import Any, List, Tuple

from numpy.random import default_rng

from managers.optimistic_manager import OptimisticManager
from runner import ComponentConfig, run_simulation
from structs import Behavior, BehaviorMessage, Port, State


class AnotherBehavior(Behavior):
    rng: Any = default_rng()

    def rand(self) -> int:
        # return random.randint(100, 200)
        # return max(3, int(random.gauss(100, 10)))
        return max(3, int(random.gauss(100, 1000)))
        # return randint(100, 1000)

    def messages(self, ts: int) -> List[BehaviorMessage]:
        # if random.randint(1, 2) == 2:
        #     return [
        #         BehaviorMessage("content", ts + self.rand(), "out"),
        #         BehaviorMessage("content", ts + self.rand(), "out2"),
        #     ]
        return [BehaviorMessage("content", ts + self.rand(), "out")]

    def init(self) -> Tuple[State, List[BehaviorMessage]]:
        return ("state", self.messages(0))

    def on_message(
        self, state: State, message: BehaviorMessage
    ) -> Tuple[State, List[BehaviorMessage]]:
        return ("state", self.messages(message.exec_ts))


def main():
    component_configs = [
        ComponentConfig(
            manager_class=OptimisticManager, behavior=AnotherBehavior(), id=1
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=AnotherBehavior(), id=2
        ),
        ComponentConfig(
            manager_class=OptimisticManager, behavior=AnotherBehavior(), id=3
        ),
    ]
    port_config = {
        Port(component=1, route="out"): Port(component=2, route="in"),
        Port(component=2, route="out"): Port(component=3, route="in"),
        Port(component=3, route="out"): Port(component=1, route="in"),
        Port(component=1, route="out2"): Port(component=3, route="in"),
        Port(component=2, route="out2"): Port(component=1, route="in"),
        Port(component=3, route="out2"): Port(component=2, route="in"),
    }
    run_simulation(port_config=port_config, component_configs=component_configs)


if __name__ == "__main__":
    main()
