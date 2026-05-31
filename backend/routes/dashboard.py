from flask import Blueprint, jsonify, session
from database import db, Patient
from sqlalchemy import func
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

def require_auth():
    return session.get('user_id')

@dashboard_bp.route('/stats', methods=['GET'])
def get_stats():
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    total = Patient.query.count()
    risk_counts = db.session.query(Patient.risk_level, func.count(Patient.id))\
        .group_by(Patient.risk_level).all()

    risk_dist = {'Low': 0, 'Moderate': 0, 'High': 0, 'Critical': 0}
    for level, count in risk_counts:
        if level in risk_dist:
            risk_dist[level] = count

    avg_glucose = db.session.query(func.avg(Patient.glucose)).scalar() or 0
    avg_haemoglobin = db.session.query(func.avg(Patient.haemoglobin)).scalar() or 0
    avg_cholesterol = db.session.query(func.avg(Patient.cholesterol)).scalar() or 0

    # Last 7 days admissions
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_count = Patient.query.filter(Patient.created_at >= seven_days_ago).count()

    # Monthly trend (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        end = (start + timedelta(days=31)).replace(day=1)
        count = Patient.query.filter(
            Patient.created_at >= start,
            Patient.created_at < end
        ).count()
        monthly_data.append({
            'month': start.strftime('%b %Y'),
            'count': count
        })

    # Glucose distribution buckets
    glucose_buckets = {
        'Hypoglycemia (<70)': Patient.query.filter(Patient.glucose < 70).count(),
        'Normal (70-99)': Patient.query.filter(Patient.glucose.between(70, 99)).count(),
        'Pre-diabetic (100-125)': Patient.query.filter(Patient.glucose.between(100, 125)).count(),
        'Diabetic (126-200)': Patient.query.filter(Patient.glucose.between(126, 200)).count(),
        'Severe (>200)': Patient.query.filter(Patient.glucose > 200).count(),
    }

    # Cholesterol distribution
    chol_buckets = {
        'Desirable (<200)': Patient.query.filter(Patient.cholesterol < 200).count(),
        'Borderline (200-239)': Patient.query.filter(Patient.cholesterol.between(200, 239)).count(),
        'High (240-300)': Patient.query.filter(Patient.cholesterol.between(240, 300)).count(),
        'Very High (>300)': Patient.query.filter(Patient.cholesterol > 300).count(),
    }

    # Recent patients
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

    return jsonify({
        'total_patients': total,
        'risk_distribution': risk_dist,
        'averages': {
            'glucose': round(avg_glucose, 1),
            'haemoglobin': round(avg_haemoglobin, 1),
            'cholesterol': round(avg_cholesterol, 1)
        },
        'recent_admissions': recent_count,
        'monthly_trend': monthly_data,
        'glucose_distribution': glucose_buckets,
        'cholesterol_distribution': chol_buckets,
        'recent_patients': [p.to_dict() for p in recent_patients]
    }), 200
