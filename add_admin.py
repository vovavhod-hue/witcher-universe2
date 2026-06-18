import sqlite3

conn = sqlite3.connect('database.db', timeout=10)
c = conn.cursor()
c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
          ('admin', 'admin', 'admin@witcher.com'))
conn.commit()
conn.close()
print("Администратор добавлен!")