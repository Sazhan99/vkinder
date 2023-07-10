import vk_api
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from vkinder.config import community_token, access_token, db_url_object
from vkinder.core import VkTools
from vkinder.data_store import user_exists_in_db, add_user, set_offset, Last_offset
from sqlalchemy.exc import NoResultFound

engine = create_engine(db_url_object)
session = Session(engine)


class BotInterface:

    def __init__(self, community_token, access_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.vk_tools = VkTools(access_token)
        self.longpoll = VkLongPoll(self.vk)
        self.params = {}
        self.worksheets = []
        self.init_offset_from_db()
        self.count = 1
        self.offset = 0

    def fetch_profiles(self):
        self.init_offset_from_db()
        profiles = self.vk_tools.search_users(self.params, self.offset, self.count)
        self.offset += self.count
        set_offset(engine, self.params['id'], self.offset)
        print(self.params['id'], self.offset)
        return profiles

    def process_search(self):
        profiles = self.fetch_profiles()

        not_found_profiles = []  # list of profiles not in the database

        while not not_found_profiles:
            for profile in profiles:
                if user_exists_in_db(engine, self.params['id'], profile['id']):
                    print(f"пользователь был посмотрен {profile['id']}")
                    continue
                else:
                    not_found_profiles.append(profile)

            # If we haven't found any new profiles, fetch more
            if not not_found_profiles:
                set_offset(engine, self.params['id'], self.offset)
                profiles = self.fetch_profiles()

        return not_found_profiles[0]  # return first found profile



    def init_offset_from_db(self):
        with Session(engine) as session:
            try:
                offset_entry = session.query(Last_offset).first()
                self.offset = offset_entry.offset if offset_entry else 0
            except NoResultFound:
                self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )
    def start(self):
        self.event_handler()

    def change_search_params(self, user_id):
        params = self.vk_tools.get_profile_info(user_id)
        all_params_received = True  # флаг для отслеживания получения всех параметров
        for param in params:
            if params[param] is None:
                all_params_received = False  # установка флага на False, если какой-то параметр не был получен
                self.message_send(user_id, f'Хотите изменить {param} в параметрах поиска? Ответьте "да" или "нет".')
                self.await_user_response(user_id)
        if all_params_received:
            self.message_send(user_id, 'Параметры поиска получены')
            return self.params

    def await_user_response(self, user_id):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.user_id == user_id:
                if event.text.lower() == 'да':
                    self.message_send(user_id, 'Введите название города:')
                    for response_event in self.longpoll.listen():
                        if (response_event.type == VkEventType.MESSAGE_NEW and
                                response_event.to_me and response_event.user_id == user_id):
                            if response_event.text.lower() == 'отмена':
                                self.message_send(user_id, 'Отменено изменение параметров поиска.')
                                break
                            else:
                                self.params['city'] = response_event.text
                                self.message_send(user_id, 'Параметр города успешно изменен.')
                                break
                elif event.text.lower() == 'нет':
                    self.message_send(user_id, 'Параметры города остаются без изменений.')
                break


    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()

                if command == 'привет':
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    # self.change_search_params(event.user_id)
                    self.message_send(event.user_id, f'Здравствуй {self.params["name"]}')

                elif command == 'поиск':
                    user = self.process_search()
                    photos_user = self.vk_tools.get_photos(user['id'])
                    user_url = f"https://vk.com/id{user['id']}"
                    attachments = []
                    for num, photo in enumerate(photos_user[:3]):
                        attachments.append(f'photo{photo["owner_id"]}_{photo["id"]}')
                        if num == 2:
                            break
                    status = self.vk_tools.get_status(user['id'])
                    self.message_send(event.user_id,
                                      (f'Встречайте {user["name"]}. '
                                       f'Ссылка на профиль: {user_url},\nстатус: {status}'),
                                      attachment=','.join(attachments))
                    add_user(engine, event.user_id, user['id'])
                    self.message_send(event.user_id, 'введите - поиск')

                elif command == 'пока':
                    self.message_send(event.user_id, 'пока')
                else:
                    self.message_send(event.user_id, 'Неизвестная команда')


if __name__ == '__main__':
    bot = BotInterface(community_token, access_token)
    bot.event_handler()