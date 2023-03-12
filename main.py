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
        self.search_params_common = {
            'v': '5.131',
            'fields': 'is_closed, id, first_name, last_name',
            'has_photo': '1',
            'count': 1000
        }

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

    def find_users(self, user_id, params):
        if not params:
            age_from = select_param_user(user_id)[3]
            if not age_from or len(age_from) < 5:
                age_from = self.age_from(user_id)
            if "." in str(age_from) and len(str(age_from).split(".")) == 3:
                age_from = self.calculate_age(age_from)

            city = select_param_user(user_id)[2]
            if not city:
                city = self.find_city(user_id)
            age_to = age_from + 20
        else:
            age_from = self.age_from(user_id)
            age_to = self.age_to(user_id)
            city = self.find_city(user_id)

        search_params_common = self.search_params_common.copy()
        search_params_common.update({
            'sex': 2 if int(select_param_user(user_id)[0]) == 1 else 1,
            'age_from': age_from,
            'age_to': age_to,
            'city': city,
        })

        search_params_1 = {
            **search_params_common,
            'status': '6'
        }

        search_params_2 = {
            **search_params_common,
            'status': '1'
        }
        try:
            response_1 = self.user.method('users.search', search_params_1)['items']
            response_2 = self.user.method('users.search', search_params_2)['items']

            response = response_1 + response_2  # объединяем результаты двух запросов

            users_list = []

            if not response:
                self.write_msg(user_id, 'Попробуйте еще раз.')
            else:
                for data in response:
                    if data["is_closed"] == False:
                        viewed_user = select_viewed_user(data['id'], user_id)
                        if viewed_user is None:
                            user = [data["first_name"].replace("'", ''), data["last_name"].replace("'", ''),
                                    "vk.com/id" + str(data["id"]), str(data["id"])]
                            users_list.append(user)
                        else:
                            pass

            for user in users_list:
                yield user

        except Exception as e:
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
