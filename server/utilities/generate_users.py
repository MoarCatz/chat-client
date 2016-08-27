# This is not part of the actual server
# Run after generating messages

import os
try:
    os.remove('../data/users.db')
except:
    pass

import sqlite3, random
from hashlib import sha256

def cjoin(ls):
    return ','.join(map(str, ls))

def get_dialogs(name):
    db = sqlite3.connect('../data/messages.db')
    c = db.cursor()
    res = []
    for i in range(16):
        c.execute('''SELECT sender FROM d{} WHERE sender = ?'''.format(i), (name,))
        if c.fetchone():
            res.append(i)
    return res

db = sqlite3.connect('../data/users.db')
db.row_factory = sqlite3.Row
c = db.cursor()

users = ['user' + str(i) for i in range(11)]

c.execute('''PRAGMA foreign_keys = 1''')

c.execute('''CREATE TABLE users
    (name text PRIMARY KEY,
     password text,

     friends text,
     favorites text,
     blacklist text,
     dialogs text)''')

c.execute('''CREATE TABLE profiles
 (name text PRIMARY KEY
  REFERENCES users(name),
  status text,
  email text,
  birthday int,
  about text,
  image blob)''')

for user in users:
    pswd = (user + '2016')[::-1] + 'mysalt'
    sha = sha256(pswd.encode())

    friends = list({random.choice(users) for i in range(random.randint(1,5))})
    favorites = random.choice(friends)
    blacklist = random.choice(list(set(users).difference(friends)))
    dl = cjoin(get_dialogs(user))
    c.execute('''INSERT INTO users VALUES
    (?,?,?,?,?,?)''',
    (user,
    sha.hexdigest(),
    cjoin(friends),
    favorites,
    blacklist,
    dl))

    c.execute('''INSERT INTO profiles VALUES
    (?,?,?,?,?,?)''',
    (user,
    '',
    'undefined',
    1355292732,
    'I am ' + user,
    b'lolno'))

db.commit()
db.close()
