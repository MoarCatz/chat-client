import sqlite3, json, re
from hashlib import md5
from enum import IntEnum

sample_img = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
              b'\x00\x00\x00\x01\x00\x00\x00\x01\x08'
              b'\x02\x00\x00\x00\x90wS\xde\x00\x00\x00'
              b'\x0cIDATx\x9cc```\x00\x00\x00\x04\x00'
              b'\x01\xf6\x178U\x00\x00\x00\x00IEND\xaeB`\x82')

class BadRequest(Exception):
    """Класс исключений для индикации логической ошибки в запросе"""

class ClientCodes(IntEnum):
    """Перечисление кодов запросов от клиента"""
    register = 0
    login = 1
    search_username = 2
    friends_group = 3
    get_message_history = 4
    send_message = 5
    new_message_received = 6
    change_profile_section = 7
    add_to_blacklist = 8
    delete_from_friends = 9
    send_request = 10
    delete_profile = 11
    friends_group_update_succ = 12
    new_add_request_received = 13
    add_request_confirm_received = 14
    logout = 15
    create_dialog = 16
    get_profile_info = 17
    remove_from_blacklist = 18
    take_request_back = 19
    confirm_add_request = 20
    add_to_favorites = 21
    delete_dialog = 22
    add_request_decline_received = 23
    search_msg = 24
    remove_from_favorites = 25
    get_add_requests = 26
    decline_add_request = 27
    set_image = 28

class ServerCodes(IntEnum):
    """Перечисление кодов запросов от сервера"""
    login_error = 0
    register_error = 1
    login_succ = 2
    register_succ = 3
    search_username_result = 4
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

# Quote SQL identifiers
# Add notificators about events

