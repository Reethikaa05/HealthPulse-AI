from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import bcrypt

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='doctor')
    avatar = db.Column(db.String(10), default='👨‍⚕️')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat()
        }

class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    glucose = db.Column(db.Float, nullable=False)
    haemoglobin = db.Column(db.Float, nullable=False)
    cholesterol = db.Column(db.Float, nullable=False)
    remarks = db.Column(db.Text, default='')
    risk_level = db.Column(db.String(20), default='Unknown')
    risk_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'date_of_birth': self.date_of_birth.isoformat(),
            'email': self.email,
            'glucose': self.glucose,
            'haemoglobin': self.haemoglobin,
            'cholesterol': self.cholesterol,
            'remarks': self.remarks,
            'risk_level': self.risk_level,
            'risk_score': self.risk_score,
            'age': self.age(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

def seed_database():
    if User.query.count() > 0:
        return

    # Seed users
    users_data = [
        {'name': 'Dr. Sarah Mitchell', 'email': 'admin@healthpulse.com', 'password': 'Admin@123', 'role': 'admin', 'avatar': '👩‍⚕️'},
        {'name': 'Dr. James Carter', 'email': 'doctor@healthpulse.com', 'password': 'Doctor@123', 'role': 'doctor', 'avatar': '👨‍⚕️'},
    ]
    for ud in users_data:
        u = User(name=ud['name'], email=ud['email'], role=ud['role'], avatar=ud['avatar'])
        u.set_password(ud['password'])
        db.session.add(u)
    db.session.flush()

    admin = User.query.filter_by(email='admin@healthpulse.com').first()

    # Seed patients
    from ai_service import predict_health
    patients_data = [
        {'full_name': 'Alice Johnson', 'dob': '1985-03-15', 'email': 'alice@example.com', 'glucose': 95.0, 'haemoglobin': 13.5, 'cholesterol': 185.0},
        {'full_name': 'Bob Martinez', 'dob': '1972-07-22', 'email': 'bob@example.com', 'glucose': 145.0, 'haemoglobin': 11.2, 'cholesterol': 240.0},
        {'full_name': 'Carol White', 'dob': '1990-11-08', 'email': 'carol@example.com', 'glucose': 88.0, 'haemoglobin': 14.1, 'cholesterol': 165.0},
        {'full_name': 'David Brown', 'dob': '1968-05-30', 'email': 'david@example.com', 'glucose': 210.0, 'haemoglobin': 10.5, 'cholesterol': 280.0},
        {'full_name': 'Emma Davis', 'dob': '1995-09-12', 'email': 'emma@example.com', 'glucose': 75.0, 'haemoglobin': 12.8, 'cholesterol': 175.0},
        {'full_name': 'Frank Wilson', 'dob': '1958-12-03', 'email': 'frank@example.com', 'glucose': 180.0, 'haemoglobin': 9.8, 'cholesterol': 310.0},
        {'full_name': 'Grace Lee', 'dob': '1988-04-18', 'email': 'grace@example.com', 'glucose': 102.0, 'haemoglobin': 13.9, 'cholesterol': 195.0},
        {'full_name': 'Henry Taylor', 'dob': '1975-08-25', 'email': 'henry@example.com', 'glucose': 130.0, 'haemoglobin': 12.0, 'cholesterol': 225.0},
        {'full_name': 'Iris Anderson', 'dob': '2000-01-14', 'email': 'iris@example.com', 'glucose': 82.0, 'haemoglobin': 14.5, 'cholesterol': 160.0},
        {'full_name': 'Jack Thomas', 'dob': '1963-06-07', 'email': 'jack@example.com', 'glucose': 165.0, 'haemoglobin': 10.1, 'cholesterol': 260.0},
    ]

    for pd_data in patients_data:
        prediction = predict_health(pd_data['glucose'], pd_data['haemoglobin'], pd_data['cholesterol'])
        p = Patient(
            full_name=pd_data['full_name'],
            date_of_birth=datetime.strptime(pd_data['dob'], '%Y-%m-%d').date(),
            email=pd_data['email'],
            glucose=pd_data['glucose'],
            haemoglobin=pd_data['haemoglobin'],
            cholesterol=pd_data['cholesterol'],
            remarks=prediction['remarks'],
            risk_level=prediction['risk_level'],
            risk_score=prediction['risk_score'],
            created_by=admin.id
        )
        db.session.add(p)

    db.session.commit()
    print("[OK] Database seeded successfully!")
