import pandas as pd
from app.db.session import SessionLocal, init_db
from app.db.models import Doctor, Appointment
from app.core.config import CSV_PATH


def seed():
    init_db()
    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip()
    df["doctor_name"] = df["doctor_name"].str.lower().str.strip()
    df["specialization"] = df["specialization"].str.lower().str.strip()
    df["is_available"] = df["is_available"].astype(str).str.upper() == "TRUE"
    df["date_slot"] = pd.to_datetime(df["date_slot"], format="mixed", dayfirst=False)
    df["patient_to_attend"] = df["patient_to_attend"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    session = SessionLocal()
    doctor_ids = {}
    for name, spec in df[["doctor_name", "specialization"]].drop_duplicates().values:
        doctor = Doctor(name=name, specialization=spec)
        session.add(doctor)
        session.flush()
        doctor_ids[name] = doctor.id

    for _, row in df.iterrows():
        patient_id = row["patient_to_attend"] if row["patient_to_attend"] not in ("nan", "") else None
        session.add(Appointment(
            doctor_id=doctor_ids[row["doctor_name"]],
            date_slot=row["date_slot"],
            is_available=row["is_available"],
            patient_id=patient_id,
        ))
    session.commit()
    session.close()
    print(f"Seeded {len(doctor_ids)} doctors and {len(df)} appointment slots.")


if __name__ == "__main__":
    seed()