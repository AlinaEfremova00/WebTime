from flask import Flask, request, render_template, session, redirect, url_for, jsonify
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = 'supersecretkey'


# Функция подключения к БД
def connect_db():
    return sqlite3.connect('main.db', check_same_thread=False)


# Авторизация (запоминаем пользователя в сессии)
@app.route('/authorization', methods=['GET', 'POST'])
def form_authorization():
    if request.method == 'POST':
        Login = request.form.get('Login')
        Password = request.form.get('Password')

        with sqlite3.connect('main.db') as db_lp:
            cursor_db = db_lp.cursor()
            cursor_db.execute("SELECT password FROM passwords WHERE login = ?", (Login,))
            result = cursor_db.fetchone()

        if result and bcrypt.checkpw(Password.encode('utf-8'), result[0]):
            session['user'] = Login  # Сохраняем логин в сессии
            return redirect(url_for('profile'))  # Перенаправляем в личный кабинет
        else:
            return render_template('auth_bad.html')

    return render_template('authorization.html')


# Регистрация (сразу авторизуем пользователя)
@app.route('/registration', methods=['GET', 'POST'])
def form_registration():
    if request.method == 'POST':
        Login = request.form.get('Login')
        Password = request.form.get('Password')

        hashed_password = bcrypt.hashpw(Password.encode('utf-8'), bcrypt.gensalt())

        try:
            with sqlite3.connect('main.db') as db_lp:
                cursor_db = db_lp.cursor()
                cursor_db.execute("INSERT INTO passwords VALUES (?, ?)", (Login, hashed_password))
                db_lp.commit()

            session['user'] = Login  # Авторизуем пользователя сразу после регистрации
            return redirect(url_for('profile'))

        except sqlite3.IntegrityError:
            return "Этот логин уже существует. Попробуйте другой."

    return render_template('registration.html')


