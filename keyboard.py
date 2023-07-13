import json

from vk_api.keyboard import VkKeyboard


class Keyboard:
    def __init__(self):
        self.keyboard = VkKeyboard()

    def add_button(self, text, color):
        self.keyboard.add_button(text, color=color)
        return {
            "action": {
                "type": "text",
                "payload": "{\"button\": \"" + "поиск" + "\"}",
                "label": f"{text}"
            },
            "color": f"{color}"
        }

    keyboard = {
        "one_time": False,
        "buttons": [
            [add_button('привет', 'primary')],
            [add_button('поиск', 'secondary')]
        ]
    }

    def add_line(self):
        self.keyboard.add_line()

    def get_keyboard(self):
        return self.keyboard.get_keyboard()

    def get_json(self):
        keyboard_json = json.dumps(self.keyboard, ensure_ascii=False).encode('utf-8')
        return str(keyboard_json.decode('utf-8'))
