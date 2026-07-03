from flask import Flask, jsonify
import pymysql
import os

app = Flask(__name__)

DB_HOST = os.environ.get("MYSQL_HOST", "mysql")
DB_USER = os.environ.get("MYSQL_USER", "root")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD", "root@123")
DB_NAME = os.environ.get("MYSQL_DATABASE", "flaskdb")

def getConnection():
    return pymysql.connect(
       host=DB_HOST,
       user=DB_USER,
       password=DB_PASSWORD,
       database=DB_NAME,
       cursorclass=pymysql.cursors.DictCursor,
       autocommit=True
    )

# Ensure table exists
def init_db():
    conn = getConnection()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS page_visits (
                id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
                visits INT NOT NULL
            )
        """)
        # Insert initial row if table empty
        cursor.execute("SELECT COUNT(*) AS count FROM page_visits")
        result = cursor.fetchone()
        if result['count'] == 0:
            cursor.execute("INSERT INTO page_visits (visits) VALUES (0)")

@app.route("/")
def index():
    conn = getConnection()
    with conn.cursor() as cursor:
        # Increment visits
        cursor.execute("UPDATE page_visits SET visits = visits + 1 WHERE id = 1")
        # Fetch current visit count
        cursor.execute("SELECT visits FROM page_visits WHERE id = 1")
        result = cursor.fetchone()
        visits = result['visits']
    return jsonify({"message": "Hello from Flask!", "visits": visits})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
