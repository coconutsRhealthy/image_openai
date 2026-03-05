import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="appuser",
    password="app_password",
    database="mydb"
)

cursor = conn.cursor()

entries = [
    ("Alice", "alice@example.com"),
    ("Bob", "bob@example.com")
]

cursor.executemany(
    "INSERT INTO users (name, email) VALUES (%s, %s)",
    entries
)

conn.commit()

cursor.execute("SELECT id, name, email FROM users;")
rows = cursor.fetchall()

print("\nHuidige entries in de database:")
for row in rows:
    print(row)

cursor.close()
conn.close()