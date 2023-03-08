import json


def button(text, color):
    return {
        "action": {
            "type": "text",
            "payload": "{\"button\": \"" + "1" + "  \"}",
            "label": f"{text}"
        },
        "color": f"{color}"
    }


keyboard = json.dumps({
    "one_time": False,
    "buttons": [
        [button('Поиск', 'primary'), button('Ещё', 'secondary')],
        [button('Поиск по параметрам', 'secondary')]
    ]
}, ensure_ascii=False).encode('utf-8').decode('utf-8')