# Личный кабинет
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('form_authorization'))

    user = session['user']
    db = connect_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT groups.group_id, groups.group_name 
        FROM groups 
        JOIN group_members ON groups.group_id = group_members.group_id 
        WHERE group_members.login = ?
    """, (user,))
    groups = cursor.fetchall()

    cursor.execute("""
        SELECT r.request_id, r.event_id, r.requester, r.request_type, 
               r.new_event_name, r.new_event_date, e.event_name, e.event_date
        FROM requests r
        JOIN events e ON r.event_id = e.event_id
        WHERE e.created_by = ?
    """, (user,))
    requests = cursor.fetchall()

    db.close()
    return render_template('profile.html', user=user, groups=groups, requests=requests)


# Выход из аккаунта
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('form_authorization'))


@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if request.method == 'POST':
        group_name = request.form.get('group_name')

        try:
            with sqlite3.connect('main.db') as db_lp:
                cursor_db = db_lp.cursor()
                cursor_db.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
            return "Группа успешно создана!"
        except sqlite3.IntegrityError:
            return "Группа с таким именем уже существует!"

    return render_template('create_group.html')


@app.route('/join_group', methods=['GET', 'POST'])
def join_group():
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        login = session['user']  # Текущий пользователь
        try:
            with sqlite3.connect('main.db') as db_lp:
                cursor_db = db_lp.cursor()
                # Сначала получаем id группы по её названию
                cursor_db.execute("SELECT group_id FROM groups WHERE group_name = ?", (group_name,))
                result = cursor_db.fetchone()
                if result is None:
                    return "Группа с таким названием не найдена."

                group_id = result[0]

                # Затем вставляем запись о присоединении пользователя к группе
                cursor_db.execute(
                    "INSERT INTO group_members (login, group_id) VALUES (?, ?)",
                    (login, group_id)
                )
                db_lp.commit()  # Явное подтверждение транзакции (хотя with-контекст может сделать это сам)
            return "Вы успешно присоединились к группе!"
        except sqlite3.IntegrityError:
            return "Вы уже состоите в этой группе или произошла ошибка с данными."
        except Exception as e:
            # Для отладки можно вывести ошибку, но в production лучше логировать её
            return f"Произошла непредвиденная ошибка: {e}"

    return render_template('join_group.html')


@app.route('/api/edit_event', methods=['POST'])
def edit_event():

    data = request.get_json()
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_date = data.get('event_date')

    print(f"Запрос на редактирование: {event_id} → {event_name} ({event_date})")

    try:
        print(f"Данные для обновления: event_id={event_id}, event_name={event_name}, event_date={event_date}")
        with sqlite3.connect('main.db') as db_lp:
            cursor_db = db_lp.cursor()
            cursor_db.execute(
                "UPDATE events SET event_name = ?, event_date = ? WHERE event_id = ?",
                (event_name, event_date, event_id)
            )
            db_lp.commit()
            print("Коммит выполнен!")
        print("Успешно изменено!")
        return jsonify({"success": True})
    except Exception as e:
        print(f" Ошибка: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/group_events/<int:group_id>')
def group_events(group_id):
    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()
        cursor_db.execute("SELECT event_name, event_date FROM events WHERE group_id = ?", (group_id,))
        events = cursor_db.fetchall()

    return render_template('group_events.html', events=events)


@app.route('/api/events/<int:group_id>')
def api_events(group_id):
    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()
        cursor_db.execute("SELECT event_id, event_name, event_date, created_by, event_type FROM events WHERE group_id = ?", (group_id,))
        events = cursor_db.fetchall()

    events_json = [
        {
            "id": event[0],
            "title": event[1],
            "start": event[2],
            "created_by": event[3] if event[3] else "Неизвестный",
            "event_type": event[4],
            "color": "#ff6666" if event[4] == "personal" else "#66b3ff"
        }
        for event in events
    ]
    return jsonify(events_json)


@app.route('/')
def index():
    return redirect('/index')


@app.route('/index')
def home():
    return render_template('index.html')


@app.route('/calendar/<int:group_id>')
def group_calendar(group_id):
    if 'user' not in session:
        return redirect(url_for('form_authorization'))

    user = session['user']

    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()
        cursor_db.execute("SELECT 1 FROM group_members WHERE login = ? AND group_id = ?", (user, group_id))
        is_member = cursor_db.fetchone()

    if not is_member:
        return "У вас нет доступа к этой группе!", 403

    return render_template('calendar.html', group_id=group_id)


@app.route('/add_event_ajax', methods=['POST'])
def add_event_ajax():
    if 'user' not in session:
        print("Запрос без авторизации! (только для теста)")
        session['user'] = 'test_user'

    event_name = request.form.get('event_name')
    event_date = request.form.get('event_date')
    group_id = request.form.get('group_id')
    created_by = session['user']
    event_type = request.form.get('event_type', 'group')

    try:
        with sqlite3.connect('main.db') as db_lp:
            cursor_db = db_lp.cursor()
            cursor_db.execute(
                "INSERT INTO events (group_id, event_name, event_date, created_by, event_type) VALUES (?, ?, ?, ?, ?)",
                (group_id, event_name, event_date, created_by, event_type)
            )
            db_lp.commit()
        print(f" Добавлено событие: {event_name} ({event_date})")
        return jsonify({"success": True})
    except Exception as e:
        print(f" Ошибка при добавлении: {e}")
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/delete_event', methods=['POST'])
def delete_event():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Вы не авторизованы!"})

    data = request.get_json()
    event_id = data.get('event_id')
    deleter = session['user']

    if not event_id:
        return jsonify({"success": False, "message": "Не указан ID события!"})

    try:
        with sqlite3.connect('main.db') as db_lp:
            cursor_db = db_lp.cursor()

            # Получаем данные о событии
            cursor_db.execute("SELECT group_id, created_by, event_name, event_date, event_type FROM events WHERE event_id = ?", (event_id,))
            event_data = cursor_db.fetchone()

            if not event_data:
                return jsonify({"success": False, "message": "Событие не найдено!"})

            group_id, created_by, event_name, event_date, event_type = event_data

            # Проверяем, можно ли удалить событие
            if deleter != created_by and event_type == "personal":
                return jsonify({"success": False, "message": "Вы не можете удалить чужое личное событие!"})

            if deleter != created_by:
                cursor_db.execute("SELECT 1 FROM group_members WHERE login = ? AND group_id = ?", (deleter, group_id))
                is_member = cursor_db.fetchone()
                if not is_member:
                    return jsonify({"success": False, "message": "Вы не можете удалить это событие!"})

            # Удаляем событие
            cursor_db.execute("DELETE FROM events WHERE event_id = ?", (event_id,))

            # Добавляем уведомления о удалении события
            if event_type == "group":
                cursor_db.execute("SELECT login FROM group_members WHERE group_id = ? AND login != ?", (group_id, deleter))
                users = cursor_db.fetchall()
                for user in users:
                    cursor_db.execute(
                        "INSERT INTO notifications (user, message) VALUES (?, ?)",
                        (user[0], f"{deleter} удалил событие: {event_name} ({event_date})")
                    )

            db_lp.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/event/<int:event_id>')
def event_details(event_id):
    if 'user' not in session:
        return redirect(url_for('form_authorization'))

    user = session['user']

    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()

        # Получаем информацию о событии
        cursor_db.execute("SELECT event_id, event_name, event_date, created_by FROM events WHERE event_id = ?", (event_id,))
        event = cursor_db.fetchone()

        if not event:
            return "Событие не найдено!", 404

        event_data = {
            "id": event[0],
            "title": event[1],
            "date": event[2],
            "creator": event[3]
        }

    return render_template('event.html', event=event_data, user=user)


@app.route('/notifications')
def notifications():
    if 'user' not in session:
        return redirect(url_for('form_authorization'))

    user = session['user']

    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()
        cursor_db.execute("SELECT id, message FROM notifications WHERE user = ? AND is_read = 0", (user,))
        notifications = cursor_db.fetchall()

    return render_template('notifications.html', notifications=notifications)


@app.route('/mark_read/<int:notification_id>')
def mark_read(notification_id):
    if 'user' not in session:
        return redirect(url_for('form_authorization'))

    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()
        cursor_db.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notification_id,))
        db_lp.commit()

    return redirect(url_for('notifications'))


# API: Запрос на редактирование
@app.route('/api/request_edit_event', methods=['POST'])
def request_edit_event():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Вы не авторизованы!"})

    data = request.get_json()
    user = session['user']
    event_id = data.get('event_id')
    new_event_name = data.get('event_name')
    new_event_date = data.get('event_date')

    if not event_id or not new_event_name:
        return jsonify({"success": False, "message": "Название события обязательно!"})

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT created_by FROM events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()
    if not event:
        return jsonify({"success": False, "message": "Событие не найдено!"})

    creator = event[0]

    cursor.execute("""
        INSERT INTO requests (event_id, requester, request_type, new_event_name, new_event_date)
        VALUES (?, ?, 'edit', ?, ?)
    """, (event_id, user, new_event_name, new_event_date))

    cursor.execute("""
        INSERT INTO notifications (user, message)
        VALUES (?, ?)
    """, (creator, f"✏ {user} хочет изменить '{new_event_name}' (Дата: {new_event_date or 'без изменений'})"))

    db.commit()
    db.close()
    return jsonify({"success": True})


# API: Запрос на удаление
@app.route('/api/request_delete_event', methods=['POST'])
def request_delete_event():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Вы не авторизованы!"})

    user = session['user']
    data = request.get_json()
    event_id = data.get('event_id')

    db = connect_db()
    cursor = db.cursor()

    cursor.execute("SELECT event_name, created_by FROM events WHERE event_id = ?", (event_id,))
    event = cursor.fetchone()
    if not event:
        return jsonify({"success": False, "message": "Событие не найдено!"})

    event_name, creator = event

    cursor.execute("""
        INSERT INTO requests (event_id, requester, request_type, request_status)
        VALUES (?, ?, 'delete', 'pending')
    """, (event_id, user))

    cursor.execute("""
        INSERT INTO notifications (user, message)
        VALUES (?, ?)
    """, (creator, f" {user} хочет удалить '{event_name}'"))

    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Запрос на удаление отправлен!"})


#  Получение списка запросов
@app.route('/api/get_requests')
def get_requests():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Вы не авторизованы!"})

    user = session['user']

    with sqlite3.connect('main.db') as db_lp:
        cursor_db = db_lp.cursor()
        cursor_db.execute("""
            SELECT request_id, event_id, requester, request_type, new_event_name, new_event_date, request_status
            FROM requests
            WHERE event_id IN (SELECT event_id FROM events WHERE created_by = ?)
        """, (user,))
        requests = cursor_db.fetchall()

    requests_json = [
        {
            "request_id": r[0],
            "event_id": r[1],
            "requester": r[2],
            "request_type": r[3],
            "new_event_name": r[4],
            "new_event_date": r[5],
            "status": r[6]
        }
        for r in requests
    ]
    return jsonify(requests_json)


#  Подтверждение запроса
@app.route('/api/approve_request', methods=['POST'])
def approve_request():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Вы не авторизованы!"})

    data = request.get_json()
    request_id = data.get('request_id')

    if not request_id:
        return jsonify({"success": False, "message": "Не указан request_id!"})

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT event_id, request_type, new_event_name, new_event_date FROM requests WHERE request_id = ?",
                   (request_id,))
    request_data = cursor.fetchone()

    if not request_data:
        db.close()
        return jsonify({"success": False, "message": "Запрос не найден!"})

    event_id, request_type, new_event_name, new_event_date = request_data

    if request_type == "edit":
        cursor.execute("UPDATE events SET event_name = ?, event_date = ? WHERE event_id = ?",
                       (new_event_name, new_event_date, event_id))
    elif request_type == "delete":
        cursor.execute("DELETE FROM events WHERE event_id = ?", (event_id,))

    cursor.execute("DELETE FROM requests WHERE request_id = ?", (request_id,))
    db.commit()
    db.close()

    return jsonify({"success": True})


#  Отклонение запроса
@app.route('/api/reject_request', methods=['POST'])
def reject_request():
    if 'user' not in session:
        return jsonify({"success": False, "message": "Вы не авторизованы!"})

    data = request.get_json()
    request_id = data.get('request_id')

    if not request_id:
        return jsonify({"success": False, "message": "Не указан request_id!"})

    db = connect_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM requests WHERE request_id = ?", (request_id,))
    db.commit()
    db.close()

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)