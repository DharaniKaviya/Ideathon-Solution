from datetime import datetime

from app import db  # if circular import occurs, move models into app.py


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="patient")
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="patient", lazy=True)
    prescriptions = db.relationship("Prescription", backref="patient", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "role": self.role,
            "age": self.age,
            "gender": self.gender,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Hospital(db.Model):
    __tablename__ = "hospitals"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    district = db.Column(db.String(50), nullable=False)
    taluk = db.Column(db.String(50), nullable=False)
    village = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    total_beds = db.Column(db.Integer, default=50)
    registration_status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctors = db.relationship("Doctor", backref="hospital", lazy=True)
    appointments = db.relationship("Appointment", backref="hospital", lazy=True)
    medicines = db.relationship("Medicine", backref="hospital", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "district": self.district,
            "taluk": self.taluk,
            "village": self.village,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "phone": self.phone,
            "email": self.email,
            "total_beds": self.total_beds,
            "registration_status": self.registration_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    availability_status = db.Column(db.String(20), default="available")
    consultation_fee = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True)
    prescriptions = db.relationship("Prescription", backref="doctor", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "specialization": self.specialization,
            "hospital_id": self.hospital_id,
            "phone": self.phone,
            "availability_status": self.availability_status,
            "consultation_fee": self.consultation_fee,
            "hospital_name": self.hospital.name if self.hospital else None,
        }


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.String(10), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="confirmed")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "doctor_id", "appointment_date", "appointment_time", name="uq_slot"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "hospital_id": self.hospital_id,
            "patient_name": self.patient.name if self.patient else None,
            "doctor_name": self.doctor.name if self.doctor else None,
            "hospital_name": self.hospital.name if self.hospital else None,
            "appointment_date": self.appointment_date.isoformat()
            if self.appointment_date
            else None,
            "appointment_time": self.appointment_time,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    generic_name = db.Column(db.String(150))
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), default="tablet")
    expiry_date = db.Column(db.Date, nullable=False)
    cost = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        today = datetime.now().date()
        return {
            "id": self.id,
            "hospital_id": self.hospital_id,
            "name": self.name,
            "generic_name": self.generic_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "expiry_date": self.expiry_date.isoformat()
            if self.expiry_date
            else None,
            "cost": self.cost,
            "is_available": self.quantity > 0,
            "is_expired": self.expiry_date < today if self.expiry_date else False,
        }


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)
    medicine_name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100))
    notes = db.Column(db.Text)
    prescribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor.name if self.doctor else None,
            "medicine_name": self.medicine_name,
            "dosage": self.dosage,
            "duration": self.duration,
            "notes": self.notes,
            "prescribed_at": self.prescribed_at.isoformat()
            if self.prescribed_at
            else None,
        }


class AwarenessContent(db.Model):
    __tablename__ = "awareness_content"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(10), default="EN")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "language": self.language,
            "created_at": self.created_at.isoformat()
            if self.created_at
            else None,
        }


class HealthScheme(db.Model):
    __tablename__ = "health_schemes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    eligibility = db.Column(db.Text)
    benefits = db.Column(db.Text)
    contact_info = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "eligibility": self.eligibility,
            "benefits": self.benefits,
            "contact_info": self.contact_info,
        }
