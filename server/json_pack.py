import json
from enum import IntEnum
from time import time
from random import randint

def pack(data):
    return json.dumps(data, separators = (',', ':'))

def packed_info(data, message):
    print(message)
    print(pack(data)[1:-1])
    print()

class ClientCodes(IntEnum):
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

def main():
    cc = ClientCodes
    sc = ServerCodes

    # Request map ---------------

    c_to_s = {
    cc.register: [sc.register_error,
    sc.register_succ],

    cc.login:
    [sc.login_error, sc.login_succ],

    cc.search_username:
    sc.search_username_result,

    cc.friends_group:
    sc.friends_group_response,

    cc.get_message_history:
    sc.message_history,

    cc.send_message:
    sc.message_received,

    cc.change_profile_section:
    sc.change_profile_section_succ,

    cc.add_to_blacklist:
    sc.add_to_blacklist_succ,

    cc.delete_from_friends:
    sc.delete_from_friends_succ,

    cc.send_request:
    sc.send_request_succ,

    cc.delete_profile:
    sc.delete_profile_succ,

    cc.logout:
    sc.logout_succ,

    cc.create_dialog:
    sc.create_dialog_succ,

    cc.get_profile_info:
    sc.profile_info,

    cc.remove_from_blacklist:
    sc.remove_from_blacklist_succ,

    cc.take_request_back:
    sc.take_request_back_succ,

    cc.confirm_add_request:
    sc.confirm_add_request_succ,

    cc.add_to_favorites:
    sc.add_to_favorites_succ,

    cc.delete_dialog:
    sc.delete_dialog_succ,

    cc.search_msg:
    sc.search_msg_result,

    cc.remove_from_favorites:
    sc.remove_from_favorites_succ,

    cc.get_add_requests:
    sc.add_requests,

    cc.decline_add_request:
    sc.decline_add_request_succ,

    cc.set_image:
    sc.set_image_succ
    }

    s_to_c = {
    sc.new_message:
    cc.new_message_received,

    sc.friends_group_update:
    cc.friends_group_update_succ,

    sc.new_add_request:
    cc.new_add_request_received,

    sc.add_request_confirm:
   cc.add_request_confirm_received,

    sc.add_request_decline:
   cc.add_request_decline_received
    }

    # Data passing --------------

    print('Client -> Server\n\n')

    data = (cc.register, 'request_id', 'crypt_nick', 'hash_crypt_salt_pswd', 'ip')
    packed_info(data, 'Register')

    data = (cc.login, 'request_id', 'crypt_nick', 'hash_crypt_salt_pswd', 'ip')
    packed_info(data, 'Login')

    data = (cc.search_username, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Search for a username')

    data = (cc.friends_group, 'request_id', 'session_id', 'ip')
    packed_info(data, 'Get the list of user groups (online, etc.)')

    data = (cc.get_message_history, 'request_id', 'session_id', 0, 'dialog', 'ip')
    packed_info(data, 'Retrieve last n messages (0 to get all)')

    int_timestamp = int(time())
    # msg_id is assigned by a server
    data = (cc.send_message, 'request_id', 'session_id', 'crypt_mycrypt_msg', int_timestamp, 'crypt_dialog', 'ip')
    packed_info(data, 'Send a message')

    data = (cc.new_message_received, 'request_id')
    packed_info(data, 'Response to confirm that the message was received')

    section = 0   # [0;3]
    data = (cc.change_profile_section, 'request_id', 'session_id', section, 'crypt_change', 'ip')
    packed_info(data, 'Change a profile section')

    data = (cc.add_to_blacklist, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Add to blacklist')

    data = (cc.delete_from_friends, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Delete from friends')

    data = (cc.send_request, 'request_id', 'session_id', 'crypt_nick', 'crypt_msg', 'ip')
    packed_info(data, 'Send an add request')

    data = (cc.delete_profile, 'request_id', 'session_id', 'ip')
    packed_info(data, 'Delete profile')

    data = (cc.friends_group_update_succ, 'request_id')
    packed_info(data, 'Confirm the group update')

    data = (cc.new_add_request_received, 'request_id')
    packed_info(data, 'Confirm that a new request notification was received')

    data = (cc.add_request_confirm_received, 'request_id')
    packed_info(data, 'Confirm that a confirm of an add request was received')

    data = (cc.logout, 'request_id', 'session_id')
    packed_info(data, 'Request to log out')

    data = (cc.create_dialog, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Create a dialog with a friend')

    data = (cc.get_profile_info, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Get profile info')

    data = (cc.remove_from_blacklist, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Remove a user from blacklist')

    data = (cc.take_request_back, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Take back an add request')

    data = (cc.confirm_add_request, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Confirm an add request')

    data = (cc.add_to_favorites, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Add to favorites')

    data = (cc.delete_dialog, 'request_id', 'session_id', 'crypt_dialog', 'ip')
    packed_info(data, 'Delete a dialog')

    data = (cc.add_request_decline_received, 'request_id')
    packed_info(data, 'Confirm that a decline of an add request was received')

    data = (cc.search_msg, 'request_id', 'session_id', 'crypt_dialog', 'crypt_text', 'ip')
    packed_info(data, 'Search for a message containing the given text in a given time period')

    data = (cc.remove_from_favorites, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Remove from favorites')

    data = (cc.get_add_requests, 'request_id', 'session_id', 'ip')
    packed_info(data, 'Get add requests')

    data = (cc.decline_add_request, 'request_id', 'session_id', 'crypt_nick', 'ip')
    packed_info(data, 'Decline an add request')

    data = (cc.set_image, 'request_id', 'session_id', 'crypt_binary_img', 'ip')
    packed_info(data, 'Set the profile image')

    print('Server -> Client\n\n')

    data = (sc.login_error, 'request_id')
    packed_info(data, 'Login error')
    # Incorrect password

    data = (sc.register_error, 'request_id')
    packed_info(data, 'Register error')
    # Username in use

    data = (sc.login_succ, 'request_id', 'session_id')
    packed_info(data, 'Login successful')

    data = (sc.register_succ, 'request_id', 'session_id')
    packed_info(data, 'Registration successful')

    users = ['crypt_foo',
             'crypt_bar']
    data = (sc.search_username_result, 'request_id', users)
    packed_info(data, 'Username search result')

    user_groups = [
     ['crypt_nick1'],
     # online
     ['crypt_nick2'],
     # offline
     ['crypt_nick1'],
     # favorites
     ['crypt_nick3']]
     # blacklist
    data = (sc.friends_group_response, 'request_id', user_groups)
    packed_info(data, 'List of user groups (online, etc.)')

    msg_id = randint(0, 100)
    messages = [
        [msg_id, 'crypt_mycrypt_msg', int_timestamp, 'crypt_sender']]
    data = (sc.message_history, 'request_id', messages)
    packed_info(data, 'Response containing n messages')

    data = (sc.message_received, 'request_id')
    packed_info(data, 'Confirm that the message was received')

    data = (sc.new_message, 'request_id', messages[0], msg_id)
    packed_info(data, 'Send a new message to the client')

    data = (sc.change_profile_section_succ, 'request_id')
    packed_info(data, 'Confirm a change in a profile')

    data = (sc.friends_group_update, 'request_id',
    ['crypt_nick'],
    # online new
    ['crypt_nick1'])
    # offline new
    packed_info(data, 'Send an update of friends groups')

    data = (sc.add_to_blacklist_succ, 'request_id')
    packed_info(data, 'Confirm adding to blacklist')

    data = (sc.delete_from_friends_succ, 'request_id')
    packed_info(data, 'Confirm deleting fron friends')

    data = (sc.send_request_succ, 'request_id')
    packed_info(data, 'Confirm sending an add request')

    data = (sc.new_add_request, 'request_id')
    packed_info(data, 'Notify about a new add request')

    data = (sc.add_request_confirm, 'request_id', 'crypt_nick')
    packed_info(data, 'Notify that a user confirmed an add request')

    data = (sc.delete_profile_succ, 'request_id')
    packed_info(data, 'Confirm deletion of the profile')

    data = (sc.logout_succ, 'request_id')
    packed_info(data, 'Confirm the logout')

    data = (sc.create_dialog_succ, 'request_id')
    packed_info(data, 'Confirm creation of a dialog')

    data = (sc.profile_info, 'request_id', 'crypt_status', 'crypt_email', 'crypt_birthday', 'crypt_about')
    packed_info(data, 'Profile info')

    data = (sc.remove_from_blacklist_succ, 'request_id', 'Confirm removing from blacklist')

    data = (sc.take_request_back_succ, 'request_id')
    packed_info(data, 'Confirm taking back an add request')

    data = (sc.confirm_add_request_succ, 'request_id')
    packed_info(data, 'Confirm confirming an add request')

    data = (sc.add_to_favorites_succ, 'request_id')
    packed_info(data, 'Confirm adding to favorites')

    data = (sc.delete_dialog_succ, 'request_id')
    packed_info(data, 'Confirm deleting a dialog')

    data = (sc.add_request_decline, 'request_id', 'crypt_nick')
    packed_info(data, 'Notify that a user declined an add request')

    data = (sc.search_msg_result, 'request_id', messages)
    packed_info(data, 'Return a message search result')

    data = (sc.remove_from_favorites_succ, 'request_id')
    packed_info(data, 'Confirm removing from favorites')

    requests = [('crypt_nick1', 'crypt_msg')]
    data = (sc.add_requests, 'request_id', requests)

    data = (sc.decline_add_request_succ, 'request_id')
    packed_info(data, 'Confirm declining an add request')

    data = (sc.set_image_succ, 'request_id')
    packed_info(data, 'Confirm setting the profile image')

if __name__ == '__main__':
    main()
