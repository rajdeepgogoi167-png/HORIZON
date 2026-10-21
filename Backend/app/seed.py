from sqlalchemy.orm import Session

from app.jsonutil import dumps
from app.models import Doctor, Hospital

TAGS = {
    "General Medicine": ["Fever", "Cough", "Cold", "Fatigue", "Headache"],
    "Cardiology": ["Chest pain", "Breathlessness", "Palpitations", "Dizziness"],
    "Dermatology": ["Rashes", "Acne", "Itching", "Hair loss"],
    "Orthopedics": ["Joint pain", "Back pain", "Fracture", "Stiffness"],
    "Pediatrics": ["Child fever", "Vomiting", "Diarrhea", "Rashes"],
    "Gastroenterology": ["Stomach pain", "Acidity", "Constipation"],
    "Urology": ["Frequent urine", "Kidney pain", "Blood in urine"],
    "Neurology": ["Headache", "Numbness", "Seizures"],
    "Dentistry": ["Toothache", "Gum bleeding", "Cavity"],
}

DOCTORS = [
    {
        "name": "Dr. Meera Nair",
        "specialty": "General Medicine",
        "qualification": "MBBS, MD (Medicine)",
        "institution": "Sample Medical College",
        "experience_years": 12,
        "fee": 300,
        "rating": 4.8,
        "review_count": 212,
        "languages": ["English", "हिन्दी", "অসমীয়া"],
        "slots": ["10:00", "11:30", "16:00"],
        "bio": "Family physician focused on fevers, infections and long-term care.",
        "modes": ["Video", "Audio", "In person"],
        "city": "Silchar",
        "clinic_count": 1,
    },
    {
        "name": "Dr. Arjun Rao",
        "specialty": "Cardiology",
        "qualification": "MBBS, DM (Cardiology)",
        "institution": "Sample Heart Institute",
        "experience_years": 18,
        "fee": 900,
        "rating": 4.9,
        "review_count": 340,
        "languages": ["English", "हिन्दी"],
        "slots": ["09:00", "12:00", "17:30"],
        "bio": "Cardiologist for chest pain, blood pressure and heart-rhythm concerns.",
        "modes": ["Video", "In person"],
        "city": "Guwahati",
        "clinic_count": 2,
    },
    {
        "name": "Dr. Sana Iqbal",
        "specialty": "Dermatology",
        "qualification": "MBBS, MD (Dermatology)",
        "institution": "Sample Skin Clinic",
        "experience_years": 9,
        "fee": 500,
        "rating": 4.7,
        "review_count": 158,
        "languages": ["English", "हिन्दी"],
        "slots": ["11:00", "15:00"],
        "bio": "Treats rashes, acne and hair or nail problems.",
        "modes": ["Video", "Audio"],
        "city": "Guwahati",
        "clinic_count": 3,
    },
    {
        "name": "Dr. Bikash Das",
        "specialty": "Orthopedics",
        "qualification": "MBBS, MS (Orthopedics)",
        "institution": "Sample Bone & Joint Centre",
        "experience_years": 14,
        "fee": 700,
        "rating": 4.6,
        "review_count": 121,
        "languages": ["অসমীয়া", "English"],
        "slots": ["10:30", "14:00"],
        "bio": "Joint, back and sports injuries.",
        "modes": ["Video", "In person"],
        "city": "Silchar",
        "clinic_count": 4,
    },
    {
        "name": "Dr. Kavya Menon",
        "specialty": "Pediatrics",
        "qualification": "MBBS, DCH",
        "institution": "Sample Children’s Hospital",
        "experience_years": 8,
        "fee": 400,
        "rating": 4.9,
        "review_count": 190,
        "languages": ["English", "हिन्दी"],
        "slots": ["09:30", "13:00", "18:00"],
        "bio": "Child health, vaccines and fevers in children.",
        "modes": ["Video", "Audio", "In person"],
        "city": "Imphal",
        "clinic_count": 1,
    },
    {
        "name": "Dr. Rohan Sen",
        "specialty": "Gastroenterology",
        "qualification": "MBBS, DM (Gastro)",
        "institution": "Sample Digestive Care",
        "experience_years": 11,
        "fee": 650,
        "rating": 4.5,
        "review_count": 97,
        "languages": ["English", "অসমীয়া"],
        "slots": ["12:30", "16:30"],
        "bio": "Acidity, stomach pain and liver concerns.",
        "modes": ["Video", "In person"],
        "city": "Shillong",
        "clinic_count": 2,
    },
    {
        "name": "Dr. Pranab Choudhury",
        "specialty": "Urology",
        "qualification": "MBBS, MS, MCh (Urology)",
        "institution": "Sample Kidney Institute",
        "experience_years": 13,
        "fee": 800,
        "rating": 4.6,
        "review_count": 88,
        "languages": ["English", "অসমীয়া"],
        "slots": ["10:00", "15:30"],
        "bio": "Treats kidney stones, urinary infections and prostate concerns.",
        "modes": ["Video", "In person"],
        "city": "Guwahati",
        "clinic_count": 3,
    },
    {
        "name": "Dr. Nandini Hazarika",
        "specialty": "Neurology",
        "qualification": "MBBS, DM (Neurology)",
        "institution": "Sample Brain & Spine Centre",
        "experience_years": 15,
        "fee": 1000,
        "rating": 4.8,
        "review_count": 132,
        "languages": ["English", "অসমীয়া", "हिन्दी"],
        "slots": ["11:00", "16:00"],
        "bio": "Headache, seizures, numbness and stroke follow-up.",
        "modes": ["Video", "In person"],
        "city": "Agartala",
        "clinic_count": 4,
    },
    {
        "name": "Dr. Imran Ali",
        "specialty": "Dentistry",
        "qualification": "BDS, MDS",
        "institution": "Sample Dental Clinic",
        "experience_years": 7,
        "fee": 350,
        "rating": 4.7,
        "review_count": 164,
        "languages": ["English", "हिन्दी"],
        "slots": ["10:00", "12:00", "17:00"],
        "bio": "Toothache, gum care, fillings and root canals.",
        "modes": ["In person", "Video"],
        "city": "Imphal",
        "clinic_count": 1,
    },
]

