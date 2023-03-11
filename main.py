from datetime import datetime, date

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from random import randrange
from database_bot import *
from data_config import *
from vkinder_keyboard import keyboard

class Bot:
    def __init__(self):
        self.vk = vk_api.VkApi(token=club_token)
        self.user = vk_api.VkApi(token=user_token)
        self.longpoll = VkLongPoll(self.vk)

    def write_msg(self, user_id, message):
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'keyboard': keyboard,
                                         'random_id': randrange(10 ** 7)})

    def age_from(self, user_id):
            self.write_msg(user_id, 'Введите возраст поиска от: ')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    age_from = event.text
                    if age_from.isdigit() and 18 <= int(age_from) <= 70:
                        return int(age_from)
                    else:
                        self.write_msg(user_id, 'Возраст должен быть целым числом, попробуйте еще раз.')

    def age_to(self, user_id):
        self.write_msg(user_id, 'Введите возраст поиска до: ')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                age_to = event.text
                if age_to.isdigit() and 18 <= int(age_to) <= 70:
                    return int(age_to)
                else:
                    self.write_msg(user_id, 'Возраст должен быть целым числом, попробуйте еще раз.')


    def insert_user(self, user_id):
        response = self.vk.method('users.get', {'user_ids': user_id,
                                                'fields': "sex, bdate, city",
                                                'v': '5.131'})
        for data in response:
            first_name = data['first_name']
            last_name = data['last_name']
            vk_id = data['id']
            user_birthday = data.get('bdate')
            user_birthday = None if user_birthday is None else user_birthday
            user_sex = data['sex']
            user_city = data.get('city', {}).get('id')
            user_city = None if user_city is None else user_city

            return insert_users_vk(first_name, last_name, vk_id, user_birthday, user_sex, user_city)
    def find_city(self, user_id):
        while True:
            self.write_msg(user_id, 'Введите город для поиска: ')
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    city_name = event.text
                    city_nameid = self.user.method('database.getCities', {
                        'q': city_name,
                        'count': '1'})['items']
                    if len(city_nameid) > 0:
                        for data in city_nameid:
                            return data['id']
                    else:
                        self.write_msg(user_id, 'Город не найден, попробуйте еще раз.')


    def calculate_age(self, birthdate):
        birthdate = datetime.strptime(birthdate, '%d.%m.%Y')
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age

    def find_users(self, user_id, search_params):
        if not search_params:
                # Получаем значение параметра age_from из базы данных
                age_from = select_param_user(user_id)[3]
                if not age_from or len(age_from) < 5:
                    age_from = self.age_from(user_id)
                if "." in str(age_from) and len(str(age_from).split(".")) == 3:
                    age_from = self.calculate_age(age_from)

                # Получаем значение параметра city из базы данных
                city = select_param_user(user_id)[2]
                if not city:
                    city = self.find_city(user_id)

                search_params.update({
                    'v': '5.131',
                    'sex': 2 if int(select_param_user(user_id)[0]) == 1 else 1,
                    'age_from': age_from,
                    'city': city,
                    'fields': 'is_closed, id, first_name, last_name',
                    'status': '1' or '6',
                    'has_photo': '1',
                    'count': 999
                })

        try:
            # Выполняем запрос к VK API для поиска пользователей
            response = self.user.method('users.search', search_params)['items']

            # Обрабатываем результаты поиска
            users_list = []
            if not response:
                self.write_msg(user_id, 'Попробуйте еще раз.')
            else:
                for data in response:
                    if data["is_closed"] == False:
                        # проверяем, был ли этот пользователь уже просмотрен
                        viewed_user = select_viewed_user(data['id'], user_id)
                        if viewed_user is None:
                            # формируем список пользователей
                            user = [data["first_name"].replace("'", ''), data["last_name"].replace("'", ''),
                                    "vk.com/id" + str(data["id"]), str(data["id"])]
                            users_list.append(user)
                        else:
                            # пользователь уже просмотрен, пропускаем его
                            pass

            # выводим информацию по каждой записи
            for user in users_list:
                yield user

        except Exception as e:
            # обрабатываем ошибку
            self.write_msg(user_id, f'Произошла ошибка: {e}. Попробуйте еще раз позже.')

    def find_photo(self, gen):
        person_id = gen[3]
        album_photo = self.user.method('photos.getAll', {'owner_id': person_id,
                                                         'album_id': 'profile',
                                                         'rev': '1',
                                                         'extended': '1',
                                                         'count': '200'})['items']
        album_photo.sort(key=lambda x: x['likes']['count'])
        album_photo = album_photo[-3:]
        list_photo = [f'photo{photo["owner_id"]}_{photo["id"]}' for photo in album_photo]
        return f'{",".join(list_photo)}'


    def next_user(self, user_id, gen, message):
        self.write_msg(user_id, f'{" ".join((gen)[:3])}')
        insert_viewed_user(user_id, gen[3], gen[2])
        self.vk.method('messages.send', {'user_id': user_id,
                                             'access_token': user_token,
                                             'message': message,
                                             'attachment': self.find_photo(gen),
                                             'random_id': 0})
        return



