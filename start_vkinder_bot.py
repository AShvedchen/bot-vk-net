from main import *

print('Бот готов')
delete_all_tables(engine)
create_tables()
gen = None
for event in Bot().longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        if event.text.lower() == 'поиск':
            Bot().delete_users_find(event.user_id)
            Bot().insert_user(event.user_id)
            Bot().find_users(event.user_id)
            Bot().write_msg(event.user_id, f'Привет {select_param_user(event.user_id)[1]}! Нашёл для тебя пару)')
            gen = select_find_users(event.user_id)
            Bot().next_user(event.user_id, next(gen), '')
            Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'поиск по':
            Bot().delete_users_find(event.user_id)
            Bot().insert_user(event.user_id)
            Bot().find_users_param(event.user_id)
            Bot().write_msg(event.user_id, f'Привет {select_param_user(event.user_id)[1]}! Нашёл для тебя пару)')
            gen = select_find_users(event.user_id)
            Bot().next_user(event.user_id, next(gen), '')
            Bot().write_msg(event.user_id, f'Жми "Ещё"')
        elif event.text.lower() == 'ещё' and gen is not None:
            Bot().next_user(event.user_id, next(gen), '')
            Bot().write_msg(event.user_id, f'Жми "Ещё"')
        else:
            pass
