#register:
 empty db
 
#login:
 registration
 
#search_username:
 login
 users:
  user1
  user10
 
#friends_group:
 login
 users:
  user1
  user10
  user2
  user3
 friends:
  user1
  user10
  user2
 online:
  user1
  user2
 offline:
  user10
 favorites:
  user2
 blacklist:
  user3
  
#get_message_history:
 login
 users:
  user1
 dialogs:
  new_user & user1
  
#send_message:
 get_message_history
 
#change_profile_section:
 login
 
#add_to_blacklist:
 login
 users:
  favorites:
   user2
  
#delete_from_friends:
 login
 users:
  friends:
   user2

#send_request:
 login
 users:
  user4

#delete_profile
 registration

#logout
 login

#create_dialog
 friends:
  user2

#get_profile_info
 users:
  user2
