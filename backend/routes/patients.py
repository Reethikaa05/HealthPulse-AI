from flask import Blueprint, request, jsonify, session
from database import db, Patient
from ai_service import predict_health
from datetime import datetime, date

patients_bp = Blueprint('patients', __name__)

def require_auth():
    user_id = session.get('user_id')
    if not user_id:
        return None
    return user_id

@patients_bp.route('/', methods=['GET'])
def get_patients():
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '').strip()
    risk_filter = request.args.get('risk', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')

    query = Patient.query

    if search:
        query = query.filter(
            db.or_(
                Patient.full_name.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%')
            )
        )

    if risk_filter:
        query = query.filter(Patient.risk_level == risk_filter)

    sort_col = getattr(Patient, sort_by, Patient.created_at)
    if sort_dir == 'desc':
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'patients': [p.to_dict() for p in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page
    }), 200


@patients_bp.route('/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    patient = Patient.query.get_or_404(patient_id)
    return jsonify({'patient': patient.to_dict()}), 200


@patients_bp.route('/', methods=['POST'])
def create_patient():
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    errors = validate_patient_data(data)
    if errors:
        return jsonify({'errors': errors}), 400

    dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    glucose = float(data['glucose'])
    haemoglobin = float(data['haemoglobin'])
    cholesterol = float(data['cholesterol'])

    prediction = predict_health(glucose, haemoglobin, cholesterol)

    patient = Patient(
        full_name=data['full_name'].strip(),
        date_of_birth=dob,
        email=data['email'].strip().lower(),
        glucose=glucose,
        haemoglobin=haemoglobin,
        cholesterol=cholesterol,
        remarks=prediction['remarks'],
        risk_level=prediction['risk_level'],
        risk_score=prediction['risk_score'],
        created_by=user_id
    )
    db.session.add(patient)
    db.session.commit()

    return jsonify({'patient': patient.to_dict(), 'message': 'Patient created successfully'}), 201


@patients_bp.route('/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    errors = validate_patient_data(data)
    if errors:
        return jsonify({'errors': errors}), 400

    dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
    glucose = float(data['glucose'])
    haemoglobin = float(data['haemoglobin'])
    cholesterol = float(data['cholesterol'])

    prediction = predict_health(glucose, haemoglobin, cholesterol)

    patient.full_name = data['full_name'].strip()
    patient.date_of_birth = dob
    patient.email = data['email'].strip().lower()
    patient.glucose = glucose
    patient.haemoglobin = haemoglobin
    patient.cholesterol = cholesterol
    patient.remarks = prediction['remarks']
    patient.risk_level = prediction['risk_level']
    patient.risk_score = prediction['risk_score']
    patient.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'patient': patient.to_dict(), 'message': 'Patient updated successfully'}), 200


@patients_bp.route('/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    return jsonify({'message': 'Patient deleted successfully'}), 200


@patients_bp.route('/<int:patient_id>/reanalyze', methods=['POST'])
def reanalyze_patient(patient_id):
    user_id = require_auth()
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    patient = Patient.query.get_or_404(patient_id)
    prediction = predict_health(patient.glucose, patient.haemoglobin, patient.cholesterol)
    patient.remarks = prediction['remarks']
    patient.risk_level = prediction['risk_level']
    patient.risk_score = prediction['risk_score']
    patient.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'patient': patient.to_dict(), 'message': 'Analysis updated'}), 200


def validate_patient_data(data):
    errors = {}

    if not data.get('full_name', '').strip():
        errors['full_name'] = 'Full name is required'

    email = data.get('email', '').strip()
    if not email:
        errors['email'] = 'Email is required'
    elif '@' not in email or '.' not in email:
        errors['email'] = 'Invalid email format'

    dob_str = data.get('date_of_birth', '')
    if not dob_str:
        errors['date_of_birth'] = 'Date of birth is required'
    else:
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            if dob >= date.today():
                errors['date_of_birth'] = 'Date of birth must be in the past'
        except ValueError:
            errors['date_of_birth'] = 'Invalid date format (use YYYY-MM-DD)'

    for field in ['glucose', 'haemoglobin', 'cholesterol']:
        val = data.get(field)
        if val is None or str(val).strip() == '':
            errors[field] = f'{field.capitalize()} is required'
        else:
            try:
                num = float(val)
                if num < 0:
                    errors[field] = f'{field.capitalize()} must be a positive number'
            except (ValueError, TypeError):
                errors[field] = f'{field.capitalize()} must be a numeric value'

    return errors
