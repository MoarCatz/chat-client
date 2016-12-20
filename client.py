from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.websocket import websocket_connect
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from queue import Queue

from hashlib import md5, sha256
from random import randint
from base64 import b64encode, b64decode
import rsa, json, os, pyaes


class ClientCodes():
    """Перечисление кодов запросов от клиента"""
    register = 0
    login = 1
    get_search_list = 2
    friends_group = 3
    get_message_history = 4
    send_message = 5
    change_profile_section = 6
    add_to_blacklist = 7
    delete_from_friends = 8
    send_request = 9
    delete_profile = 10
    logout = 11
    create_dialog = 12
    get_profile_info = 13
    remove_from_blacklist = 14
    take_request_back = 15
    confirm_add_request = 16
    add_to_favorites = 17
    delete_dialog = 18
    search_msg = 19
    remove_from_favorites = 20
    get_add_requests = 21
    decline_add_request = 22
    set_image = 23


class ServerCodes():
    """Перечисление кодов запросов от сервера"""
    login_error = 0
    register_error = 1
    login_succ = 2
    register_succ = 3
    search_list = 4
    friends_group_response = 5
    message_history = 6
    message_received = 7
    new_message = 8
    change_profile_section_succ = 9
    friends_group_update = 10
    add_to_blacklist_succ = 11
    delete_from_friends_succ = 12
    send_request_succ = 13
    new_add_request = 14
    add_request_confirm = 15
    delete_profile_succ = 16
    logout_succ = 17
    create_dialog_succ = 18
    profile_info = 19
    remove_from_blacklist_succ = 20
    take_request_back_succ = 21
    confirm_add_request_succ = 22
    add_to_favorites_succ = 23
    delete_dialog_succ = 24
    add_request_decline = 25
    search_msg_result = 26
    remove_from_favorites_succ = 27
    add_requests = 28
    decline_add_request_succ = 29
    set_image_succ = 30


cc = ClientCodes
sc = ServerCodes

code_map = {cc.register:                 [sc.register_error, sc.register_succ],
            cc.login:                    [sc.login_error, sc.login_succ],
            cc.get_search_list:          sc.search_list,
            cc.friends_group:            sc.friends_group_response,
            cc.get_message_history:      sc.message_history,
            cc.send_message:             sc.message_received,
            cc.change_profile_section:   sc.change_profile_section_succ,
            cc.add_to_blacklist:         sc.add_to_blacklist_succ,
            cc.delete_from_friends:      sc.delete_from_friends_succ,
            cc.send_request:             sc.send_request_succ,
            cc.delete_profile:           sc.delete_profile_succ,
            cc.logout:                   sc.logout_succ,
            cc.create_dialog:            sc.create_dialog_succ,
            cc.get_profile_info:         sc.profile_info,
            cc.remove_from_blacklist:    sc.remove_from_blacklist_succ,
            cc.take_request_back:        sc.take_request_back_succ,
            cc.confirm_add_request:      sc.confirm_add_request_succ,
            cc.add_to_favorites:         sc.add_to_favorites_succ,
            cc.delete_dialog:            sc.delete_dialog_succ,
            cc.search_msg:               sc.search_msg_result,
            cc.remove_from_favorites:    sc.remove_from_favorites_succ,
            cc.get_add_requests:         sc.add_requests,
            cc.decline_add_request:      sc.decline_add_request_succ,
            cc.set_image:                sc.set_image_succ}

o_error_codes = {sc.register_error, sc.login_error}


