from flask_sqlalchemy import SQLAlchemy
import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ------------------- STUDENT -------------------
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    second_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    date_of_birth = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    grade_level = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.String(100), nullable=True) 
    # one student → many grades
    grades = db.relationship(
        'Grade',
        backref='student_obj',
        lazy=True,
        cascade="all, delete"   # 🔥 the fix
    )

    def __repr__(self):
        return f"<Student {self.first_name} {self.last_name}>"


# ------------------- TEACHER -------------------
class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    second_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50))
    hire_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Teacher {self.first_name} {self.last_name}>"


# ------------------- COURSE -------------------
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    credit = db.Column(db.Integer, default=1)

    # one course → many grades
    grades = db.relationship(
        'Grade',
        backref='course_obj',
        lazy=True,
        cascade="all, delete"   # 🔥 the fix
    )

    def __repr__(self):
        return f"<Course {self.course_name}>"


# ------------------- GRADE -------------------
class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)

    semester = db.Column(db.String(20))
    year = db.Column(db.Integer)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='student_course_uc'),
    )



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # roles: admin, teacher, student

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
