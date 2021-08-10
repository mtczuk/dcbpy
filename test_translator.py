import unittest
from translator import Translator
from structs import BehaviorMessage, Message, Port


class TestTranslator(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        self.next_id = "id"
        self.translator = Translator(
            config={
                Port(component=1, route="1out_a"): Port(component=2, route="2in"),
                Port(component=1, route="1out_b"): Port(component=3, route="3in"),
            },
            id_generator=lambda: self.next_id,
            sender=1,
        )

    def test_translate_returns_correct_message_if_there_is_a_binding(self):
        message1 = self.translator.translate(
            message=BehaviorMessage(
                content="content",
                exec_ts=10,
                route="1out_a",
            ),
            lvt=5,
        )
        self.assertEqual(
            message1,
            Message(
                id="id",
                route="2in",
                sent_ts=5,
                exec_ts=10,
                content="content",
                sender=1,
                receiver=2,
                is_anti=False
            ),
        )

        self.next_id = "another_id"
        message2 = self.translator.translate(
            message=BehaviorMessage(
                content="another",
                exec_ts=20,
                route="1out_b",
            ),
            lvt=15,
        )
        self.assertEqual(
            message2,
            Message(
                id="another_id",
                route="3in",
                sent_ts=15,
                exec_ts=20,
                content="another",
                sender=1,
                receiver=3,
                is_anti=False
            ),
        )

    def test_translate_raises_exception_if_there_isnt_binding(self):
        self.assertRaises(
            Exception,
            lambda: self.translator.translate(
                message=BehaviorMessage(
                    content="whatever", exec_ts=100, route="invalid_route"
                ),
                lvt=50,
            ),
        )
