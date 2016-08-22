import sqlite3

db = sqlite3.connect('server/data/sessions.db')
c = db.cursor()

c.execute('''SELECT * FROM sessions''')
db.commit()
print(c.fetchall())
