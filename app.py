from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from datetime import datetime
from flask_migrate import Migrate

# --- ReportLab PDF imports ---
from io import BytesIO
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message

from itsdangerous import URLSafeTimedSerializer


import pandas as pd
import os
from werkzeug.utils import secure_filename





app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['SECRET_KEY'] = '9f3b2d8c4a1e5f7b0c8a2d4e6f1b3c9a8d7e6f4a1b2c3d4e5f6a7b8c9d0e1f2'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 8025
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None

mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ---------------- USER MODEL ----------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed passwords
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    # ✅ REPORT SETTINGS
    grading_scale = db.Column(db.Integer, default=100)
    passing_mark = db.Column(db.Float, default=40)
    dark_mode = db.Column(db.Boolean, default=False)
    # ✅ ADMIN SETTINGS
    allow_user_registration = db.Column(db.Boolean, default=True)
    default_sort = db.Column(db.String(20), default="name")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


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
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy



class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    passmark = db.Column(db.Float, nullable=False, server_default='40')
    passed = db.Column(db.Boolean, nullable=False, server_default='0')
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', backref=db.backref('grades', lazy=True))

    # Optional helper to calculate passed
    def calculate_passed(self):
        self.passed = self.score >= self.passmark




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

    new_email = request.form.get('email')
    new_student_id = request.form['student_id']

    # prevent duplicate student_id
    existing_id = Student.query.filter(
        Student.student_id == new_student_id,
        Student.id != student_id
    ).first()

    if existing_id:
        flash('Student ID already exists!', 'error')
        return redirect(url_for('students_page'))

    # prevent duplicate email
    if new_email:
        existing_email = Student.query.filter(
            Student.email == new_email,
            Student.id != student_id
        ).first()

        if existing_email:
            flash('Email already exists!', 'error')
            return redirect(url_for('students_page'))

    student.first_name = request.form['first_name']
    student.last_name = request.form['last_name']
    student.email = new_email
    student.student_id = new_student_id

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
        passmark = float(request.form.get('passmark', 40))  # default 40 if not provided

        # Automatically determine if passed
        passed = score >= passmark

        new_grade = Grade(
            student_id=student_id,
            subject=subject,
            score=score,
            passmark=passmark,
            passed=passed
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
    # List to hold all grades with student info
    grades_list = []

    # Fetch all students
    students = Student.query.all()

    for student in students:
        # Calculate average score for this student
        if student.grades:
            avg_score = sum([grade.score for grade in student.grades]) / len(student.grades)
        else:
            avg_score = 0

        for grade in student.grades:
            grades_list.append({
                'student_name': f"{student.first_name} {student.last_name}",
                'subject': grade.subject,
                'score': grade.score,
                'passmark': grade.passmark,
                'passed': grade.passed,
                'date_added': grade.date_added,
                'average_score': round(avg_score, 2)  # include average
            })

    # Pass to template as "grades"
    return render_template("reports.html", grades=grades_list)



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

    
@app.route('/download-report')
@login_required
def download_report():
    from io import BytesIO
    from flask import send_file
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib import colors

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    # Optional: Add logo
    try:
        logo = Image("static/zcas_logo.png", width=100, height=50)
        elements.append(logo)
        elements.append(Spacer(1, 12))
    except:
        pass

    # Table header
    data = [["Student", "Subject", "Score", "Passmark", "Remark", "Average", "Date"]]

    # Fetch students and calculate averages
    students = Student.query.all()
    for student in students:
        if student.grades:
            avg_score = sum([g.score for g in student.grades]) / len(student.grades)
        else:
            avg_score = 0
        for grade in student.grades:
            remark = "Passed" if grade.passed else "Failed"
            data.append([
                f"{student.first_name} {student.last_name}",
                grade.subject,
                grade.score,
                grade.passmark,
                remark,
                "%.2f" % avg_score,
                grade.date_added.strftime("%Y-%m-%d")
            ])

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#004aad')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (2,1), (4,-1), 'CENTER'),  # center numeric columns
    ]))
    elements.append(table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="student_report.pdf",
        mimetype='application/pdf'
    )


