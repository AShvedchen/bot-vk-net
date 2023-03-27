from datetime import datetime, date
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.exceptions import ApiError, AuthError, VkApiError
from database_bot import *
from data_config import *
from vkinder_keyboard import keyboard


def calculate_age(birthdate):
    birthdate = datetime.strptime(birthdate, '%d.%m.%Y')
    today = date.today()
    age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return age


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
        try:
            self.vk.method('messages.send', {'user_id': user_id,
                                             'message': message,
                                             'keyboard': keyboard,
                                             'random_id': get_random_id()})
        except (KeyError, ApiError, AuthError, VkApiError) as e:
            print(f'Произошла ошибка при отправке сообщения: {e}.')

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

    def info_user(self, user_id):
        try:
            user_data = self.vk.method('users.get', {'user_ids': user_id,
                                                     'fields': "sex, bdate, city",
                                                     'v': '5.131'})[0]
        except (KeyError, ApiError, AuthError, VkApiError) as e:
            print(f'Произошла ошибка при запросе: {e}.')
        first_name = user_data['first_name']
        last_name = user_data['last_name']
        user_birthday = user_data.get('bdate', None)
        user_sex = user_data['sex']
        user_city = user_data.get('city', {}).get('id', None)
        return first_name, last_name, user_birthday, user_sex, user_city

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

    def find_users(self, user_id, params):
        if not params:
            age_from = self.info_user(user_id)[2]
            if not age_from or len(age_from) < 5:
                age_from = self.age_from(user_id)
            if "." in str(age_from) and len(str(age_from).split(".")) == 3:
                age_from = calculate_age(age_from)

            city = self.info_user(user_id)[4]
            if not city:
                city = self.find_city(user_id)
            age_to = age_from + 20
        else:
            age_from = self.age_from(user_id)
            age_to = self.age_to(user_id)
            city = self.find_city(user_id)

        search_params_common = self.search_params_common.copy()
        search_params_common.update({
            'sex': 2 if int(self.info_user(user_id)[3]) == 1 else 1,
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
        except (KeyError, ApiError, AuthError, VkApiError) as e:
            print(f'Произошла ошибка при поиске: {e}.')
        response = response_1 + response_2  # объединяем результаты двух запросов
        print(len(response))
        users_list = []
        if not response:
            self.write_msg(user_id, 'Попробуйте еще раз.')
        else:
            for data in response:
                if not data["is_closed"]:
                    viewed_user = select_viewed_user(data['id'], user_id)
                    if viewed_user is None:
                        user_params = [data["first_name"], data["last_name"],
                                       "vk.com/id" + str(data["id"]), str(data["id"])]
                        users_list.append(user_params)
                    else:
                        pass
        for user_data in users_list:
            yield user_data

    def find_photo(self, gen):
        try:
            person_id = gen[3]
            album_photo = self.user.method('photos.getAll', {'owner_id': person_id,
                                                             'album_id': 'profile',
                                                             'rev': '1',
                                                             'extended': '1',
                                                             'count': '200'})['items']
            if not album_photo:
                avatar = self.user.method('users.get', {'user_ids': person_id,
                                                        'fields': 'photo_max'})[0]['photo_max']
                return avatar
        except (KeyError, ApiError, AuthError, VkApiError) as e:
            print(f'Произошла ошибка при поиске фото: {e}. ')

        album_photo.sort(key=lambda x: x['likes']['count'])
        album_photo = album_photo[-3:]
        list_photo = [f'photo{photo["owner_id"]}_{photo["id"]}' for photo in album_photo]
        return f'{",".join(list_photo)}'

    def next_user(self, user_id, gen, message):
        self.write_msg(user_id, f'{" ".join(gen[:3])}')
        insert_viewed_user(user_id, gen[3], gen[2])
        try:
            self.vk.method('messages.send', {'user_id': user_id,
                                             'access_token': user_token,
                                             'message': message,
                                             'attachment': self.find_photo(gen),
                                             'random_id': get_random_id()})
        except (KeyError, ApiError, AuthError, VkApiError) as e:
            print(f'Произошла ошибка: {e}. ')
        return
