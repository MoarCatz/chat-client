# This is not part of the actual server
# Run after generating users

import os
try:
    os.remove('../data/requests.db')
except:
    pass

import sqlite3, random

db = sqlite3.connect('../data/requests.db')
c = db.cursor()
c.execute('''CREATE TABLE requests
(from_who text,
to_who text,
message text)''')

users = {'user' + str(i) for i in range(11)}

for i in range(11):
    if random.randint(0, 1):
        usr = sqlite3.connect('../data/users.db')
        usr_c = usr.cursor()
        usr_c.execute('''SELECT friends FROM users WHERE name = ?''', ('user' + str(i),))
        friends = usr_c.fetchone()[0].split(',')
        friends.append('user' + str(i))
        rec = random.choice(list(users.difference(friends)))
        c.execute('''INSERT INTO requests VALUES
        (?,?,"Hey, add me")''', ('user' + str(i), rec))
        
db.commit()
db.close()
