from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime
from flask_migrate import Migrate


app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- USER MODEL ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- STUDENT MODEL ----------------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)


# ---------------- GRADE MODEL ----------------
class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('grades', lazy=True))


# ---------------- ROUTES ----------------

@app.route("/")
@login_required
def home():

    students = Student.query.all()

    # ✅ Average grade
    
    
    average_grades = db.session.query(
    Grade.student_id,
    Student.first_name,
    Student.last_name,
    func.avg(Grade.score).label('average_score')
    ).join(Student, Student.id == Grade.student_id) \
    .group_by(Grade.student_id, Student.first_name, Student.last_name) \
    .all()

    average_grade = db.session.query(func.avg(Grade.score)).scalar()

     

    # ✅ Top student
    top_student_result = (
        db.session.query(Student, func.avg(Grade.score).label('avg_score'))
        .join(Grade, Student.id == Grade.student_id)
        .group_by(Student.id)
        .order_by(func.avg(Grade.score).desc())
        .first()
    )

    top_student = top_student_result[0] if top_student_result else None

    # ✅ Grade distribution
    grade_labels = ["A", "B", "C", "D", "F"]
    grade_counts = [0, 0, 0, 0, 0]

    grades = Grade.query.all()

    for g in grades:
        if g.score >= 90:
            grade_counts[0] += 1
        elif g.score >= 80:
            grade_counts[1] += 1
        elif g.score >= 70:
            grade_counts[2] += 1
        elif g.score >= 60:
            grade_counts[3] += 1
        else:
            grade_counts[4] += 1

    # ✅ Subject averages
    subject_data = (
        db.session.query(Grade.subject, func.avg(Grade.score))
        .group_by(Grade.subject)
        .all()
    )

    subjects = [row[0] for row in subject_data]
    subject_averages = [round(row[1], 2) for row in subject_data]

    return render_template(
        'index.html',
        students=students,
        average_grade=average_grade,
        top_student=top_student,
        grade_labels=grade_labels,
        grade_counts=grade_counts,
        subjects=subjects,
        subject_averages=subject_averages
    )





# ---------------- STUDENTS ----------------
@app.route('/students', methods=['GET', 'POST'])
@login_required
def students_page():

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form.get('email')
        student_id = request.form['student_id']

        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists!', 'error')
            return redirect(url_for('students_page'))

        if email and Student.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('students_page'))

        new_student = Student(
            first_name=first_name,
            last_name=last_name,
            email=email,
            student_id=student_id
        )

        db.session.add(new_student)
        db.session.commit()

        flash('Student added successfully!', 'success')
        return redirect(url_for('students_page'))

    students = Student.query.all()
    return render_template("students.html", students=students)


@app.route('/edit_student/<int:student_id>', methods=['POST'])
@login_required
def edit_student(student_id):

    student = Student.query.get_or_404(student_id)

    student.first_name = request.form['first_name']
    student.last_name = request.form['last_name']
    student.email = request.form.get('email')
    student.student_id = request.form['student_id']

    db.session.commit()

    flash('Student updated successfully!', 'success')
    return redirect(url_for('students_page'))


@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):

    student = Student.query.get_or_404(student_id)

    db.session.delete(student)
    db.session.commit()

    flash('Student deleted successfully!', 'success')
    return redirect(url_for('students_page'))



# ---------------- STUDENT GRADES ----------------
@app.route('/grades/<int:student_id>', methods=['GET', 'POST'])
@login_required
def grades_page(student_id):
    # Get the student or 404
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        # Add a new grade
        subject = request.form['subject']
        score = float(request.form['score'])

        new_grade = Grade(
            student_id=student_id,
            subject=subject,
            score=score
        )

        db.session.add(new_grade)
        db.session.commit()

        flash('Grade added successfully!', 'success')
        return redirect(url_for('grades_page', student_id=student_id))

    # GET request → show grades
    grades = Grade.query.filter_by(student_id=student_id).all()
    return render_template("grades.html", student=student, grades=grades)





# ---------------- AUTH ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        user = User(
            username=username,
            password=password,
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email']
        )

        db.session.add(user)
        db.session.commit()

        flash('User registered successfully!', 'success')
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        user = User.query.filter_by(username=request.form['username']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))

        flash('Invalid credentials', 'error')

    return render_template("login.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
    
# ---------------- STUDENT REPORTS ----------------
@app.route('/reports')
@login_required
def student_reports_page():
    # List to hold tuples: (student, average_score)
    student_reports_with_avg = []

    # Fetch all students
    students = Student.query.all()

    for student in students:
        # Calculate average score for this student
        if student.grades:
            avg_score = sum([grade.score for grade in student.grades]) / len(student.grades)
        else:
            avg_score = 0  # or None if you prefer

        student_reports_with_avg.append((student, avg_score))

    # Pass to template
    return render_template("reports.html", student_reports=student_reports_with_avg, page='reports')


@app.route('/settings')
@login_required
def settings_page():
    return render_template("settings.html")

# --- Update User Profile ---
@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password')

    current_user.first_name = first_name
    current_user.last_name = last_name
    current_user.email = email

    if password:
        current_user.set_password(password)  # Use your User model's password hashing

    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('settings_page'))

# --- Update Report Settings ---
@app.route('/update_report_settings', methods=['POST'])
@login_required
def update_report_settings():
    grading_scale = request.form.get('grading_scale', type=int)
    passing_mark = request.form.get('passing_mark', type=float)
    dark_mode = request.form.get('dark_mode') == 'on'

    current_user.grading_scale = grading_scale
    current_user.passing_mark = passing_mark
    current_user.dark_mode = dark_mode

    db.session.commit()
    flash("Report settings updated successfully!", "success")
    return redirect(url_for('settings_page'))

# --- Update Admin Settings ---
@app.route('/update_admin_settings', methods=['POST'])
@login_required
def update_admin_settings():
    if not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for('settings_page'))

    allow_registration = request.form.get('allow_user_registration') == 'on'
    default_sort = request.form.get('default_sort')

    current_user.allow_user_registration = allow_registration
    current_user.default_sort = default_sort

    db.session.commit()
    flash("Admin settings updated successfully!", "success")
    return redirect(url_for('settings_page'))




# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
