"""
Rural Healthcare System - Flask Backend
Main Application Entry Point
"""

from datetime import datetime, timedelta
import math
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)

    # ---------- CONFIG ----------
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "mysql+pymysql://root:password@localhost/rural_healthcare",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv(
        "JWT_SECRET_KEY", "change-this-secret-in-production"
    )
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=30)

    CORS(app)
    db.init_app(app)
    jwt.init_app(app)

    from models import (
        User,
        Hospital,
        Doctor,
        Appointment,
        Medicine,
        Prescription,
        AwarenessContent,
        HealthScheme,
    )

    # ---------- UTIL ----------

    def calculate_distance(lat1, lon1, lat2, lon2):
        """Haversine distance in km."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)

    # ---------- AUTH ----------

    @app.post("/api/auth/register")
    def register():
        data = request.get_json() or {}
        phone = data.get("phone")
        password = data.get("password")
        role = data.get("role", "patient")

        if not phone or not password:
            return jsonify({"error": "Phone and password required"}), 400

        try:
            if role == "patient":
                if User.query.filter_by(phone=phone).first():
                    return jsonify({"error": "User already exists"}), 409

                user = User(
                    name=data.get("name", ""),
                    phone=phone,
                    email=data.get("email"),
                    role="patient",
                    age=data.get("age"),
                    gender=data.get("gender"),
                )
                user.password_hash = generate_password_hash(password)
                db.session.add(user)
                db.session.commit()
                return (
                    jsonify(
                        {"message": "Patient registered", "user": user.to_dict()}
                    ),
                    201,
                )

            if role == "hospital":
                email = data.get("email")
                if not email:
                    return jsonify({"error": "Email required for hospital"}), 400
                if Hospital.query.filter_by(email=email).first():
                    return jsonify({"error": "Hospital already exists"}), 409

                hospital = Hospital(
                    name=data.get("name", ""),
                    district=data.get("district", ""),
                    taluk=data.get("taluk", ""),
                    village=data.get("village", ""),
                    latitude=float(data.get("latitude", 10.7905)),
                    longitude=float(data.get("longitude", 78.7047)),
                    phone=phone,
                    email=email,
                    total_beds=int(data.get("total_beds", 50)),
                )
                hospital.password_hash = generate_password_hash(password)
                db.session.add(hospital)
                db.session.commit()
                return (
                    jsonify(
                        {
                            "message": "Hospital registered (pending approval)",
                            "hospital": hospital.to_dict(),
                        }
                    ),
                    201,
                )

            return jsonify({"error": "Invalid role"}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Registration failed: {e}"}), 500

    @app.post("/api/auth/login")
    def login():
        data = request.get_json() or {}
        phone = data.get("phone")
        password = data.get("password")
        role = data.get("role", "patient")

        if not phone or not password:
            return jsonify({"error": "Phone and password required"}), 400

        try:
            if role == "patient":
                user = User.query.filter_by(phone=phone).first()
                if not user or not check_password_hash(user.password_hash, password):
                    return jsonify({"error": "Invalid credentials"}), 401
                token = create_access_token(identity={"id": user.id, "role": "patient"})
                return (
                    jsonify(
                        {
                            "message": "Login successful",
                            "access_token": token,
                            "user": user.to_dict(),
                        }
                    ),
                    200,
                )

            if role == "hospital":
                # hospital login uses email as 'phone' field in frontend
                hospital = Hospital.query.filter_by(email=phone).first()
                if not hospital or not check_password_hash(
                    hospital.password_hash, password
                ):
                    return jsonify({"error": "Invalid credentials"}), 401
                if hospital.registration_status != "approved":
                    return jsonify({"error": "Hospital not approved"}), 403
                token = create_access_token(
                    identity={"id": hospital.id, "role": "hospital"}
                )
                return (
                    jsonify(
                        {
                            "message": "Login successful",
                            "access_token": token,
                            "hospital": hospital.to_dict(),
                        }
                    ),
                    200,
                )

            if role == "admin":
                # hard-coded admin for demo
                if phone != "admin" or password != "admin123":
                    return jsonify({"error": "Invalid admin credentials"}), 401
                token = create_access_token(identity={"id": 0, "role": "admin"})
                return (
                    jsonify(
                        {
                            "message": "Admin login successful",
                            "access_token": token,
                        }
                    ),
                    200,
                )

            return jsonify({"error": "Invalid role"}), 400
        except Exception as e:
            return jsonify({"error": f"Login failed: {e}"}), 500

    # ---------- PATIENT: LOCATION & DOCTORS ----------

    @app.post("/api/hospitals/nearby")
    def hospitals_nearby():
        data = request.get_json() or {}
        lat = float(data.get("latitude", 10.7905))
        lon = float(data.get("longitude", 78.7047))
        radius = float(data.get("radius", 50))

        try:
            hospitals = Hospital.query.filter_by(registration_status="approved").all()
            result = []
            for h in hospitals:
                d = calculate_distance(lat, lon, h.latitude, h.longitude)
                if d <= radius:
                    item = h.to_dict()
                    item["distance"] = d
                    item["available_doctors"] = sum(
                        1 for dtr in h.doctors if dtr.availability_status == "available"
                    )
                    result.append(item)
            result.sort(key=lambda x: x["distance"])
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"error": f"Failed to fetch hospitals: {e}"}), 500

    @app.post("/api/doctors/nearby")
    def doctors_nearby():
        data = request.get_json() or {}
        lat = float(data.get("latitude", 10.7905))
        lon = float(data.get("longitude", 78.7047))
        radius = float(data.get("radius", 50))
        specialization = data.get("specialization")

        try:
            hospitals = Hospital.query.filter_by(registration_status="approved").all()
            doctors_result = []
            for h in hospitals:
                d = calculate_distance(lat, lon, h.latitude, h.longitude)
                if d <= radius:
                    for doc in h.doctors:
                        if specialization and doc.specialization.lower() != specialization.lower():
                            continue
                        item = doc.to_dict()
                        item["distance"] = d
                        doctors_result.append(item)
            doctors_result.sort(key=lambda x: x["distance"])
            return jsonify(doctors_result), 200
        except Exception as e:
            return jsonify({"error": f"Failed to fetch doctors: {e}"}), 500

    # ---------- PATIENT: APPOINTMENTS & PRESCRIPTIONS ----------

    @app.post("/api/appointments/book")
    @jwt_required()
    def book_appointment():
        identity = get_jwt_identity() or {}
        if identity.get("role") != "patient":
            return jsonify({"error": "Only patients can book"}), 403

        data = request.get_json() or {}
        patient_id = identity["id"]
        doctor_id = data.get("doctor_id")
        hospital_id = data.get("hospital_id")
        date_str = data.get("appointment_date")
        time_str = data.get("appointment_time")
        reason = data.get("reason")

        if not all([doctor_id, hospital_id, date_str, time_str, reason]):
            return jsonify({"error": "Missing fields"}), 400

        try:
            apt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if apt_date < datetime.now().date():
                return jsonify({"error": "Date must be in future"}), 400

            existing = Appointment.query.filter_by(
                doctor_id=doctor_id,
                appointment_date=apt_date,
                appointment_time=time_str,
            ).first()
            if existing:
                return jsonify({"error": "Slot already booked"}), 409

            appt = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                hospital_id=hospital_id,
                appointment_date=apt_date,
                appointment_time=time_str,
                reason=reason,
            )
            db.session.add(appt)
            db.session.commit()
            return (
                jsonify(
                    {
                        "message": "Appointment booked",
                        "appointment": appt.to_dict(),
                    }
                ),
                201,
            )
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Booking failed: {e}"}), 500

    @app.get("/api/appointments/my")
    @jwt_required()
    def my_appointments():
        identity = get_jwt_identity() or {}
        if identity.get("role") != "patient":
            return jsonify({"error": "Only patients allowed"}), 403
        try:
            appts = Appointment.query.filter_by(patient_id=identity["id"]).all()
            return jsonify([a.to_dict() for a in appts]), 200
        except Exception as e:
            return jsonify({"error": f"Failed to fetch: {e}"}), 500

    @app.put("/api/appointments/<int:apt_id>/cancel")
    @jwt_required()
    def cancel_appointment(apt_id):
        identity = get_jwt_identity() or {}
        if identity.get("role") != "patient":
            return jsonify({"error": "Only patients allowed"}), 403
        try:
            appt = Appointment.query.get(apt_id)
            if not appt or appt.patient_id != identity["id"]:
                return jsonify({"error": "Appointment not found"}), 404
            if appt.status != "confirmed":
                return jsonify({"error": "Can cancel only confirmed"}), 400
            appt.status = "cancelled"
            db.session.commit()
            return jsonify({"message": "Cancelled", "appointment": appt.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Cancel failed: {e}"}), 500

    @app.get("/api/prescriptions/my")
    @jwt_required()
    def my_prescriptions():
        identity = get_jwt_identity() or {}
        if identity.get("role") != "patient":
            return jsonify({"error": "Only patients allowed"}), 403
        try:
            presc = Prescription.query.filter_by(patient_id=identity["id"]).all()
            return jsonify([p.to_dict() for p in presc]), 200
        except Exception as e:
            return jsonify({"error": f"Failed to fetch: {e}"}), 500

    # ---------- PUBLIC ----------

    @app.get("/api/awareness/all")
    def awareness_all():
        lang = request.args.get("language", "EN")
        try:
            items = AwarenessContent.query.filter_by(language=lang).all()
            return jsonify([i.to_dict() for i in items]), 200
        except Exception as e:
            return jsonify({"error": f"Failed to fetch: {e}"}), 500

    @app.get("/api/health-schemes")
    def health_schemes():
        try:
            schemes = HealthScheme.query.all()
            return jsonify([s.to_dict() for s in schemes]), 200
        except Exception as e:
            return jsonify({"error": f"Failed to fetch: {e}"}), 500

    @app.get("/api/health")
    def health():
        return jsonify({"status": "OK", "time": datetime.utcnow().isoformat()}), 200

    # ---------- ERROR HANDLERS ----------

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(_):
        db.session.rollback()
        return jsonify({"error": "Server error"}), 500

    # ---------- INIT DB ----------

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("APP_PORT", 5000)), debug=True)
