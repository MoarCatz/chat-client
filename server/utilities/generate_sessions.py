# This is not part of the actual server
# Independent execution

import os
try:
    os.remove('../data/sessions.db')
except:
    pass

import sqlite3, random
from hashlib import sha256

online = {'user' + str(random.randint(0, 10)) for i in range(random.randint(2, 10))}

def get_ip(st):
    num = st[4:]
    return '.'.join([num] * 4)

db = sqlite3.connect('../data/sessions.db')
c = db.cursor()
c.execute('''CREATE TABLE sessions
         (name text,
          session_id text UNIQUE,
          ip text)''')

for i in online:
    sha = sha256((get_ip(i) + i).encode())
    c.execute('''INSERT INTO sessions VALUES
    (?,?,?)''', (i,
    sha.hexdigest(),
    get_ip(i)))

db.commit()
db.close()
