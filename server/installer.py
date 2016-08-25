import sqlite3

class Installer:
    @staticmethod
    def install():
        open('data/messages.db', 'w').close()

        db = sqlite3.connect('data/users.db')
        c = db.cursor()

        c.execute('''PRAGMA foreign_keys = 1''')

        c.execute('''CREATE TABLE users (name text PRIMARY KEY,
                                         password text,

                                         friends text,
                                         favorites text,
                                         blacklist text,
                                         dialogs text)''')

        c.execute('''CREATE TABLE profiles (name text PRIMARY KEY
                                            REFERENCES users(name),

                                            status text,
                                            email text,
                                            birthday int,
                                            about text,
                                            image blob)''')

        db.commit()
        db.close()

        db = sqlite3.connect('data/sessions.db')
        c = db.cursor()
        c.execute('''CREATE TABLE sessions (name text,
                                            session_id text UNIQUE,
                                            ip text)''')

        db.commit()
        db.close()

        db = sqlite3.connect('data/requests.db')
        c = db.cursor()
        c.execute('''CREATE TABLE requests (from_who text,
                                            to_who text,
                                            message text)''')

        db.commit()
        db.close()
