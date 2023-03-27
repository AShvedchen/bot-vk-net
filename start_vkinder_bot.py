from main import *
import threading

gen = {}


def handle_user_event(event):
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        if event.text.lower() == 'поиск':
            gen[event.user_id] = Bot().find_users(event.user_id, params=False)
            try:
                next_user = next(gen[event.user_id])
            except StopIteration:
                Bot().write_msg(event.user_id, 'К сожалению, больше нет подходящих пользователей')
            else:
                Bot().write_msg(event.user_id, f'Привет, {Bot().info_user(event.user_id)[0]}! Нашёл для тебя пару)')
                Bot().next_user(event.user_id, next_user, '')
                Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'поиск по параметрам':
            gen[event.user_id] = Bot().find_users(event.user_id, params=True)
            try:
                next_user = next(gen[event.user_id])
            except StopIteration:
                Bot().write_msg(event.user_id, 'К сожалению, больше нет подходящих пользователей')
            else:
                Bot().write_msg(event.user_id, f'Привет, {Bot().info_user(event.user_id)[0]}! Нашёл для тебя пару)')
                Bot().next_user(event.user_id, next_user, '')
                Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'ещё' and event.user_id in gen:
            try:
                next_user = next(gen[event.user_id])
            except StopIteration:
                Bot().write_msg(event.user_id, 'К сожалению, больше нет подходящих пользователей')
            else:
                Bot().next_user(event.user_id, next_user, '')
                Bot().write_msg(event.user_id, f'Жми "Ещё"')


def listen_for_events():
    try:
        for event in Bot().longpoll.listen():
            threading.Thread(target=handle_user_event, args=(event,)).start()
    except (KeyError, ApiError, AuthError, VkApiError) as e:
        print(f'Произошла ошибка при запуске бота: {e}.')

if __name__ == '__main__':
    print('Бот готов')
    delete_all_tables(engine)
    create_tables()
    listen_for_events()
