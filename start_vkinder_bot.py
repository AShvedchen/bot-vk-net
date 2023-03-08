from main import *
import threading

gen = {}

def handle_user_event(event):
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        if event.text.lower() == 'поиск':
            Bot().delete_users_find(event.user_id)
            Bot().insert_user(event.user_id)
            Bot().find_users(event.user_id)
            Bot().write_msg(event.user_id, f'Привет, {select_param_user(event.user_id)[1]}! Нашёл для тебя пару)')
            gen[event.user_id] = select_find_users(event.user_id)
            Bot().next_user(event.user_id, next(gen[event.user_id]), '')
            Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'поиск по параметрам':
            Bot().delete_users_find(event.user_id)
            Bot().insert_user(event.user_id)
            Bot().find_users_param(event.user_id)
            Bot().write_msg(event.user_id, f'Привет, {select_param_user(event.user_id)[1]}! Нашёл для тебя пару)')
            gen[event.user_id] = select_find_users(event.user_id)
            Bot().next_user(event.user_id, next(gen[event.user_id]), '')
            Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'ещё' and event.user_id in gen:
            next_user = next(gen[event.user_id])
            Bot().next_user(event.user_id, next_user, '')
            Bot().write_msg(event.user_id, f'Нашёл для тебя пару:')

def listen_for_events():
    for event in Bot().longpoll.listen():
        threading.Thread(target=handle_user_event, args=(event,)).start()

if __name__ == '__main__':
    print('Бот готов')
    delete_all_tables(engine)
    create_tables()
    listen_for_events()