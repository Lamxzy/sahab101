import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "siwes_portal_key"

def db():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

# HOME
@app.route("/")
def home():
    if "user" in session:
        return render_template("dashboard.html", user=session["user"])
    return render_template("home.html")

# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
                    (name,email,password))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")

# LOGIN
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user"] = user[1]
            session["id"] = user[0]
            return redirect(url_for("home"))

    return render_template("login.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# STUDENTS
@app.route("/students")
def students():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY id")
    data = cur.fetchall()
    conn.close()
    return render_template("students.html", students=data)

@app.route("/add_student", methods=["POST"])
def add_student():
    conn = db()
    cur = conn.cursor()
    cur.execute("INSERT INTO students(name,department,level) VALUES(%s,%s,%s)",
                (request.form["name"], request.form["department"], request.form["level"]))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))

# RESULTS
@app.route("/results")
def results():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name, c.course, c.score
        FROM students s
        JOIN courses c ON s.id = c.student_id
    """)
    data = cur.fetchall()
    conn.close()
    return render_template("results.html", data=data)

# PERFORMANCE
@app.route("/performance")
def performance():
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name,
               SUM(c.score),
               AVG(c.score)
        FROM students s
        JOIN courses c ON s.id = c.student_id
        GROUP BY s.id
        ORDER BY SUM(c.score) DESC
    """)
    data = cur.fetchall()
    conn.close()
    return render_template("performance.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)