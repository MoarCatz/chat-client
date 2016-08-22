# This is not part of the actual server

import os
try:
    os.remove('../data/messages.db')
except:
    pass

import sqlite3, random
from time import time

db = sqlite3.connect('../data/messages.db')
c = db.cursor()

for file_id in range(16):
    c.execute('''CREATE TABLE d{}
    (content text, 
     timestamp int, 
     sender text)'''.format(file_id))
    users = [random.randint(0, 10), random.randint(0, 10)]
    for msg_num in range(20):
        msg_record = ('Some, text', int(time() * 100),
        'user' + str(random.choice(users)))
        c.execute('''INSERT INTO d{} VALUES (?, ?, ?)'''.format(file_id), msg_record)
        
db.commit()
db.close()
