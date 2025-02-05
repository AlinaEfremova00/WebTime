import sqlite3

db_lp = sqlite3.connect('main.db')
cursor_db = db_lp.cursor()
sql_create = '''CREATE TABLE passwords(
login TEXT PRIMARY KEY,
password TEXT NOT NULL);'''

# Создание таблицы для групп
cursor_db.execute('''
CREATE TABLE events(
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    event_date DATE NOT NULL, created_by TEXT NOT NULL DEFAULT 'Unknown', event_type TEXT NOT NULL DEFAULT 'group',
    FOREIGN KEY (group_id) REFERENCES groups(group_id)
);
''')
cursor_db.execute('''
CREATE TABLE group_members(
    login TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY (login) REFERENCES passwords(login),
    FOREIGN KEY (group_id) REFERENCES groups(group_id),
    PRIMARY KEY (login, group_id)
);
''')
cursor_db.execute('''
CREATE TABLE groups(
    group_id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL UNIQUE
);
''')
cursor_db.execute('''
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    message TEXT NOT NULL,
    event_id INTEGER,
    is_read INTEGER DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);
''')
cursor_db.execute('''
CREATE TABLE requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    requester TEXT NOT NULL,
    request_type TEXT NOT NULL,  -- 'edit' или 'delete'
    request_status TEXT DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    new_event_name TEXT,  -- Если это запрос на редактирование
    new_event_date DATE,  -- Если это запрос на редактирование
    FOREIGN KEY (event_id) REFERENCES events(event_id),
    FOREIGN KEY (requester) REFERENCES passwords(login)
);
''')
cursor_db.execute('''
CREATE TABLE sqlite_sequence(name,seq)
''')

cursor_db.execute(sql_create)
db_lp.commit()
cursor_db.close()
db_lp.close()