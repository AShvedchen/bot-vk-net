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

    def delete_users_find(self, user_id):
        vk_id = user_id
        return delete_tables(vk_id)

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

    def find_users(self, user_id):
        # Получаем значение параметра sex из базы данных
        sex = select_param_user(user_id)[0]

        # Меняем значение sex на противоположное
        if int(sex) == 1:
            search_sex = 2
        else:
            search_sex = 1

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

        # Выполняем запрос к VK API для поиска пользователей
        response = self.user.method('users.search', {'v': '5.131',
                                                     'sex': search_sex,
                                                     'age_from': age_from,
                                                     'city': city,
                                                     'fields': 'is_closed, id, first_name, last_name',
                                                     'status': '1' or '6',
                                                     'has_photo': '1',
                                                     'count': 999})['items']

        # Обрабатываем результаты поиска
        for data in response:
            if data["is_closed"] == False:
                first_name = data["first_name"].replace("'", '')
                last_name = data["last_name"].replace("'", '')
                find_vk_id = str(data["id"])
                find_vk_link = "vk.com/id" + str(data["id"])
                insert_users_find(first_name, user_id, last_name, find_vk_id, find_vk_link)
        return self.write_msg(user_id, 'Поиск завершён')

    def find_users_param(self, user_id):
        sex = select_param_user(user_id)[0]
        if int(sex) == 1:
            search_sex = 2
        else:
            search_sex = 1
        response = self.user.method('users.search', {'v': '5.131',
                                                     'sex': search_sex,
                                                     'age_from': self.age_from(user_id),
                                                     'age_to': self.age_to(user_id),
                                                     'city': self.find_city(user_id),
                                                     'fields': 'is_closed, id, first_name, last_name',
                                                     'status': '1' or '6',
                                                     'has_photo': '1',
                                                     'count': 999})['items']

        for data in response:
            if data["is_closed"] == False:
                first_name = data["first_name"].replace("'", '')
                last_name = data["last_name"].replace("'", '')
                find_vk_id = str(data["id"])
                find_vk_link = "vk.com/id" + str(data["id"])
                insert_users_find(first_name, user_id, last_name, find_vk_id, find_vk_link)
        return self.write_msg(user_id, 'Поиск завершён')

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
