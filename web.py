from flask import Flask, render_template, request, redirect
from db import get_conn

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_SECRET"

@app.route("/")
def index():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM prayers")
    prayers = c.fetchall()
    conn.close()
    return render_template("prayers.html", prayers=prayers)

@app.route("/mark_prayed/<int:prayer_id>")
def mark_prayed(prayer_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE prayers SET prayed=1 WHERE id=?", (prayer_id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(port=5000)
