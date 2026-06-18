from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
import sqlite3
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

app = Flask(__name__)
app.secret_key = 'секретный_ключ_для_сообщений'

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "the.w1tcher.hub.67@gmail.com"
SENDER_PASSWORD = "anku teso fthx beev"
RECIPIENT_EMAIL = "the.w1tcher.hub.67@gmail.com"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return url_for('static', filename=f'uploads/{filename}')
    return 'https://via.placeholder.com/200x300'

def get_db():
    conn = sqlite3.connect('database.db', timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, type TEXT, year TEXT, image TEXT, desc TEXT,
                  content TEXT, author TEXT, publisher TEXT, 
                  original_title TEXT, translator TEXT, genre TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS games
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, year TEXT, platform TEXT, image TEXT, desc TEXT,
                  publisher TEXT, rating TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS encyclopedia
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT, type TEXT, image TEXT, desc TEXT, tags TEXT)''') 
    c.execute('''CREATE TABLE IF NOT EXISTS journal
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  time TEXT, user TEXT, action TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS moderation
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  author TEXT, topic TEXT, message TEXT, status TEXT DEFAULT 'pending',
                  created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS replies
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                author TEXT,
                message TEXT,
                created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE, password TEXT, email TEXT)''')
    conn.commit()
    conn.close()
    print("База данных инициализирована")

def add_log(action):
    time_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO journal (time, user, action) VALUES (?, ?, ?)", 
                  (time_str, 'Администратор', action))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при записи в журнал: {e}")
    finally:
        conn.close()

init_db()

def check_data():
    conn = get_db()
    c = conn.cursor()
    books = c.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    games = c.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    ency = c.execute("SELECT COUNT(*) FROM encyclopedia").fetchone()[0]
    print(f"📊 Данные в БД: Книги: {books}, Игры: {games}, Энциклопедия: {ency}")
    conn.close()

check_data()

def debug_db():
    conn = get_db()
    c = conn.cursor()
    books = c.execute("SELECT id, title FROM books").fetchall()
    games = c.execute("SELECT id, title FROM games").fetchall()
    ency = c.execute("SELECT id, title FROM encyclopedia").fetchall()
    print("=" * 50)
    print("📚 КНИГИ В БАЗЕ:")
    for book in books:
        print(f"  ID: {book[0]}, Название: '{book[1]}'")
    print("\n🎮 ИГРЫ В БАЗЕ:")
    for game in games:
        print(f"  ID: {game[0]}, Название: '{game[1]}'")
    print("\n📖 СТАТЬИ В БАЗЕ:")
    for entry in ency:
        print(f"  ID: {entry[0]}, Название: '{entry[1]}'")
    print("=" * 50)
    conn.close()

debug_db()

def validate_year(year):
    if not year:
        return True
    return year.isdigit() and 1900 <= int(year) <= 2030

def validate_required_fields(title, item_type):
    if not title:
        return False, "Название не может быть пустым"
    if not item_type:
        return False, "Тип элемента не выбран"
    return True, None

@app.route('/')
def index():
    conn = get_db()
    c = conn.cursor()
    books = c.execute("SELECT * FROM books LIMIT 3").fetchall()
    games = c.execute("SELECT * FROM games LIMIT 3").fetchall()
    ency = c.execute("SELECT * FROM encyclopedia LIMIT 3").fetchall()
    conn.close()
    return render_template('index.html', books=books, games=games, ency=ency)

@app.route('/books')
def books_page():
    conn = get_db()
    c = conn.cursor()
    books = c.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template('books.html', books=books)

@app.route('/book/<int:id>')
def book_detail(id):
    conn = get_db()
    c = conn.cursor()
    book = c.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
    conn.close()
    if not book:
        return "Книга не найдена", 404
    return render_template('book_detail.html', book=book)

@app.route('/games')
def games_page():
    conn = get_db()
    c = conn.cursor()
    games = c.execute("SELECT * FROM games").fetchall()
    conn.close()
    return render_template('games.html', games=games)

@app.route('/game/<int:id>')
def game_detail(id):
    conn = get_db()
    c = conn.cursor()
    game = c.execute("SELECT * FROM games WHERE id=?", (id,)).fetchone()
    conn.close()
    if not game:
        return "Игра не найдена", 404
    return render_template('game_detail.html', game=game)

@app.route('/encyclopedia')
def encyclopedia_page():
    filter_type = request.args.get('type', 'all')
    conn = get_db()
    c = conn.cursor()
    if filter_type != 'all':
        ency = c.execute("SELECT * FROM encyclopedia WHERE type = ?", (filter_type,)).fetchall()
    else:
        ency = c.execute("SELECT * FROM encyclopedia").fetchall()
    conn.close()
    return render_template('encyclopedia.html', ency=ency, filter_type=filter_type)

@app.route('/forum')
def forum():
    conn = get_db()
    c = conn.cursor()
    topics = c.execute("""
        SELECT id, author, topic, message, datetime(created_at) as created_at 
        FROM moderation 
        WHERE status='approved' 
        ORDER BY id DESC
    """).fetchall()
    
    topics_with_counts = []
    for topic in topics:
        topics_with_counts.append({
            'id': topic[0],
            'author': topic[1],
            'topic': topic[2],
            'message': topic[3],
            'created_at': topic[4],
            'replies_count': 0
        })
    conn.close()
    return render_template('forum.html', topics=topics_with_counts)

@app.route('/topic/new', methods=['GET', 'POST'])
def new_topic():
    if request.method == 'POST':
        author = request.form.get('author', 'Аноним').strip()
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        
        if not title or not message:
            flash('Заголовок и сообщение не могут быть пустыми!')
            return redirect(url_for('new_topic'))
        
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO moderation (author, topic, message, status, created_at) 
                VALUES (?, ?, ?, 'pending', datetime('now'))
            """, (author, title, message))
            conn.commit()
            flash('Ваша тема отправлена на модерацию!')
        except Exception as e:
            flash(f'Ошибка: {str(e)}')
        finally:
            conn.close()
        return redirect(url_for('forum'))
    
    return render_template('new_topic.html')

@app.route('/topic/<int:id>')
def topic_detail(id):
    conn = get_db()
    c = conn.cursor()
    topic = c.execute("""
        SELECT id, author, topic, message, datetime(created_at) as created_at 
        FROM moderation 
        WHERE id=? AND status='approved'
    """, (id,)).fetchone()
    
    if not topic:
        return "Тема не найдена", 404

    messages = [{
        'author': topic[1],
        'author_initial': topic[1][0].upper(),
        'message': topic[3],
        'created_at': topic[4]
    }]
    
    replies =c.execute("""
        SELECT author, message, datetime(created_at) as create_at
        FROM replies
        WHERE topic_id=?
        ORDER BY created_at ASC
        """, (id,)).fetchall()

    for reply in replies:
        messages.append({
            'author': reply[0],
            'author_initial': reply[0][0].upper(),
            'message': reply[1],
            'created_at': reply[2],
        })
    
    conn.close()
    return render_template('topic_detail.html', topic=topic, messages=messages)

@app.route('/topic/<int:id>/reply', methods=['POST'])
def add_reply(id):
    if 'username' not in session:
        flash('Чтобы ответить, необходимо войти в систему или зарегистрироваться!')
        return redirect(url_for('login'))
    
    reply_message = request.form.get('reply', '').strip()
    if not reply_message:
        flash('Сообщение не может быть пустым!')
        return redirect(url_for('topic_detail', id=id))
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
        INSERT INTO replies (topic_id, author, message, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """, (id, session['username'], reply_message))
        conn.commit()
        flash('Ваш ответ опубликован')
    except Exception as e:
        flash(f'Ошибка при сохранении ответа: {str(e)}')
    finally:
        conn.close()
    
    return redirect(url_for('topic_detail', id=id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                      (username, password, email))
            conn.commit()
            user_id = c.lastrowid
            session['user_id'] = user_id
            session['username'] = username
            flash('Регистрация успешна! Добро пожаловать в мир Ведьмака!')
            return redirect(url_for('profile'))
        except sqlite3.IntegrityError:
            flash('Имя пользователя уже занято!')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session.pop('_flashes', None)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        c = conn.cursor()
        user = c.execute("SELECT * FROM users WHERE username=? AND password=?", 
                         (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            if username == 'admin' and password == 'admin':
                return redirect(url_for('admin_panel'))
            else:
                flash('Вход выполнен!')
                return redirect(url_for('profile'))
        else:
            flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('Сначала войдите в систему, чтобы увидеть личный кабинет.')
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    user = c.execute("SELECT username, email FROM users WHERE username=?", (session['username'],)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы.')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_panel():
    if 'username' not in session or session['username'] != 'admin':
        session['alert_message'] = '🚫 Доступ запрещен! Эта страница только для администратора.'
        return redirect(url_for('index'))
    
    conn = get_db()
    c = conn.cursor()
    books = c.execute("SELECT * FROM books").fetchall()
    games = c.execute("SELECT * FROM games").fetchall()
    ency = c.execute("SELECT * FROM encyclopedia").fetchall()
    journal = c.execute("SELECT * FROM journal ORDER BY id DESC LIMIT 20").fetchall()
    mod = c.execute("SELECT * FROM moderation WHERE status='pending'").fetchall()
    users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    stats = {
        'books': len(books),
        'games': len(games),
        'ency': len(ency),
        'users': users
    }
    conn.close()
    return render_template('admin.html', books=books, games=games, ency=ency, 
                           journal=journal, mod=mod, stats=stats)

@app.route('/add_item', methods=['POST'])
def add_item():
    try:
        item_type = request.form.get('type')
        title = request.form.get('title', '').strip()
        desc = request.form.get('desc', '').strip()
        
        valid, error = validate_required_fields(title, item_type)
        if not valid:
            flash(error)
            return redirect(url_for('admin_panel'))
        
        image_url = 'https://via.placeholder.com/200x300'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_url = save_image(file)
        
        conn = get_db()
        c = conn.cursor()
        
        if item_type == 'book':
            book_type = request.form.get('subtype', 'Роман')
            year = request.form.get('year', '').strip()
            author = request.form.get('author', '')
            publisher = request.form.get('publisher', '')
            original_title = request.form.get('original_title', '')
            translator = request.form.get('translator', '')
            genre = request.form.get('genre', '')
            
            html_content = ''
            if 'html_file' in request.files:
                html_file = request.files['html_file']
                if html_file and html_file.filename:
                    html_content = html_file.read().decode('utf-8')
                    print(f"📄 Файл загружен: {html_file.filename}, размер: {len(html_content)} символов")
            
            if year and not validate_year(year):
                flash('Год должен содержать только цифры (например, 1993)')
                conn.close()
                return redirect(url_for('admin_panel'))
            
            if not year:
                year = 'Не указан'
            
            c.execute("""INSERT INTO books 
                         (title, type, year, image, desc, content, author, publisher, original_title, translator, genre) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                      (title, book_type, year, image_url, desc, html_content, author, publisher, original_title, translator, genre))
            
        elif item_type == 'game':
            year = request.form.get('year', '').strip()
            if not year:
                year = 'Не указан'
            platform = request.form.get('platform', 'PC').strip()
            if not platform:
                platform = 'PC'
            
            publisher = request.form.get('publisher', '').strip()
            rating = request.form.get('rating', '').strip()
            
            html_content = ''
            if 'html_file' in request.files:
                html_file = request.files['html_file']
                if html_file and html_file.filename:
                    html_content = html_file.read().decode('utf-8')
            
            c.execute("INSERT INTO games (title, year, platform, image, desc, publisher, rating, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                      (title, year, platform, image_url, desc, publisher, rating, html_content))
            
        elif item_type == 'ency':
            ency_type = request.form.get('subtype', 'Персонажи')
            tags = request.form.get('tags', '').strip()
            
            c.execute("INSERT INTO encyclopedia (title, type, image, desc, tags) VALUES (?, ?, ?, ?, ?)", 
                    (title, ency_type, image_url, desc, tags))
        else:
            flash('Неизвестный тип элемента!')
            conn.close()
            return redirect(url_for('admin_panel'))
        
        conn.commit()
        add_log(f"Добавлен: {title}")
        conn.close()
        
        flash(f'✅ "{title}" успешно добавлен!')
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        flash(f'Ошибка при добавлении: {str(e)}')
        return redirect(url_for('admin_panel'))
    
    return redirect(url_for('admin_panel'))

@app.route('/delete_item/<type>/<int:id>')
def delete_item(type, id):
    conn = get_db()
    c = conn.cursor()
    try:
        if type == 'book':
            c.execute("DELETE FROM books WHERE id=?", (id,))
            add_log(f"Удалена книга (ID: {id})")
        elif type == 'game':
            c.execute("DELETE FROM games WHERE id=?", (id,))
            add_log(f"Удалена игра (ID: {id})")
        elif type == 'ency':
            c.execute("DELETE FROM encyclopedia WHERE id=?", (id,))
            add_log(f"Удалена статья энциклопедии (ID: {id})")
        conn.commit()
        flash('Элемент удален!')
    except Exception as e:
        flash(f'Ошибка при удалении: {str(e)}')
    finally:
        conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/approve_mod/<int:id>')
def approve_mod(id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("UPDATE moderation SET status='approved' WHERE id=?", (id,))
        conn.commit()
        add_log(f"Одобрена тема модерации (ID: {id})")
        flash('Тема одобрена!')
    except Exception as e:
        flash(f'Ошибка: {str(e)}')
    finally:
        conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/delete_mod/<int:id>')
def delete_mod(id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("DELETE FROM moderation WHERE id=?", (id,))
        conn.commit()
        add_log(f"Удалена тема модерации (ID: {id})")
        flash('Тема удалена!')
    except Exception as e:
        flash(f'Ошибка: {str(e)}')
    finally:
        conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/news')
def news():
    return render_template('news.html')

@app.route('/movies')
def movies():
    return render_template('movies.html')

@app.route('/movie/<int:id>')
def movie_detail_witcher1(id):
    movies_data = {
        1: {'title': 'Ведьмак (2001)', 'poster': '/static/images/300x450.jpg', 'year': '2001', 'country': 'Польша', 'rating': '6.6', 'duration': '130 мин', 'description': 'Фильм рассказывает о приключениях ведьмака Геральта из Ривии...', 'actors': ['Михал Жебровский', 'Збигнев Замаховский', 'Анна Дымна'], 'trailer': 'images/witcher_video.mp4'},
        2: {'title': 'Ведьмак (2002)', 'poster': '/static/images/witcher2.jpg', 'year': '2002', 'country': 'Польша', 'rating': '7.4', 'duration': '130 мин', 'description': 'Продолжение приключений Геральта...', 'actors': ['Михал Жебровский', 'Збигнев Замаховский', 'Анна Дымна'], 'trailer': 'images/witcher2_video.mp4'},
        3: {'title': 'Дорога без возврата', 'poster': '/static/images/Road_without_return._ESSE._Film-musical_poster.jpg', 'year': '2009', 'country': 'Россия', 'rating': '7.1', 'duration': '120 мин', 'description': 'Российский фильм по мотивам произведений Сапковского...', 'actors': ['Алексей Серебряков', 'Дарья Мороз', 'Александр Балуев'], 'trailer': 'witcher3_video.mkv'},
        4: {'title': 'Ведьмак (2019)', 'poster': 'https://upload.wikimedia.org/wikipedia/ru/thumb/5/5a/The_Witcher_Netflix.jpg/220px-The_Witcher_Netflix.jpg', 'year': '2019', 'country': 'США, Польша', 'rating': '7.1', 'duration': '60 мин (серия)', 'description': 'Сериал от Netflix по мотивам книг Сапковского...', 'actors': ['Генри Кавилл', 'Аня Чалотра', 'Фрейя Аллан'], 'trailer': 'https://www.youtube.com/embed/VIDEO_ID_4'},
        5: {'title': 'Полвека поэзии спустя', 'poster': 'https://upload.wikimedia.org/wikipedia/ru/thumb/0/0a/Polveka_poezii_spustya.jpg/220px-Polveka_poezii_spustya.jpg', 'year': '2023', 'country': 'Польша', 'rating': '6.5', 'duration': '95 мин', 'description': 'Документальный фильм о влиянии творчества Сапковского...', 'actors': ['Анджей Сапковский', 'Адам Мицкевич'], 'trailer': 'https://www.youtube.com/embed/VIDEO_ID_5'}
    }
    movie = movies_data.get(id)
    if not movie:
        return "Фильм не найден", 404
    return render_template('movie_detail.html', movie=movie)

@app.route('/anime')
def anime():
    return render_template('anime.html')

@app.route('/anime/<int:id>')
def anime_detail(id):
    if id == 1:
        anime = {
            'id': id, 'title': 'Ведьмак: Кошмар волка', 'poster': 'https://upload.wikimedia.org/wikipedia/ru/thumb/c/cb/The_Witcher_Nightmare_of_the_Wolf_poster.jpg/220px-The_Witcher_Nightmare_of_the_Wolf_poster.jpg',
            'year': '2021', 'country': 'США', 'rating': '6.9', 'duration': '83 мин', 'description': 'Анимационный фильм о мире «Ведьмака» от Netflix...', 'actors': ['Мэри Макдоннелл', 'Давид Эрриго мл.', 'Тео Джеймс'], 'trailer': 'https://www.youtube.com/embed/VIDEO_ID'
        }
    elif id == 2:
        anime = {
            'id': id, 'title': 'Ведьмак: Сирены глубин', 'poster': 'https://upload.wikimedia.org/wikipedia/ru/thumb/2/28/The_Witcher_Sirens_of_the_Deep_poster.jpg/220px-The_Witcher_Sirens_of_the_Deep_poster.jpg',
            'year': '2025', 'country': 'Польша, Корея Южная, США', 'rating': '6.2', 'duration': '91 мин', 'description': 'Анимационный фильм о мире «Ведьмака» от Netflix...', 'actors': ['Даг Кокл', 'Джоэль Эдгертон', 'Аня Чало́тра'], 'trailer': 'https://www.youtube.com/embed/VIDEO_ID'
        }
    else:
        return "Страница не найдена", 404
    return render_template('anime_detail.html', anime=anime)

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        if not name or not email or not subject or not message:
            flash('Все поля обязательны для заполнения!')
            return redirect(url_for('feedback'))
        
        msg = EmailMessage()
        msg['From'] = f'Вселенная Ведьмака <{SENDER_EMAIL}>'
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f'Обратная связь: {subject}'
        msg.set_content(f'Имя: {name}\nEmail: {email}\nТема: {subject}\n\nСообщение:\n{message}')
        
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)
            flash('Ваше сообщение отправлено! Мы ответим в ближайшее время.')
        except Exception as e:
            flash(f'Ошибка при отправке: {str(e)}')
        return redirect(url_for('feedback'))
    return render_template('feedback.html')

@app.route('/help')
def help():
    return render_template('help.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip().lower()
    conn = get_db()
    c = conn.cursor()
    
    if not query:
        conn.close()
        return render_template('search.html')
    
    all_items = []
    
    books = c.execute("SELECT id, title, desc FROM books").fetchall()
    for book in books:
        all_items.append({
            'title': book[1],
            'description': book[2][:100] + '...' if book[2] else 'Описание отсутствует',
            'url': url_for('book_detail', id=book[0]),
            'type': 'Книга',
            'icon': '📖'
        })
    
    games = c.execute("SELECT id, title, desc FROM games").fetchall()
    for game in games:
        all_items.append({
            'title': game[1],
            'description': game[2][:100] + '...' if game[2] else 'Описание отсутствует',
            'url': url_for('game_detail', id=game[0]),
            'type': 'Игра',
            'icon': '🎮'
        })
    
    ency = c.execute("SELECT id, title, desc, tags FROM encyclopedia").fetchall()
    for entry in ency:
        all_items.append({
            'title': entry[1],
            'description': entry[2][:100] + '...' if entry[2] else 'Описание отсутствует',
            'url': url_for('encyclopedia_page'),
            'type': 'Статья',
            'icon': '📚'
        })
    
    conn.close()
    
    all_items.append({
        'title': 'Геральт из Ривии',
        'description': 'Главный герой саги. Профессиональный ведьмак-мутант.',
        'url': url_for('encyclopedia_page'),
        'type': 'Персонаж',
        'icon': '⚔️'
    })
    all_items.append({
        'title': 'Цирилла (Цири)',
        'description': 'Дитя Предназначения, наследница Старшей Крови.',
        'url': url_for('encyclopedia_page'),
        'type': 'Персонаж',
        'icon': '⚔️'
    })
    
    results = []
    for item in all_items:
        title_lower = item['title'].lower()
        desc_lower = item['description'].lower()
        if query in title_lower or query in desc_lower:
            results.append(item)
    
    return render_template('search.html', results=results, query=request.args.get('q', ''))

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)