import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ================= DATABASE ================= #
def connect():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

# ================= HOME ================= #
@app.route("/")
def home():
    return render_template("index.html")


# ================= STUDENTS ================= #
@app.route("/students")
def students():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY student_id")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("students.html", students=data)


@app.route("/add_student", methods=["POST"])
def add_student():
    name = request.form["name"]
    department = request.form["department"]
    level = request.form["level"]

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO students (name, department, level) VALUES (%s, %s, %s)",
        (name, department, level)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("students"))


@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    conn = connect()
    cur = conn.cursor()

    # FIX: remove child records first
    cur.execute("DELETE FROM courses WHERE student_id = %s", (student_id,))
    cur.execute("DELETE FROM students WHERE student_id = %s", (student_id,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("students"))


@app.route("/update_student/<int:student_id>", methods=["GET", "POST"])
def update_student(student_id):
    conn = connect()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        department = request.form["department"]
        level = request.form["level"]

        cur.execute("""
            UPDATE students
            SET name=%s, department=%s, level=%s
            WHERE student_id=%s
        """, (name, department, level, student_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("students"))

    cur.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    student = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("update_student.html", student=student)


# ================= COURSES ================= #
@app.route("/add_course", methods=["POST"])
def add_course():
    student_id = request.form["student_id"]
    course_name = request.form["course_name"]
    score = request.form["score"]

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO courses (student_id, course_name, score) VALUES (%s, %s, %s)",
        (student_id, course_name, score)
    )

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("results"))


@app.route("/results")
def results():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.name, c.course_name, c.score
        FROM students s
        JOIN courses c ON s.student_id = c.student_id
        ORDER BY s.name
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("results.html", results=data)


# ================= PERFORMANCE ================= #
@app.route("/performance")
def performance():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.name,
            SUM(c.score) AS total,
            AVG(c.score) AS avg,
            RANK() OVER (ORDER BY SUM(c.score) DESC) AS rank
        FROM students s
        JOIN courses c ON s.student_id = c.student_id
        GROUP BY s.student_id
        ORDER BY rank
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("performance.html", rows=data)


# ================= TOP STUDENTS ================= #
@app.route("/top")
def top():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.name, SUM(c.score) AS total
        FROM students s
        JOIN courses c ON s.student_id = c.student_id
        GROUP BY s.student_id
        ORDER BY total DESC
        LIMIT 3
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("top_students.html", rows=data)


# ================= GRADES ================= #
@app.route("/grades")
def grades():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        WITH avg_table AS (
            SELECT s.name, AVG(c.score) AS avg_score
            FROM students s
            JOIN courses c ON s.student_id = c.student_id
            GROUP BY s.student_id
        )
        SELECT 
            name,
            avg_score,
            CASE
                WHEN avg_score >= 90 THEN 'A'
                WHEN avg_score >= 80 THEN 'B'
                WHEN avg_score >= 70 THEN 'C'
                ELSE 'F'
            END AS grade
        FROM avg_table
        ORDER BY avg_score DESC
    """)

    data = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("grades.html", rows=data)


# ================= RUN ================= #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))