HOSPITALS = [
    {"name": "Sample City Hospital", "city": "Guwahati", "specialties": ["Cardiology", "Orthopedics", "Emergency care"]},
    {"name": "Barak Valley Medical Centre", "city": "Silchar", "specialties": ["General Medicine", "Pediatrics", "Surgery"]},
    {"name": "Loktak Care Hospital", "city": "Imphal", "specialties": ["Gastroenterology", "Neurology"]},
    {"name": "Hills Community Hospital", "city": "Shillong", "specialties": ["Dermatology", "Dentistry"]},
    {"name": "Tripura Heart & Joint Centre", "city": "Agartala", "specialties": ["Cardiology", "Orthopedics"]},
]

LABS = [
    {"name": "Complete blood count", "price": 350},
    {"name": "Blood sugar (fasting)", "price": 120},
    {"name": "Lipid profile", "price": 600},
    {"name": "Thyroid profile", "price": 450},
    {"name": "Dengue NS1 antigen", "price": 700},
]

ARTICLES = [
    {
        "title": "Dengue: when to get tested",
        "body": "Fever with severe body ache, a rash, or bleeding from the gums needs a test and a doctor’s review. Drink plenty of fluids and don’t take aspirin or ibuprofen unless a doctor says so.",
    },
    {
        "title": "Fever in children: what to watch",
        "body": "Get care quickly for fever in a baby under 3 months, a fit, trouble breathing, or a child who is very drowsy or won’t drink.",
    },
    {
        "title": "Diabetes and your feet",
        "body": "Check your feet every day. See a doctor for sores that don’t heal, numbness, or colour changes.",
    },
    {
        "title": "Giving blood: what to expect",
        "body": "Eat and drink well beforehand. A short health check at the blood bank decides if you can donate that day, and rest afterwards helps.",
    },
]

CITIES = ["Guwahati", "Silchar", "Imphal", "Shillong", "Agartala"]


def seed_if_empty(db: Session) -> None:
    if db.query(Doctor).count() == 0:
        for row in DOCTORS:
            db.add(
                Doctor(
                    name=row["name"],
                    specialty=row["specialty"],
                    qualification=row["qualification"],
                    institution=row["institution"],
                    experience_years=row["experience_years"],
                    fee=row["fee"],
                    rating=row["rating"],
                    review_count=row["review_count"],
                    city=row["city"],
                    languages=dumps(row["languages"]),
                    slots=dumps(row["slots"]),
                    modes=dumps(row["modes"]),
                    bio=row["bio"],
                    keywords=dumps(TAGS.get(row["specialty"], [])),
                    clinic_count=row["clinic_count"],
                    approved=1,
                    available=1,
                )
            )
    if db.query(Hospital).count() == 0:
        for row in HOSPITALS:
            db.add(
                Hospital(
                    name=row["name"],
                    city=row["city"],
                    specialties=dumps(row["specialties"]),
                )
            )
    db.commit()