@app.route('/users', methods=['GET', 'POST'])
@login_required
def user_management_page():
    # Only admins can access
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access", "danger")
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form

        # Check duplicates
        if User.query.filter_by(username=username).first():
            flash("Username already exists!", "error")
            return redirect(url_for('user_management_page'))
        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "error")
            return redirect(url_for('user_management_page'))

        # Create new user
        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=generate_password_hash(password),
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()

        flash("User added successfully!", "success")
        return redirect(url_for('user_management_page'))

    # GET request → show users
    users = User.query.all()
    return render_template("users.html", users=users, page='users')

@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash("You do not have permission to delete users.")
        return redirect(url_for('user_management_page'))

    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.")
    return redirect(url_for('user_management_page'))

@login_required
@app.route('/add_user', methods=['POST'])
def add_user():
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = request.form['password']
    is_admin = 'is_admin' in request.form

    # Create user object
    new_user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        is_admin=is_admin
    )
    new_user.set_password(password)  # ✅ hashes the password
    db.session.add(new_user)
    db.session.commit()

    flash('User added successfully!', 'success')
    return redirect(url_for('user_management_page'))

    
@login_required
@app.route('/edit_user/<int:user_id>', methods=['POST'])
def edit_user(user_id):
    user = User.query.get(user_id)  # or session.get(User, user_id) for SQLAlchemy 2.0
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('user_management_page'))

    user.username = request.form['username']
    user.first_name = request.form['first_name']
    user.last_name = request.form['last_name']
    user.email = request.form['email']
    user.is_admin = 'is_admin' in request.form
    password = request.form.get('password')
    if password:
        user.set_password(password)  # update password only if entered

    db.session.commit()
    flash('User updated successfully!', 'success')
    return redirect(url_for('user_management_page'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # Get the new password fields
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Simple validation
        if not new_password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for('forgot_password'))

        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('forgot_password'))

        # Here you would normally save the new password to the database
        flash("Password changed successfully!", "success")
        return redirect(url_for('login'))

    # GET request: show form
    return render_template('reset_password.html')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        # Get the new passwords from the form
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Simple validation
        if not new_password or not confirm_password:
            flash("Please fill in all fields.", "error")
            return redirect(url_for('reset_password'))

        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('reset_password'))

        # Here you would normally update the password in your database
        # For now, just flash a success message
        flash("Password updated successfully!", "success")
        return redirect(url_for('login'))

    # GET request: show the reset password form
    return render_template('reset_password.html')  # Your HTML file name



@app.route('/upload-students', methods=['POST'])
@login_required
def upload_students():
    # Only admins can upload
    if not getattr(current_user, 'is_admin', False):
        flash("Unauthorized access", "danger")
        return redirect(url_for('students_page'))

    file = request.files.get('file')
    if not file:
        flash("No file selected!", "error")
        return redirect(url_for('students_page'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Detect file type
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            flash("Unsupported file type! Only CSV or XLSX allowed.", "error")
            return redirect(url_for('students_page'))

        # Loop through rows and add students
        added = 0
        skipped = 0
        for _, row in df.iterrows():
            # Skip rows with missing required fields
            if pd.isna(row.get('first_name')) or pd.isna(row.get('last_name')) or pd.isna(row.get('student_id')):
                skipped += 1
                continue

            # Skip duplicates
            if Student.query.filter_by(student_id=row['student_id']).first():
                skipped += 1
                continue

            new_student = Student(
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row.get('email'),
                student_id=row['student_id']
            )
            db.session.add(new_student)
            added += 1

        db.session.commit()
        flash(f"Upload completed: {added} added, {skipped} skipped.", "success")
    except Exception as e:
        flash(f"Failed to upload file: {str(e)}", "error")

    return redirect(url_for('students_page'))




# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