class RequestSender:
    url = 'moarcatz-alexbagirov.c9users.io/'
    # Фиксированный URL сервера (без протокола, с обязятельным / на конце)
    response_queue = Queue()
    require_response = False

    async def _connect(self):
        """Устанавливает соединение с сервером по протоколу WSS"""
        req = HTTPRequest('wss://' + self.url,
                          headers={'Connection': 'Keep-Alive'})
        self.conn = await websocket_connect(req, io_loop = self.ioloop)
        self.server_key = await self._get_server_key()

        self.ioloop.add_callback(self._listen)

    async def _get_server_key(self):
        """Получает публичный ключ сервера"""
        cl = AsyncHTTPClient()
        resp = await cl.fetch('https://' + self.url + 'key')
        return rsa.PublicKey(*list(map(int, resp.body.decode().split(':'))))

    def _request_id(self):
        """Генерирует случайный идентификатор запроса"""
        return md5(str(randint(0, 10000000)).encode()).hexdigest()

    def _pack(self, *data):
        """Собирает данные data в формат для передачи
        Возвращает отформатированную байт-строку"""
        return json.dumps(data, separators = (',', ':'))[1:-1].encode()

    def _unpack_resp(self, response):
        """Распаковывает ответ response"""
        if response[:2] == str(sc.profile_info).encode():
            comma_idx = 0
            for i in range(6):
                comma_idx += response[comma_idx:].find(b',') + 1
            body, img = response[:comma_idx - 1], response[comma_idx:]
            code, *data = json.loads('[' + body.decode() + ']')
            data.append(img)
            return code, data

        code, resp_id, *data = json.loads('[' + response.decode() + ']')
        return code, resp_id, data

    async def _listen(self):
        while True:
            msg = await self.conn.read_message()
            if msg is None:
                print("connection closed")
                break
            if self.require_response:
                self.response_queue.put(msg)
                self.require_response = False
            else:
                print(msg)

    async def _send(self, code, req_id, *data):
        """Отправляет запрос с кодом code и данными data
        на сервер в зашифрованном виде вместе с подписью
        Возвращает статус обработки запроса и данные ответа сервера"""
        request = self._pack(code, req_id, *data)

        key = os.urandom(32)
        aes_ctr = pyaes.AESModeOfOperationCTR(key)
        enc = aes_ctr.encrypt(request)

        enc_key = rsa.encrypt(key, self.server_key)
        sign = rsa.sign(enc, self.privkey, 'SHA-256')

        message = b':'.join(map(b64encode, (enc, sign, enc_key)))

        self.conn.write_message(message)
        self.require_response = True

    def _process(self, response, req_code, req_id):
        """Обрабатывает ответ сервера response
        В обработку входит:
         * декодирование
         * расшифровка
         * распаковка
        Возвращаемое значение варьируется. Если код ответа не соответствует
        коду запроса, возвращается False. Возвращается также соответствие ID
        запроса и ответа. Если ответ сервера имеет данные, они возвращаются.
        Если запрос О-типа, возвращается корректность запроса"""
        enc_resp, enc_key = map(b64decode, response.decode().split(':'))
        key = rsa.decrypt(enc_key, self.privkey)

        aes = pyaes.AESModeOfOperationCTR(key)
        resp = aes.decrypt(enc_resp)

        # In the future, make the server also send a signature
        resp_code, resp_id, *resp_data = json.loads('[' + resp.decode() + ']')

        # Better to raise an exception in case of failure
        if isinstance(code_map[req_code], list):
            if resp_code not in code_map[req_code]:
                return False
            return resp_code not in o_error_codes, req_id == resp_id
        else:
            if resp_code != code_map[req_code]:
                return False

        if not resp_data:
            return req_id == resp_id
        return req_id == resp_id, resp_data

    def register(self, nick, pswd):
        """Создает новый аккаунт с данными входа nick, pswd
        Не возвращает данные"""
        self.pubkey, self.privkey = rsa.newkeys(2048, accurate = False)
        key = ':'.join(map(str, self.pubkey.__getstate__()))

        pswd_hash = sha256(pswd.encode()).hexdigest()
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.register, req_id, nick,
                                 pswd_hash, key)

        response = self.response_queue.get()
        status, id_match = self._process(response, cc.register, req_id)
        return status, id_match

    def login(self, nick, pswd):
        """Открывает новую сессию с данными входа nick, pswd
        Не возвращает данные"""
        self.pubkey, self.privkey = rsa.newkeys(2048, accurate = False)
        key = ':'.join(map(str, self.pubkey.__getstate__()))

        pswd_hash = sha256(pswd.encode()).hexdigest()
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.login, req_id, nick,
                                 pswd_hash, key)

        response = self.response_queue.get()
        status, id_match = self._process(response, cc.login, req_id)
        return status, id_match

    def get_search_list(self):
        """Возвращает список пользователей для поиска"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.get_search_list, req_id)
        response = self.response_queue.get()
        id_match, user_list = self._process(response, cc.get_search_list,
                                            req_id)
        return id_match, user_list

    def get_friends_group(self):
        """Возвращает список друзей
        Формат: [онлайн, оффлайн, избранное, заблокированные]`"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.friends_group, req_id)
        response = self.response_queue.get()
        id_match, friends_group = self._process(response, cc.friends_group,
                                                req_id)
        return id_match, friends_group

    def get_message_history(self, count, dialog):
        """Получает count последних сообщений из диалога dialog
        Возвращает сообщения в формате `(текст, время, отправитель)`"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.get_message_history, req_id,
                                 count, user)
        response = self.response_queue.get()
        id_match, msg_history = self._process(response, cc.get_message_history,
                                              req_id)
        return id_match, msg_history

    def send_message(self, msg, tm, dialog):
        """Отправляет сообщение msg с временем tm в диалог dialog
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.send_message, req_id,
                                 msg, tm, dialog)
        response = self.response_queue.get()
        id_match = self._process(response, cc.send_message, req_id)
        return id_match

    def change_profile_section(self, sect, change):
        """Устанавливает в секцию профиля sect значение change
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.change_profile_section, req_id,
                                 sect, change)
        response = self.response_queue.get()
        id_match = self._process(response, cc.change_profile_section, req_id)
        return id_match

    def add_to_blacklist(self, user):
        """Добавляет пользователя user в заблокированные
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.add_to_blacklist, req_id, user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.add_to_blacklist, req_id)
        return id_match

    def delete_from_friends(self, user):
        """Удаляет пользователя user из друзей
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.delete_from_friends, req_id,
                                 user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.delete_from_friends, req_id)
        return id_match

    def send_request(self, user, msg):
        """Отправляет исходящий запрос пользователю user с сообщением msg
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.send_request, req_id,
                                 user, msg)
        response = self.response_queue.get()
        id_match = self._process(response, cc.send_request, req_id)
        return id_match

    def delete_profile(self):
        """Удаляет профиль пользователя
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.delete_profile, req_id)
        response = self.response_queue.get()
        id_match = self._process(response, cc.delete_profile, req_id)
        if id_match:
            self.pubkey = self.privkey = None
            return True
        return False

    def logout(self):
        """Закрывает активную сессию пользователя
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.logout, req_id)
        response = self.response_queue.get()
        id_match = self._process(response, cc.logout, req_id)
        if id_match:
            self.pubkey = self.privkey = None
            return True
        return False

    def create_dialog(self, user):
        """Создает диалог с пользователем user или находит существующий
        Возвращает номер диалога"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.create_dialog, req_id, user)
        response = self.response_queue.get()
        id_match, dialog = self._process(response, cc.create_dialog, req_id)
        return id_match, dialog

    def get_profile_info(self, user):
        """Получает информацию о профиле user
        Формат: `(статус, почта, день_рождения, о_себе, аватар)`"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.get_profile_info, req_id, user)
        response = self.response_queue.get()
        id_match, data = self._process(response,
                                       cc.get_profile_info,
                                       req_id)
        *profile_info, img = data
        profile_info.append(b64decode(img))
        return id_match, profile_info

    def remove_from_blacklist(self, user):
        """Убирает пользователя user из заблокированных
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.remove_from_blacklist, req_id,
                                 user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.remove_from_blacklist, req_id)
        return id_match

    def take_request_back(self, user):
        """Отменяет исходящий запрос пользователю user
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.take_request_back, req_id,
                                 user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.take_request_back, req_id)
        return id_match

    def confirm_add_request(self, user):
        """Подтверждает входящий запрос от пользователя user
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.confirm_add_request, req_id,
                                 user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.confirm_add_request, req_id)
        return id_match

    def add_to_favorites(self, user):
        """Добавляет пользователя user в избранное
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.add_to_favorites, req_id, user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.add_to_favorites, req_id)
        return id_match

    def delete_dialog(self, dialog):
        """Удаляет диалог dialog
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.delete_dialog, req_id, dialog)
        response = self.response_queue.get()
        id_match = self._process(response, cc.delete_dialog, req_id)
        return id_match

    def search_msg(self, dialog, text, lower_tm, upper_tm):
        """Ищет сообщение, содержащее text в диалоге dialog в промежутке
        времени между lower_tm и upper_tm
        Возвращает соообщения в формате `(текст, время, отправитель)`"""
        req_id = self._request_id()
        response = self._send(cc.search_msg, req_id,
                              dialog, text, lower_tm, upper_tm)
        id_match, search_results = self._process(response, cc.search_msg,
                                                 req_id)
        return id_match, search_results

    def remove_from_favorites(self, user):
        """Убирает пользователя user из избранного
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.remove_from_favorites, req_id,
                                 user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.remove_from_favorites,)
        return id_match

    def get_add_requests(self):
        """Возвращает входящие запросы
        Форма: `[(отправитель, сообщение, статус), # входящие
                 (адресат, сообщение, статус)] # исходящие`"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.get_add_requests, req_id)
        response = self.response_queue.get()
        id_match, add_requests = self._process(response, cc.get_add_requests,
                                               req_id)
        return id_match, add_requests

    def decline_add_request(self, user):
        """Отменяет входящий запрос от пользователя user
        Не возвращает данные"""
        req_id = self._request_id()
        self.ioloop.add_callback(self._send, cc.decline_add_request, req_id,
                                 user)
        response = self.response_queue.get()
        id_match = self._process(response, cc.decline_add_request, req_id)
        return id_match

    def set_image(self, img_data):
        """Устанавливает бинарные данные картинки img_data как аватар
        Не возвращает данные"""
        req_id = self._request_id()
        response = self._send(cc.set_image, req_id, b64encode(img_data))
        id_match = self._process(response, cc.set_image, req_id)
        return id_match

    def __init__(self):
        self.ioloop = IOLoop.current()
        self.conn = None
        self.server_key = None

        # Call _connect on the next I/O loop iteration
        self.ioloop.add_callback(self._connect)

    def run(self):
        self.ioloop.start()