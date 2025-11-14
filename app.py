from flask import Flask, render_template, request, redirect, url_for
from models import db
from models import Student, Teacher, Course, Grade
import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_db.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to get the correct image URL
def get_profile_pic_url(filename):
    if filename:
        return url_for('static', filename=f'uploads/{filename}')
    return url_for('static', filename='images/default_profile.png')  # Add a default image

@app.route('/')
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
def students():
    students = Student.query.all()
    return render_template('students.html', students=students, get_profile_pic_url=get_profile_pic_url)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    courses = Course.query.all()
    if request.method == 'POST':
        first = request.form['first_name']
        second = request.form.get('second_name')
        last = request.form['last_name']
        gender = request.form['gender']
        dob_str = request.form['date_of_birth']
        grade_level = request.form['grade_level']
        dob = datetime.datetime.strptime(dob_str, '%Y-%m-%d')

        profile_file = request.files.get('profile_pic')
        filename = None
        if profile_file and allowed_file(profile_file.filename):
            filename = secure_filename(profile_file.filename)
            # Make sure upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            # Create unique filename to avoid overwrites
            unique_filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
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
            profile_pic=filename
        )

        db.session.add(student)
        db.session.commit()
        return redirect(url_for('students'))

    return render_template('add_student.html', courses=courses)

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    # Delete the profile picture file if it exists
    if student.profile_pic:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], student.profile_pic))
        except:
            pass  # If file doesn't exist, continue
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('students')) 

# Teacher routes
@app.route('/teachers')
def show_teachers():
    teachers = Teacher.query.all()
    return render_template('teachers.html', teachers=teachers)

@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == "POST":
        first = request.form['first_name']
        second = request.form.get('second_name')
        last = request.form['last_name']
        gender = request.form['gender']
        department = request.form.get('department')
        hire_date = datetime.datetime.strptime(request.form['hire_date'], '%Y-%m-%d')

        teacher = Teacher(
            first_name=first,
            second_name=second,
            last_name=last,
            gender=gender,
            department=department,
            hire_date=hire_date
        )
        db.session.add(teacher)
        db.session.commit()
        return redirect(url_for('show_teachers'))

    return render_template('add_teacher.html')

@app.route('/delete_teacher/<int:teacher_id>', methods=['POST'])
def delete_teacher(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    return redirect(url_for('show_teachers')) 

# Course routes
@app.route('/courses')
def show_courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@app.route('/add_course', methods=['GET', 'POST'])
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
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return redirect(url_for('show_courses'))

# Grade routes
@app.route('/grades')
def show_grades():
    grades = Grade.query.all()
    return render_template('grades.html', grades=grades)

@app.route('/add_grade', methods=['GET', 'POST'])
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

# Grade level routes
@app.route('/grade_levels')
def grade_levels():
    grades = db.session.query(Student.grade_level).distinct().all()
    grades = [g[0] for g in grades if g[0]]
    return render_template('grade_levels.html', grades=grades)

@app.route('/students_by_grade/<grade_level>')
def students_by_grade(grade_level):
    students = Student.query.filter_by(grade_level=grade_level).all()
    return render_template('students_by_grade.html', grade_level=grade_level, students=students, get_profile_pic_url=get_profile_pic_url)

@app.route('/delete_grade/<int:grade_id>', methods=['POST'])
def delete_grade(grade_id):
    grade = Grade.query.get_or_404(grade_id)
    db.session.delete(grade)
    db.session.commit()
    return redirect(url_for('show_grades'))

if __name__ == "__main__":
    with app.app_context():
        # Create uploads directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        db.create_all()
        app.run(debug=True)