-- ============================================================
-- Rural Healthcare System - MySQL Database Schema + Sample Data
-- ============================================================

-- 1. Create database
CREATE DATABASE IF NOT EXISTS rural_healthcare;
USE rural_healthcare;

-- 2. Clean existing tables (for fresh setup)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS medicines;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS awareness_content;
DROP TABLE IF EXISTS health_schemes;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS hospitals;
DROP TABLE IF EXISTS users;
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================
-- USERS (patients)
-- ==========================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'patient',      -- 'patient' only in this table
    age INT,
    gender VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_phone (phone),
    INDEX idx_users_role (role)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- HOSPITALS
-- ==========================
CREATE TABLE hospitals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    district VARCHAR(50) NOT NULL,
    taluk VARCHAR(50) NOT NULL,
    village VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    total_beds INT DEFAULT 50,
    registration_status VARCHAR(20) DEFAULT 'approved', -- 'approved','pending','rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_hosp_district (district),
    INDEX idx_hosp_status (registration_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- DOCTORS
-- ==========================
CREATE TABLE doctors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    hospital_id INT NOT NULL,
    phone VARCHAR(15) NOT NULL,
    availability_status VARCHAR(20) DEFAULT 'available', -- 'available','off-duty'
    consultation_fee DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_doctors_hospital
        FOREIGN KEY (hospital_id)
        REFERENCES hospitals(id)
        ON DELETE CASCADE,
    INDEX idx_doctors_hospital (hospital_id),
    INDEX idx_doctors_specialization (specialization),
    INDEX idx_doctors_availability (availability_status)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- APPOINTMENTS
-- ==========================
CREATE TABLE appointments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    hospital_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(10) NOT NULL,  -- e.g. '10:00'
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed', -- 'confirmed','cancelled','completed'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_apt_patient
        FOREIGN KEY (patient_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_apt_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_apt_hospital
        FOREIGN KEY (hospital_id) REFERENCES hospitals(id)
        ON DELETE CASCADE,

    INDEX idx_apt_patient (patient_id),
    INDEX idx_apt_doctor (doctor_id),
    INDEX idx_apt_hospital (hospital_id),
    INDEX idx_apt_date (appointment_date),
    INDEX idx_apt_status (status),

    CONSTRAINT uq_apt_slot
        UNIQUE (doctor_id, appointment_date, appointment_time)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- MEDICINES (inventory)
-- ==========================
CREATE TABLE medicines (
    id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    generic_name VARCHAR(150),
    quantity INT NOT NULL,
    unit VARCHAR(20) DEFAULT 'tablet',
    expiry_date DATE NOT NULL,
    cost DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_med_hospital
        FOREIGN KEY (hospital_id)
        REFERENCES hospitals(id)
        ON DELETE CASCADE,

    INDEX idx_med_hospital (hospital_id),
    INDEX idx_med_name (name),
    INDEX idx_med_expiry (expiry_date)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- PRESCRIPTIONS
-- ==========================
CREATE TABLE prescriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    medicine_name VARCHAR(150) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    duration VARCHAR(100),
    notes TEXT,
    prescribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_presc_patient
        FOREIGN KEY (patient_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_presc_doctor
        FOREIGN KEY (doctor_id)
        REFERENCES doctors(id)
        ON DELETE CASCADE,

    INDEX idx_presc_patient (patient_id),
    INDEX idx_presc_doctor (doctor_id),
    INDEX idx_presc_date (prescribed_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- AWARENESS CONTENT
-- ==========================
CREATE TABLE awareness_content (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    content LONGTEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    language VARCHAR(10) DEFAULT 'EN', -- 'EN' or 'TA'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_aware_category (category),
    INDEX idx_aware_language (language)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ==========================
-- HEALTH SCHEMES
-- ==========================
CREATE TABLE health_schemes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL,
    description LONGTEXT NOT NULL,
    eligibility TEXT,
    benefits TEXT,
    contact_info VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Demo patient user (password: demo123 -> bcrypt hash pre-computed)
INSERT INTO users (name, phone, email, password_hash, role, age, gender)
VALUES
('Demo Patient', '9876543210', 'patient@demo.com',
 '$2b$12$L9SEr0.3U0jV6mT0.5.jJOKVQZzOqGGAjAVL2MxGm4p0KX8uj6eSC', -- demo123
 'patient', 30, 'M');

-- Hospitals (Tamil Nadu)
INSERT INTO hospitals
(name, district, taluk, village, latitude, longitude, phone, email, password_hash,
 total_beds, registration_status)
VALUES
('District Hospital Tiruppur', 'Tiruppur', 'Tiruppur', 'Tiruppur City',
 11.108500, 77.341100, '9876543211', 'dh.tiruppur@tn.gov.in',
 '$2b$12$1234567890123456789012345678901234567890', 200, 'approved'),
('PHC Udumalaippettai', 'Tiruppur', 'Udumalaippettai', 'Udumalaippettai',
 10.790500, 77.246700, '9876543212', 'phc.udumalaippettai@tn.gov.in',
 '$2b$12$1234567890123456789012345678901234567890', 50, 'approved'),
('GH Salem', 'Salem', 'Salem', 'Salem City',
 11.664300, 78.146000, '9876543213', 'gh.salem@tn.gov.in',
 '$2b$12$1234567890123456789012345678901234567890', 150, 'approved'),
('CHC Coimbatore', 'Coimbatore', 'Coimbatore', 'Coimbatore City',
 11.008100, 76.995600, '9876543214', 'chc.coimbatore@tn.gov.in',
 '$2b$12$1234567890123456789012345678901234567890', 100, 'approved'),
('Primary Health Centre Madurai', 'Madurai', 'Madurai', 'Madurai City',
 9.925200, 78.119800, '9876543215', 'phc.madurai@tn.gov.in',
 '$2b$12$1234567890123456789012345678901234567890', 75, 'approved');

-- Doctors
INSERT INTO doctors
(name, specialization, hospital_id, phone, availability_status, consultation_fee)
VALUES
('Dr. Rajesh Kumar', 'General Medicine', 1, '9999111111', 'available', 250),
('Dr. Priya Sharma', 'Pediatrics', 1, '9999111112', 'available', 300),
('Dr. Amit Patel', 'Obstetrics', 1, '9999111113', 'available', 350),
('Dr. Neha Singh', 'General Medicine', 2, '9999111114', 'available', 200),
('Dr. Vinod Kumar', 'Orthopedics', 2, '9999111115', 'available', 250),
('Dr. Anjali Verma', 'Cardiology', 3, '9999111116', 'available', 400),
('Dr. Suresh Kumar', 'General Medicine', 3, '9999111117', 'available', 250),
('Dr. Lakshmi Devi', 'Gynecology', 4, '9999111118', 'available', 300),
('Dr. Ramesh Rao', 'Pediatrics', 4, '9999111119', 'available', 280),
('Dr. Meena Krishnan', 'General Medicine', 5, '9999111120', 'available', 220);

-- Medicines
INSERT INTO medicines
(hospital_id, name, generic_name, quantity, unit, expiry_date, cost)
VALUES
(1, 'Paracetamol 500mg', 'Paracetamol', 500, 'tablet', '2026-12-31', 5),
(1, 'Amoxicillin 500mg', 'Amoxicillin', 300, 'capsule', '2026-06-30', 20),
(1, 'Ibuprofen 400mg', 'Ibuprofen', 400, 'tablet', '2026-10-31', 8),
(2, 'Metformin 500mg', 'Metformin', 200, 'tablet', '2026-03-31', 15),
(2, 'Aspirin 100mg', 'Aspirin', 350, 'tablet', '2026-09-30', 3),
(3, 'Cough Syrup', 'Dextromethorphan', 50, 'ml', '2026-12-31', 25),
(3, 'Antibiotic Ointment', 'Neomycin', 100, 'tube', '2026-05-31', 35),
(4, 'Antacid Tablet', 'Magnesium Hydroxide', 250, 'tablet', '2026-11-30', 2),
(4, 'Multivitamin Tablet', 'Multivitamins', 300, 'tablet', '2027-08-31', 50),
(5, 'Antihistamine Tablet', 'Cetirizine', 200, 'tablet', '2026-10-31', 10);

-- Awareness content (EN + TA)
INSERT INTO awareness_content (title, content, category, language) VALUES
('Child Vaccination Schedule',
 'All children should receive routine vaccinations at government health centers. Vaccinations are free and protect against serious diseases.',
 'Vaccination', 'EN'),
('Maternal and Child Health Care',
 'Free antenatal, delivery, and postnatal care are available at government hospitals. Regular checkups are essential for mother and baby.',
 'Maternal Health', 'EN'),
('Nutrition and Balanced Diet',
 'A balanced diet with grains, vegetables, fruits, and proteins helps prevent disease and improves immunity.',
 'Nutrition', 'EN'),
('Hygiene and Sanitation',
 'Wash hands with soap, drink safe water, and maintain cleanliness to prevent infections.',
 'Hygiene', 'EN'),
('பிள்ளைகளுக்கான தடுப்பூசி திட்டம்',
 'அனைத்து சிறுவர்களும் அரசு சுகாதார நிலையங்களில் வழக்கமான தடுப்பூசிகளைப் பெற வேண்டும். இது முற்றிலும் இலவசம்.',
 'Vaccination', 'TA'),
('தாய் மற்றும் சிசு சுகாதாரம்',
 'கர்ப்ப காலத்தில் மற்றும் பிரசவத்திற்குப் பிறகு அரசு மருத்துவமனைகளில் இலவச பரிசோதனைகள் கிடைக்கின்றன.',
 'Maternal Health', 'TA');

-- Health schemes
INSERT INTO health_schemes
(name, description, eligibility, benefits, contact_info)
VALUES
('Aayushman Bharat - PMJAY',
 'National Health Protection Scheme providing health insurance coverage to eligible families.',
 'Below Poverty Line (BPL) families',
 'Coverage up to 5 lakh rupees per family per year.',
 'Toll-free: 14555'),
('CM Health Insurance Scheme (TN)',
 'Tamil Nadu state health insurance scheme.',
 'Eligible Tamil Nadu residents as per scheme rules.',
 'Cashless treatment for selected procedures in empanelled hospitals.',
 'District Health Office'),
('Maternal Benefit Scheme',
 'Cash assistance for pregnant and lactating mothers.',
 'Pregnant women registered in government facilities.',
 'Multiple instalments linked to antenatal visits and immunization.',
 'Anganwadi / PHC'),
('Child Health Scheme',
 'Free health services for children under 5 years.',
 'All children under 5 years in Tamil Nadu.',
 'Free immunization, growth monitoring, and nutrition support.',
 'Nearest PHC / Anganwadi'),
('Senior Citizen Health Programme',
 'Special health services for senior citizens.',
 'Citizens above 60 years.',
 'Free check-ups and subsidized medicines at government hospitals.',
 'District Hospital Helpdesk');

-- Quick verification
SELECT 'Database and tables created successfully!' AS status;
SELECT COUNT(*) AS total_hospitals FROM hospitals;
SELECT COUNT(*) AS total_doctors FROM doctors;
SELECT COUNT(*) AS total_medicines FROM medicines;
SELECT COUNT(*) AS total_awareness FROM awareness_content;
SELECT COUNT(*) AS total_schemes FROM health_schemes;
