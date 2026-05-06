# app.py
from flask import Flask, render_template, request, redirect
import psycopg2

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ---------------- #
def connect():
    return psycopg2.connect(
        database="siwes_db",
        user="postgres",
        password="@Lam1200",
        host="localhost",
        port="5434"
    )


# ---------------- HOME ---------------- #
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- STUDENT MANAGEMENT ---------------- #
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
    conn.close()

    return redirect("/students")


@app.route("/students")
def view_students():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM students ORDER BY student_id")
    rows = cur.fetchall()
    conn.close()

    return render_template("students.html", students=rows)


@app.route("/update_student/<int:student_id>", methods=["GET", "POST"])
def update_student(student_id):
    conn = connect()
    cur = conn.cursor()

    if request.method == "POST":
        new_name = request.form["name"]
        new_department = request.form["department"]
        new_level = request.form["level"]

        cur.execute("""
            UPDATE students
            SET name = %s, department = %s, level = %s
            WHERE student_id = %s
        """, (new_name, new_department, new_level, student_id))

        conn.commit()
        conn.close()
        return redirect("/students")

    cur.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
    student = cur.fetchone()
    conn.close()

    return render_template("update_student.html", student=student)


@app.route("/delete_student/<int:student_id>")
def delete_student(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute("DELETE FROM courses WHERE student_id = %s", (student_id,))
    cur.execute("DELETE FROM students WHERE student_id = %s", (student_id,))

    conn.commit()
    conn.close()

    return redirect("/students")


# ---------------- COURSE MANAGEMENT ---------------- #
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
    conn.close()

    return redirect("/results")


@app.route("/results")
def view_results():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.name,
            c.course_name,
            c.score
        FROM students s
        JOIN courses c
        ON s.student_id = c.student_id
        ORDER BY s.name;
    """)

    rows = cur.fetchall()
    conn.close()

    return render_template("results.html", results=rows)


# ---------------- ANALYTICS ---------------- #
@app.route("/performance")
def performance_report():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.name,
            SUM(c.score) AS total_score,
            AVG(c.score) AS avg_score,
            RANK() OVER (ORDER BY SUM(c.score) DESC) AS ranking
        FROM students s
        JOIN courses c
        ON s.student_id = c.student_id
        GROUP BY s.student_id, s.name
        ORDER BY ranking;
    """)

    rows = cur.fetchall()
    conn.close()

    return render_template("performance.html", rows=rows)


@app.route("/top_students")
def top_students():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            s.name,
            SUM(c.score) AS total_score
        FROM students s
        JOIN courses c
        ON s.student_id = c.student_id
        GROUP BY s.student_id, s.name
        ORDER BY total_score DESC
        LIMIT 3;
    """)

    rows = cur.fetchall()
    conn.close()

    return render_template("top_students.html", rows=rows)


@app.route("/grades")
def grade_report():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        WITH student_avg AS (
            SELECT 
                s.name,
                AVG(c.score) AS avg_score
            FROM students s
            JOIN courses c
            ON s.student_id = c.student_id
            GROUP BY s.student_id, s.name
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
        FROM student_avg
        ORDER BY avg_score DESC;
    """)

    rows = cur.fetchall()
    conn.close()

    return render_template("grades.html", rows=rows)


if __name__ == "__main__":
    app.run(debug=True)