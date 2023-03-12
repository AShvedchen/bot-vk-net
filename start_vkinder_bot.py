from main import *
import threading

gen = {}


def handle_user_event(event):
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        if event.text.lower() == 'поиск':
            Bot().insert_user(event.user_id)
            gen[event.user_id] = Bot().find_users(event.user_id, search_params={})
            try:
                next_user = next(gen[event.user_id])
            except StopIteration:
                Bot().write_msg(event.user_id, 'К сожалению, больше нет подходящих пользователей')
            except Exception as e:
                Bot().write_msg(event.user_id, f'Произошла ошибка: {str(e)}')
            else:
                Bot().write_msg(event.user_id, f'Привет, {select_param_user(event.user_id)[1]}! Нашёл для тебя пару)')
                Bot().next_user(event.user_id, next_user, '')
                Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'поиск по параметрам':
            Bot().insert_user(event.user_id)
            params = {
                'v': '5.131',
                'sex': 2 if int(select_param_user(event.user_id)[0]) == 1 else 1,
                'age_from': Bot().age_from(event.user_id),
                'age_to': Bot().age_to(event.user_id),
                'city': Bot().find_city(event.user_id),
                'fields': 'is_closed, id, first_name, last_name',
                'status': '6',
                'has_photo': '1',
                'count': 999
            }
            gen[event.user_id] = Bot().find_users(event.user_id, search_params=params)
            try:
                next_user = next(gen[event.user_id])
            except StopIteration:
                Bot().write_msg(event.user_id, 'К сожалению, больше нет подходящих пользователей')
            except Exception as e:
                Bot().write_msg(event.user_id, f'Произошла ошибка: {str(e)}')
            else:
                Bot().write_msg(event.user_id, f'Привет, {select_param_user(event.user_id)[1]}! Нашёл для тебя пару)')
                Bot().next_user(event.user_id, next_user, '')
                Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'ещё' and event.user_id in gen:
            try:
                next_user = next(gen[event.user_id])
            except StopIteration:
                Bot().write_msg(event.user_id, 'К сожалению, больше нет подходящих пользователей')
            except Exception as e:
                Bot().write_msg(event.user_id, f'Произошла ошибка: {str(e)}')
            else:
                Bot().next_user(event.user_id, next_user, '')
                Bot().write_msg(event.user_id, f'Жми "Ещё"')


def listen_for_events():
    for event in Bot().longpoll.listen():
        threading.Thread(target=handle_user_event, args=(event,)).start()


if __name__ == '__main__':
    print('Бот готов')
    delete_all_tables(engine)
    create_tables()
    listen_for_events()