class Processor:
    def _contains(self, cont, st):
        """Показывает, является ли строка st одним из элементов
        строки cont, разделенных запятыми
        Для использования в качестве SQL-функции"""
        return int(st in cont.split(','))

    u_db = sqlite3.connect('data/users.db')

    u_db.row_factory = sqlite3.Row
    u_db.create_function('CONTAINS', 2, _contains)
    u_c = u_db.cursor()

    u_c.execute('''PRAGMA foreign_keys = 1''')

    m_db = sqlite3.connect('data/messages.db')
    m_db.row_factory = sqlite3.Row
    m_c = m_db.cursor()

    r_db = sqlite3.connect('data/requests.db')
    r_c = r_db.cursor()

    s_db = sqlite3.connect('data/sessions.db')
    s_db.row_factory = sqlite3.Row
    s_c = s_db.cursor()

    # Регулярное выражение для валидации имен пользователей
    nick_ptrn = re.compile('(?![ ]+)[\w ]{2,15}')

    def _add_session(self, nick, ip):
        """Добавляет пользователя nick по IP-адресу ip в таблицу сессий
        Вызывает BadRequest, если такая комбинация данных уже есть в таблице"""
        md = md5((ip + nick).encode())
        session_id = md.hexdigest()
        try:
            with self.s_db:
                self.s_c.execute('''INSERT INTO sessions
                                    VALUES (?, ?, ?)''', (nick, session_id, ip))
        except sqlite3.IntegrityError:
            raise BadRequest
        return session_id

    def _check_session(self, session_id, ip):
        """Проверяет, есть ли в таблице сессий запись с идентификатором id и IP-адресом ip
        Возвращает имя пользователя, записанного под этим идентификатором
        Вызывает BadRequest, если такой записи нет"""
        self.s_c.execute('''SELECT name FROM sessions
                            WHERE session_id = ? AND ip = ?''', (session_id, ip))
        nick = self.s_c.fetchone()
        if nick:
            return nick['name']
        raise BadRequest

    def _pack(self, *data):
        """Собирает данные data в формат для передачи
        Возвращает отформатированную байт-строку"""
        return json.dumps(data, separators = (',', ':'))[1:-1].encode()

    def _comma_split(self, st):
        """Получает из строки st, содержащей элементы, разделенные запятой, эти элементы
        Возвращает список элементов"""
        if st:
            return st.split(',')
        return []

    def _close_session(self, session_id):
        """Удаляет из таблицы сессий запись с идентификатором session_id"""
        with self.s_db:
            self.s_c.execute('''DELETE FROM sessions
                                WHERE session_id = ?''', (session_id,))

    def _remove_from(self, nick, item, sect):
        """Удаляет элемент item из графы sect в записи с именем nick
        Вызывает BadRequest, если пользователь nick не найден
        """
        self.u_c.execute('''SELECT {} FROM users
                            WHERE name = ?'''.format(sect), (nick,))

        prev = self.u_c.fetchone()
        if not prev:
            raise BadRequest
        data = prev[sect].split(',')
        try:
            data.remove(item)
        except ValueError:
            pass  # Если элемента нет, проигнорировать исключение
        with self.u_db:
            self.u_c.execute('''UPDATE users SET {} = ?
                                WHERE name = ?'''.format(sect), (','.join(data), nick))

    def _is_blacklisted(self, nick, user):
        """Проверяет, находится ли nick в черном списке user"""
        if nick == user:
            return False
        self.u_c.execute('''SELECT blacklist FROM users
                            WHERE name = ? AND CONTAINS(blacklist, ?)''', (user, nick))
        return bool(self.u_c.fetchone())

    def _remove_add_request(self, nick, user):
        """Удаляет запрос от nick к user"""
        with self.r_db:
            self.r_c.execute('''DELETE FROM requests
                                WHERE from_who = ? AND to_who = ?''', (nick, user))

    def _add_to(self, nick, item, sect):
        """Добавляет элемент item к графе sect в записи с именем nick
        Вызывает BadRequest, если пользователь nick не найден"""
        self.u_c.execute('''SELECT {} FROM users
                            WHERE name = ?'''.format(sect), (nick,))

        prev = self.u_c.fetchone()
        if not prev:
            raise BadRequest
        data = self._comma_split(prev[sect])
        if item in data:
            return  # Если элемент уже есть, не добавлять его еще раз
        data.append(item)
        with self.u_db:
            self.u_c.execute('''UPDATE users SET {} = ?
                                WHERE name = ?'''.format(sect), (','.join(data), nick))

    def _user_in_dialog(self, user, dialog):
        """Проверяет, что диалог под номером dialog есть
        в графе диалогов пользователя user
        Вызывает BadRequest, если пользователь не найден,
        диалога dialog нет в графе или dialog не является целым числом"""
        if not isinstance(dialog, int):
            raise BadRequest
        self.u_c.execute('''SELECT dialogs FROM users
                            WHERE name = ? AND CONTAINS(dialogs, ?)''', (user, str(dialog)))
        if not self.u_c.fetchone():
            raise BadRequest

    def _delete_dialog(self, dialog, user):
        """Удаляет диалог под номером dialog по запросу пользователя user
        Если собеседник удалил для себя этот диалог, таблица диалога удаляется.
        Иначе пользователь, от кого поступил запрос на удаление,
        помечается как удаливший этот диалог для себя"""
        self.m_c.execute('''SELECT sender FROM d{}
                            WHERE sender != ?'''.format(dialog), (user,))
        sender = self.m_c.fetchone()
        if not sender or sender['sender'][0] == '~':
            self.m_c.execute('''DROP TABLE d{}'''.format(dialog))
        else:
            self.m_c.execute('''UPDATE d{} SET sender = '~' || ?1
                                WHERE sender = ?1'''.format(dialog), (user,))
        self._remove_from(user, dialog, 'dialogs')  # Диалог с номером dialog удаляется из диалогов пользователя user
        self.m_db.commit()

    def _user_exists(self, user):
        """Проверяет, что пользователь user существует
        Вызывает BadRequest в противном случае"""
        self.u_c.execute('''SELECT name FROM users
                            WHERE name = ?''', (user,))
        if not self.u_c.fetchone():
            raise BadRequest

    def _valid_nick(self, nick):
        """Проверяет, является ли nick допустимым именем пользователя"""
        return bool(re.fullmatch(nick_ptrn, nick))

    def _next_free_dialog(self):
        """Возвращает следующий свободный номер диалога"""
        self.m_c.execute('''SELECT name FROM sqlite_master''')
        dialogs = sorted(int(i['name'][1:]) for i in self.m_c.fetchall())
        for i in range(1, len(dialogs)):
            if dialogs[i] - dialogs[i - 1] != 1:
                return dialogs[i - 1] + 1
        return dialogs[i] + 1


    def register(self, request_id, ip, nick, pswd):
        """Зарегистрироваться с именем nick и хэшем pswd пароля"""
        # 0,"c75233dafc00e71181a1649a9741f75a","127.0.0.1","new_user","0caec022675fc5b13b8f3188bfe91468"
        if not self._valid_nick(nick):
            return self._pack(sc.register_error, request_id)

        try:
            with self.u_db:
                self.u_c.execute('''INSERT INTO users
                                    VALUES (?, ?, '', '', '', '')''', (nick, pswd))

                self.u_c.execute('''INSERT INTO profiles
                                    VALUES (?, '', '', 0, '', x'')''', (nick,))
        except sqlite3.IntegrityError:
            # Если пользователь с таким именем существует
            return self._pack(sc.register_error, request_id)

        session_id = self._add_session(nick, ip)
        return self._pack(sc.register_succ, request_id, session_id)

    def login(self, request_id, ip, nick, pswd):
        """Войти в систему с именем nick и хэшем pswd пароля"""
        #  1,"b4f8b9e82ab097ecc0c63803307be083","127.0.0.1","new_user","0caec022675fc5b13b8f3188bfe91468"
        self.u_c.execute('''SELECT name FROM users
                            WHERE name = ? AND password = ?''', (nick, pswd))
        if not self.u_c.fetchone():
            # Если такой комбинации имени-пароля нет
            return self._pack(sc.login_error, request_id)

        try:
            session_id = self._add_session(nick, ip)
        except BadRequest:
            return self._pack(sc.login_error, request_id)
        return self._pack(sc.login_succ, request_id, session_id)

    def search_username(self, request_id, ip, session_id, user):
        """Найти среди пользователей тех, чье имя содержит подстроку user"""
        # 2,"a2e6190b636ed13c2ccaea3f7e48fe09","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user1"
        self._check_session(session_id, ip)
        self.u_c.execute('''SELECT name FROM users
                            WHERE INSTR(name, ?)''', (user,))
        search_results = [row['name'] for row in self.u_c.fetchall()]
        return self._pack(sc.search_username_result, request_id, search_results)

    def friends_group(self, request_id, ip, session_id):
        """Получить список друзей, сгрупированных в списки:
        онлайн, оффлайн, избранные, черный список"""
        # 3,"afddae89eee058b3ac83faaa9997ad7d","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df"
        nick = self._check_session(session_id, ip)
        self.u_c.execute('''SELECT friends, favorites, blacklist FROM users
                            WHERE name = ?''', (nick,))
        friends, fav, bl = (self._comma_split(i) for i in self.u_c.fetchone())

        self.s_c.execute('''SELECT name FROM sessions''')
        online_all = {i['name'] for i in self.s_c.fetchall()}

        online = []
        offline = []
        for i in friends:
            if i in online_all:
                online.append(i)
            else:
                offline.append(i)
        return self._pack(sc.friends_group_response, request_id, [online, offline, fav, bl])

    def message_history(self, request_id, ip, session_id, count, dialog):
        """Получить count последних сообщений из диалога dialog
        Если count = 0, возвращает все сообщения
        Вызывает BadRequest, если count < 0"""
        # 4,"58778f90cde359791f41f0fae23c8ab4","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df",0,3
        if count < 0:
            raise BadRequest

        nick = self._check_session(session_id, ip)
        self._user_in_dialog(nick, dialog)

        self.m_c.execute('''SELECT * FROM d{}
                            ORDER BY timestamp'''.format(dialog))
        msgs = [tuple(i) for i in self.m_c.fetchall()]
        return self._pack(sc.message_history, msgs[-count:])

    def send_message(self, request_id, ip, session_id, msg, tm, dialog):
        """Отправить сообщение msg с временем tm в диалог под номером dialog
        Вызывает BadRequest, если отправитель находится в черном списке
        собеседника или длина сообщения превышает 1000 символов"""
        # 5,"c5b4fa4513a4a186a87d5252c5b44401","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","Hello, World!",146938168600,0
        max_msg_length = 1000
        if len(msg) > max_msg_length:
            raise BadRequest
        nick = self._check_session(session_id, ip)
        self._user_in_dialog(nick, dialog)

        self.m_c.execute('''SELECT sender FROM d{}
                            WHERE sender != ?'''.format(dialog), (nick,))
        user = self.m_c.fetchone()
        if user and self._is_blacklisted(nick, user['sender']):
            raise BadRequest

        with self.m_db:
            self.m_c.execute('''INSERT INTO d{}
                                VALUES (?, ?, ?)'''.format(dialog), (msg, tm, nick))
        return self._pack(sc.message_received, request_id)

    def change_profile_section(self, request_id, ip, session_id, sect, change):
        """Заменить секцию профиля sect на change
        Вызывает BadRequest, если дата рождения (секция 2)
        меняется на что-то кроме целого числа или указана несуществующая секция"""
        # 7,"daa2d58f534fd1cf286ff731172601be","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df",0,"test status"
        nick = self._check_session(session_id, ip)

        birthday = 2
        if not isinstance(change, int) and sect == birthday:
            raise BadRequest

        sections = {0: 'status',
                    1: 'email',
                    2: 'birthday',
                    3: 'about'}

        try:
            sect_name = sections[sect]
        except KeyError:
            raise BadRequest

        with self.u_db:
            self.u_c.execute('''UPDATE users SET {} = ?
                                WHERE name = ?'''.format(sect_name), (change, nick))
        return self._pack(sc.change_profile_section_succ, request_id)

    def add_to_blacklist(self, request_id, ip, session_id, user):
        """Добавить пользователя user в черный список
        Вызывает BadRequest, если отправитель пытается добавить себя"""
        # 8,"67283fe9ad7687864051688510f7a701","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user1"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        if nick == user:
            raise BadRequest
        self._remove_from(nick, user, 'friends')
        self._remove_from(nick, user, 'favorites')
        self._add_to(nick, user, 'blacklist')
        self._remove_add_request(nick, user)
        self._remove_add_request(user, nick)
        return self._pack(sc.add_to_blacklist_succ, request_id)

    def delete_from_friends(self, request_id, ip, session_id, user):
        """Удалить пользователя user из друзей"""
        # 9,"208d20401bc664c6bbdd859c95620d80","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user1"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        self._remove_from(nick, user, 'friends')
        self._remove_from(nick, user, 'favorites')
        return self._pack(sc.delete_from_friends_succ, request_id)

    def send_request(self, request_id, ip, session_id, user, msg):
        """Отправить пользователю user запрос на добавление с сообщением msg
        Вызывает BadRequest, если уже отправлен запрос этому пользователю
        или отправитель пытается отправить запрос на добавление себе
        или тому, в чьем черном списке или друзьях он находится"""
        # 10,"6ea037902c53de5161356d979e81ce53","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user2","Test"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        if nick == user:
            raise BadRequest

        self.u_c.execute('''SELECT name FROM users
                            WHERE name = ? AND
                            CONTAINS(friends, ?2) > 0 OR CONTAINS(blacklist, ?2) > 0''', (user, nick))
        if self.u_c.fetchone():
            raise BadRequest

        self.r_c.execute('''SELECT from_who FROM requests
                            WHERE from_who = ?1 AND to_who = ?2 OR
                            from_who = ?2 AND to_who = ?1''', (user, nick))
        if self.r_c.fetchone():
            raise BadRequest

        with self.r_db:
            self.r_c.execute('''INSERT INTO requests
                                VALUES (?,?,?)''', (nick, user, msg))
        return self._pack(sc.send_request_succ, request_id)

    def delete_profile(self, request_id, ip, session_id):
        """Удалить свой профиль"""
        # 11,"416c3830ddeb76446caeed7284800935","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df"
        nick = self._check_session(session_id, ip)
        nick_tuple = (nick,)
        self.u_c.execute('''SELECT friends, dialogs FROM users
                            WHERE name = ? ''', nick_tuple)
        friends, messages = map(self._comma_split, self.u_c.fetchone())

        self.r_c.execute('''DELETE FROM requests
                            WHERE from_who = ?1 OR to_who = ?1''', nick_tuple)

        self._close_session(session_id)

        for i in friends:
            self._remove_from(i, nick, 'friends')
            self._remove_from(i, nick, 'favorites')

        for i in messages:
            self._delete_dialog(int(i), nick)

        self.u_c.execute('''DELETE FROM profiles
                            WHERE name = ?''', nick_tuple)
        self.u_c.execute('''DELETE FROM users
                            WHERE name = ?''', nick_tuple)

        self.u_c.execute('''SELECT name FROM users''')
        for i in self.u_c.fetchall():
            self._remove_from(i['name'], nick, 'blacklist')

        self.r_db.commit()
        self.u_db.commit()
        return self._pack(sc.delete_profile_succ, request_id)

    def logout(self, request_id, ip, session_id):
        """Выйти из системы"""
        # Tested 15,"93ce13538abff4f109bd198db7f1afce","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df"
        self._check_session(session_id, ip)
        self._close_session(session_id)
        return self._pack(sc.logout_succ, request_id)

    def create_dialog(self, request_id, ip, session_id, user):
        """Создать диалог с пользователем user
        Вызывает BadRequest, если пользователь user
        не находится в друзьях отправителя"""
        # 16,"fd3665a75038ea5460dd9be2458f3f74","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user3"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)

        self.u_c.execute('''SELECT name FROM users
                            WHERE name = ? AND CONTAINS(friends, ?)''', (user, nick))
        if not self.u_c.fetchone():
            raise BadRequest

        self.u_c.execute('''SELECT dialogs FROM users
                            WHERE name = ? OR name = ?''', (nick, user))
        dlg1 = set(self._comma_split(self.u_c.fetchone()['dialogs']))
        dlg2 = set(self._comma_split(self.u_c.fetchone()['dialogs']))

        if dlg1.intersection(dlg2):
            # Если у отправителя и пользователя user есть общий диалог
            return self._pack(sc.create_dialog_succ, request_id)

        d_st = str(self._next_free_dialog())
        with self.m_db:
            self.m_c.execute('''CREATE TABLE d{} (content text,
                                                  timestamp int,
                                                  sender text)'''.format(d_st))

        self._add_to(nick, d_st, 'dialogs')
        self._add_to(user, d_st, 'dialogs')
        return self._pack(sc.create_dialog_succ, request_id)

    def profile_info(self, request_id, ip, session_id, user):
        """Получить информацию о пользователе user
        Вызывает BadRequest, если отправитель находится
        в черном списке пользователя user"""
        # 17,"ca915530f94da4878efe2a535e587be0","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user0"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        if self._is_blacklisted(nick, user):
            raise BadRequest
        self.u_c.execute('''SELECT status, email, birthday, about, image FROM profiles
                            WHERE name = ?''', (user,))

        *info, img_data = tuple(self.u_c.fetchone())
        return self._pack(sc.profile_info, *info) + b',' + img_data

    def remove_from_blacklist(self, request_id, ip, session_id, user):
        """Удалить пользователя user из черного списка отправителя"""
        # 18,"186dfd552b41e6504475b967ad887ea8","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user1"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        self._remove_from(nick, user, 'blacklist')
        return self._pack(sc.remove_from_blacklist_succ, request_id)

    def take_request_back(self, request_id, ip, session_id, user):
        """Отменить запрос от отправителя к пользователю user"""
        # 19,"8643065ee11eba0a5512e2f9e9c32828","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user3"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        self._remove_add_request(nick, user)
        return self._pack(sc.take_request_back_succ, request_id)

    def confirm_add_request(self, request_id, ip, session_id, user):
        """Принять запрос на добавление от пользователя user отправителем
        Вызывает BadRequest, если пользователь user
        находится в черном списке отправителя"""
        # 20,"365546cd09dd0f811d40b75054fc880f","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user4"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        if self._is_blacklisted(user, nick):
            raise BadRequest
        self._remove_add_request(user, nick)
        self._add_to(user, nick, 'friends')
        self._add_to(nick, user, 'friends')
        return self._pack(sc.confirm_add_request_succ, request_id)

    def add_to_favorites(self, request_id, ip, session_id, user):
        """Добавить пользователя user в избранное отправителя
        Вызывает BadRequest, если пользователь user
        не находится в друзьях отправителя"""
        # 21,"39f70523475b979a673267f27b2d6b6f","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user3"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)

        self.u_c.execute('''SELECT name FROM users
                            WHERE name = ? AND CONTAINS(friends, ?)''', (nick, user))
        if not self.u_c.fetchone():
            raise BadRequest
        self._add_to(nick, user, 'favorites')
        return self._pack(sc.add_to_favorites_succ, request_id)

    def delete_dialog(self, request_id, ip, session_id, dialog):
        """Удалить диалог под номером dialog от лица отправителя
        Вызывает BadRequest, если dialog не является целым числом"""
        # 22,"14f2c0c8bb2c0296c354eca20167c38f","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df",0
        nick = self._check_session(session_id, ip)
        if not isinstance(dialog, int):
            raise BadRequest
        self._user_in_dialog(nick, dialog)
        self._delete_dialog(dialog, nick)
        return self._pack(sc.delete_dialog_succ, request_id)

    def search_msg(self, request_id, ip, session_id, dialog, text, lower_tm, upper_tm):
        """Найти в диалоге под номером dialog сообщение,
        содержащее строку text и отправленное между
        временами lower_tm и upper_tm
        Поднимает BadRequest, если lower_tm > upper_tm"""
        # 24,"c0ba5245d96bdb356d1337082fd7bdae","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df",1,"text",0,147068731300
        if lower_tm > upper_tm:
            raise BadRequest
        nick = self._check_session(session_id, ip)
        self._user_in_dialog(nick, dialog)
        self.m_c.execute('''SELECT * FROM d{}
                            WHERE INSTR(content, ?) AND
                            timestamp BETWEEN ? AND ?'''.format(dialog), (text, lower_tm, upper_tm))
        result = map(tuple, self.m_c.fetchall())
        return self._pack(sc.search_msg_result, request_id, list(result))

    def remove_from_favorites(self, request_id, ip, session_id, user):
        """Удалить пользователя user из избранного отправителя"""
        # 25,"25a357b1754a1c7d0cb9fcfbfd5c349e","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user0"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        self._remove_from(nick, user, 'favorites')
        return self._pack(sc.remove_from_favorites_succ, request_id)

    def add_requests(self, request_id, ip, session_id):
        """Получить запросы на добавление к отправителю"""
        # 26,"92958007536c86e1344eecb7cf2fb75c","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df"
        nick = self._check_session(session_id, ip)
        self.r_c.execute('''SELECT from_who, message FROM requests
                            WHERE to_who = ?''', (nick,))
        result = map(tuple, self.r_c.fetchall())
        return self._pack(sc.add_requests, list(result))

    def decline_add_request(self, request_id, ip, session_id, user):
        """Отменить запрос на добавление от пользователя user к отправителю"""
        # 27,"4725d6b4865af0cbf9988631a736b8e1","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df","user0"
        nick = self._check_session(session_id, ip)
        self._user_exists(user)
        self._remove_add_request(user, nick)
        return self._pack(sc.decline_add_request_succ, request_id)

    def set_image(self, request_id, ip, session_id, img_data):
        """Установить в качестве изображения пользователя картинку, бинарные данные которой находятся в img_data"""
        # 28,"d525adab0bb8e7f15afb94e189fec281","127.0.0.1","446f70d040ebb98c10d380a0ffaf83df",PNG
        nick = self._check_session(session_id, ip)
        with self.u_db:
            self.u_c.execute('''UPDATE profiles SET image = ?
                                WHERE name = ?''', (img_data, nick))
        return self._pack(sc.set_image_succ, request_id)
