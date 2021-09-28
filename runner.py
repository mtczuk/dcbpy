from dataclasses import dataclass
from messenger import Messenger
from translator import Translator
from component_manager import ComponentManager
from structs import Behavior, Message, PortConfig
from typing import Dict, List
import queue
import uuid
import threading


def run_component(
    queues: Dict[int, queue.Queue[Message]],
    port_config: PortConfig,
    id: int,
    behavior: Behavior,
    manager_class: type[ComponentManager],
) -> None:
    translator = Translator(
        config=port_config, id_generator=lambda: str(uuid.uuid4()), sender=id
    )
    messenger = Messenger(queues=queues)

    def send(message: Message):
        messenger.send(message)

    manager = manager_class(id=id, send=send, behavior=behavior, translator=translator)
    manager.init()

    try:
        while True:
            if manager.refuses_to_continue():
                manager.on_exit()
                break
            while queues[id].qsize() != 0 or not manager.can_run_without_new_messages():
                manager.on_message(queues[id].get(timeout=1))
            manager.step()

    except queue.Empty:
        manager.on_exit()
        print(f"Component {id} stopped because of timeout")


@dataclass
class ComponentConfig:
    manager_class: type[ComponentManager]
    behavior: Behavior
    id: int


def run_simulation(port_config: PortConfig, component_configs: List[ComponentConfig]):
    queues: Dict[int, queue.Queue[Message]] = {
        conf.id: queue.Queue() for conf in component_configs
    }

    def component_thread(component_config: ComponentConfig) -> threading.Thread:
        return threading.Thread(
            target=lambda: run_component(
                queues=queues,
                port_config=port_config,
                id=component_config.id,
                behavior=component_config.behavior,
                manager_class=component_config.manager_class,
            )
        )

    threads: List[threading.Thread] = []
    for conf in component_configs:
        threads.append(component_thread(conf))

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    print("all threads joined")
