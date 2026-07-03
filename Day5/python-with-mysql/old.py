from flask import Flask, jsonify
import pymysql
import os

app = Flask(__name__)

DB_HOST = os.environ.get("MYSQL_HOST", "mysql")
DB_USER = os.environ.get("MYSQL_USER", "flaskuser")
DB_PASSWORD = os.environ.get("MYSQL_PASSWORD", "flaskpass")
DB_NAME = os.environ.get("MYSQL_DATABASE", "flaskdb")

def getConnection():
    return pymysql.connect(
       host=DB_HOST,
       user=DB_USER,
       password=DB_PASSWORD,
       database=DB_NAME,
       cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def index():
    conn = getConnection()
    with conn.cursor() as cursor:
        cursor.execute("CREATE TABLE IF NOT EXISTS visits (count INT)")
        cursor.execute("SELECT count FROM visits")
        result = cursor.fetchone()
        if result is None:
            cursor.execute("INSERT INTO visits (count) VALUES (1)")
            visits = 1
        else:
            visits = result['count'] + 1
            cursor.execute("UPDATE visits SET count=%s",(visits,))
        conn.commit()
    conn.close()
    return jsonify({"message": f"Hello! This page has been visited {visits} times."})

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=8080)
