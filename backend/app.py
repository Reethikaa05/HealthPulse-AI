import os

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k.strip()] = v.strip().strip("'").strip('"')

from flask import Flask
from flask_cors import CORS
from database import db, seed_database
from routes.auth import auth_bp
from routes.patients import patients_bp
from routes.dashboard import dashboard_bp


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'healthpulse-dev-secret-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthpulse.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Cross-domain session cookie settings for production
if os.environ.get('RENDER') or os.environ.get('PORT'):
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'

CORS(app, supports_credentials=True, origins=[
    'https://health-pulse-ai-7sw4.vercel.app',
    'http://localhost:3000',
    'http://127.0.0.1:3000'
])
db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(patients_bp, url_prefix='/api/patients')
app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
