from flask import Flask, render_template, request, redirect, url_for, abort
from models import db, Student, Teacher, Course, Grade, User
import datetime
import os
import uuid
from werkzeug.utils import secure_filename
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user
)
from functools import wraps

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = "simoon123"

db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role decorators
def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Helper functions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_profile_pic_url(filename):
    if filename:
        return url_for('static', filename=f'uploads/{filename}')
    return url_for('static', filename='images/default_profile.png')

@app.context_processor
def utility_processor():
    return dict(get_profile_pic_url=get_profile_pic_url)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        second_name = request.form.get('second_name')
        gender = request.form['gender']
        dob_str = request.form['date_of_birth']
        grade_level = request.form['grade_level']
        
        # Force all public signups to be students only
        role = 'student'

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return "Username already taken", 400

        # Handle profile picture upload
        profile_file = request.files.get('profile_pic')
        filename = None

        if profile_file and profile_file.filename:
            if allowed_file(profile_file.filename):
                # Generate unique filename
                ext = profile_file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4()}.{ext}"
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                profile_file.save(file_path)
                filename = unique_filename
            else:
                return "Invalid file type. Please upload JPG, PNG, or GIF images.", 400

        # Convert date string to datetime
        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d')

        # Create the user
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()  # Get the user ID

        # Create student profile with provided information
        student = Student(
            first_name=first_name,
            last_name=last_name,
            second_name=second_name,
            gender=gender,
            date_of_birth=dob,
            grade_level=grade_level,
            profile_pic=filename,  # Save the profile picture filename
            user_id=new_user.id   # Link to the user
        )
        db.session.add(student)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return "Invalid username or password", 401

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Home - accessible to all authenticated users
@app.route('/')
@login_required
def home():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_courses = Course.query.count()
    return render_template(
        'home.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses
    )

# Student routes
@app.route('/students')
@login_required
def students():
    # Students can only see their own profile
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if student:
            return render_template('student_profile.html', student=student)
        else:
            return "Student profile not found. Please contact administrator.", 404
    
    # Admins and teachers can see all students
    students = Student.query.all()
    return render_template('students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'teacher')
def add_student():
    courses = Course.query.all()
    users = User.query.filter_by(role='student', student=None).all()  # Users without student profiles
    
    if request.method == 'POST':
        first = request.form['first_name']
        second = request.form.get('second_name')
        last = request.form['last_name']
        gender = request.form['gender']
        dob_str = request.form['date_of_birth']
        grade_level = request.form['grade_level']
        user_id = request.form.get('user_id')

        if not first or not last or not dob_str:
            return "Missing required fields", 400

        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d')

        profile_file = request.files.get('profile_pic')
        filename = None

        if profile_file and allowed_file(profile_file.filename):
            ext = profile_file.filename.rsplit('.', 1)[1]
            unique_filename = f"{uuid.uuid4()}.{ext}"
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            profile_file.save(file_path)
            filename = unique_filename

        student = Student(
            first_name=first,
            second_name=second,
            last_name=last,
            gender=gender,
            date_of_birth=dob,
            grade_level=grade_level,
            profile_pic=filename,
            user_id=user_id if user_id else None
        )

        db.session.add(student)
        db.session.commit()
        return redirect(url_for('students'))

    return render_template('add_student.html', courses=courses, users=users)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    if student.profile_pic:
        path = os.path.join(app.config['UPLOAD_FOLDER'], student.profile_pic)
        if os.path.exists(path):
            os.remove(path)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('students'))

# Student-specific routes
@app.route('/my_profile')
@login_required
@role_required('student')
def my_profile():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return "Student profile not found. Please contact administrator.", 404
    return render_template('student_profile.html', student=student)

@app.route('/my_grades')
@login_required
@role_required('student')
def my_grades():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return "Student profile not found. Please contact administrator.", 404
    
    grades = Grade.query.filter_by(student_id=student.id).all()
    return render_template('student_grades.html', student=student, grades=grades)

@app.route('/my_courses')
@login_required
@role_required('student')
def my_courses():
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        return "Student profile not found. Please contact administrator.", 404
    
    grades = Grade.query.filter_by(student_id=student.id).all()
    courses = [grade.course_obj for grade in grades]
    return render_template('student_courses.html', student=student, courses=courses)

# Teacher routes
@app.route('/teachers')
@login_required
@roles_required('admin', 'teacher')
def show_teachers():
    teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/add_teacher', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_teacher():
    users = User.query.filter_by(role='teacher', teacher=None).all()  # Users without teacher profiles
    
    if request.method == "POST":
        first = request.form['first_name']
        second = request.form.get('second_name')
        last = request.form['last_name']
        gender = request.form['gender']
        department = request.form.get('department')
        hire_date = datetime.datetime.strptime(request.form['hire_date'], '%Y-%m-%d')
        user_id = request.form.get('user_id')

        teacher = Teacher(
            first_name=first,
            second_name=second,
            last_name=last,
            gender=gender,
            department=department,
            hire_date=hire_date,
            user_id=user_id if user_id else None
        )
        db.session.add(teacher)
        db.session.commit()
        return redirect(url_for('show_teachers'))

    return render_template('add_teacher.html', users=users)

@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    return redirect(url_for('show_teachers'))

# Course routes
@app.route('/courses')
@login_required
@roles_required('admin', 'teacher', 'student')
def show_courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@app.route('/add_course', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'teacher')
def add_course():
    if request.method == 'POST':
        name = request.form['course_name']
        credit = request.form.get('credit', 1, type=int)

        course = Course(course_name=name, credit=credit)
        db.session.add(course)
        db.session.commit()
        return redirect(url_for('show_courses'))

    return render_template('add_course.html')

@app.route('/delete_course/<int:course_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('show_courses'))

# Grade routes
@app.route('/grades')
@login_required
@roles_required('admin', 'teacher')
def show_grades():
    grades = Grade.query.all()
    return render_template('grades.html', grades=grades)

@app.route('/add_grade', methods=['GET', 'POST'])
@login_required
@roles_required('admin', 'teacher')
def add_grade():
    students = Student.query.all()
    courses = Course.query.all()
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        semester = request.form.get('semester')
        year = request.form.get('year', type=int)

        if not student_id or not course_id:
            return "Error: student and course must be selected", 400

        grade = Grade(
            student_id=student_id,
            course_id=course_id,
            semester=semester,
            year=year
        )
        db.session.add(grade)
        db.session.commit()
        return redirect(url_for('show_grades'))

    return render_template('add_grade.html', students=students, courses=courses)

@app.route('/delete_grade/<int:grade_id>', methods=['POST'])
@login_required
@roles_required('admin', 'teacher')
def delete_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    db.session.delete(grade)
    db.session.commit()
    return redirect(url_for('show_grades'))

# Grade levels
@app.route('/grade_levels')
@login_required
@roles_required('admin', 'teacher')
def grade_levels():
    grades = db.session.query(Student.grade_level).distinct().all()
    grades = [g[0] for g in grades if g[0]]
    return render_template('grade_levels.html', grades=grades)

@app.route('/students_by_grade/<grade_level>')
@login_required
@roles_required('admin', 'teacher')
def students_by_grade(grade_level):
    students = Student.query.filter_by(grade_level=grade_level).all()
    return render_template('students_by_grade.html', grade_level=grade_level, students=students)

# Error handlers
@app.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == "__main__":
    with app.app_context():
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
        app.run(debug=True)