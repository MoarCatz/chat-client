import json, logging
from processors import Processor, cc, sc, BadRequest

import os

class RequestHandler:
    pr = Processor()
    handler_map = {
        cc.register: pr.register,
        cc.login: pr.login,
        cc.search_username: pr.search_username,
        cc.friends_group: pr.friends_group,
        cc.get_message_history: pr.message_history,
        cc.send_message: pr.send_message,
        cc.change_profile_section: pr.change_profile_section,
        cc.add_to_blacklist: pr.add_to_blacklist,
        cc.delete_from_friends: pr.delete_from_friends,
        cc.send_request: pr.send_request,
        cc.delete_profile: pr.delete_profile,
        cc.logout: pr.logout,
        cc.create_dialog: pr.create_dialog,
        cc.get_profile_info: pr.profile_info,
        cc.remove_from_blacklist: pr.remove_from_blacklist,
        cc.take_request_back: pr.take_request_back,
        cc.confirm_add_request: pr.confirm_add_request,
        cc.add_to_favorites: pr.add_to_favorites,
        cc.delete_dialog: pr.delete_dialog,
        cc.search_msg: pr.search_msg,
        cc.get_add_requests: pr.add_requests,
        cc.decline_add_request: pr.decline_add_request,
        cc.set_image: pr.set_image
    }
    set_image_code = str(cc.set_image.value).encode()
    profile_info_code = str(sc.profile_info.value).encode()

    def unpack_req(self, request):
        """Распаковывает запрос request"""
        if request[:2] == self.set_image_code:
            comma_idx = 0
            for i in range(4):
                comma_idx += request[comma_idx:].find(b',') + 1
            body, img = request[:comma_idx - 1], request[comma_idx:]
            code, *data = json.loads('[' + body.decode() + ']')
            data.append(img)
            return code, data

        code, *data = json.loads('[' + request.decode() + ']')
        return code, data

    def unpack_resp(self, response):
        """Распаковывает ответ response"""
        if response[:2] == self.profile_info_code:
            comma_idx = 0
            for i in range(5):
                comma_idx += response[comma_idx:].find(b',') + 1
            body, img = response[:comma_idx - 1], response[comma_idx:]
            code, *data = json.loads('[' + body.decode() + ']')
            data.append(img)
            return code, data

        code, *data = json.loads('[' + response.decode() + ']')
        return code, data

    def run(self):
        """Главный цикл работы сервера,
        отвечающий за обработку запросов"""
        while True:
            # The following section imitates getting the request over an Internet connection, will be removed
            request = input()
            address = '127.0.0.1'
            with open('request', 'w', encoding = 'utf-8') as f:
                f.write(request)
            with open('request', 'rb') as f:
                request = f.read()
            os.remove('request')

            log.info('received request from {}'.format(address))
            log.debug('request: {}'.format(request))
            try:
                code, data = self.unpack_req(request)
            except ValueError:
                log.error('failed to decode request {}'.format(request))
                print('\nDecode Error\n')
                continue

            print()
            try:
                handler = self.handler_map[code]
                log.info('processing request with ' + handler.__name__ + '()')
                if address != data[1]:
                    print(address, data[1])
                    log.error('IP address in the request does not match the actual one, ignoring request')
                    continue
                response = handler(*data)
            except (TypeError, IndexError, BadRequest):
                log.error('bad request from {}: {}'.format(address, request))
                print('Bad Request\n')
                continue
            r_code, r_data = self.unpack_resp(response)
            log.info('response code: ' + sc(r_code).name)
            log.debug('response: {}'.format(response))
            print(r_code, r_data)
            print(sc(r_code).name)
            print()
            print(response)
            print()

if __name__ == '__main__':
    # Will be removed
    try:
        os.remove('server.log')
    except:
        pass

    log_level = logging.DEBUG

    log = logging.Logger('request_handler')
    log.setLevel(log_level)

    log_handler = logging.FileHandler('server.log')
    log_handler.setLevel(log_level)

    log_fmt = logging.Formatter('[{asctime}] [{levelname}]\n{message}\n',
                                datefmt = '%d-%m %H:%M:%S', style = '{')
    log_handler.setFormatter(log_fmt)

    log.addHandler(log_handler)

    log.info('starting up')
    try:
        RequestHandler().run()
    except KeyboardInterrupt:
        log.info('manual exit')
    except Exception as e:
        log.exception('exception occured')
        log.critical('emergency exit')
