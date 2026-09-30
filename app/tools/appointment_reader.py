from datetime import datetime
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.db.models import Doctor, Appointment


@tool
def get_available_slots(specialization: str = "", doctor_name: str = "", date_filter: str = "") -> list:
    """Return available appointment slots, optionally filtered by specialization, doctor_name, or date_filter (M/D/YYYY)."""
    session = SessionLocal()
    query = session.query(Appointment, Doctor).join(Doctor).filter(Appointment.is_available == True)
    if specialization:
        query = query.filter(Doctor.specialization == specialization.lower().strip())
    if doctor_name:
        query = query.filter(Doctor.name == doctor_name.lower().strip())
    if date_filter:
        try:
            day = datetime.strptime(date_filter, "%m/%d/%Y")
            query = query.filter(
                Appointment.date_slot >= day,
                Appointment.date_slot < day.replace(hour=23, minute=59),
            )
        except ValueError:
            pass
    rows = query.limit(20).all()
    session.close()
    return [{"date_slot": a.date_slot.strftime("%m/%d/%Y %H:%M"), "specialization": d.specialization, "doctor_name": d.name} for a, d in rows]


@tool
def get_patient_appointments(patient_id: str) -> list:
    """Return all booked appointments for a given patient ID."""
    session = SessionLocal()
    rows = session.query(Appointment, Doctor).join(Doctor).filter(Appointment.patient_id == str(patient_id).strip()).all()
    session.close()
    return [{"date_slot": a.date_slot.strftime("%m/%d/%Y %H:%M"), "specialization": d.specialization, "doctor_name": d.name, "patient_id": a.patient_id} for a, d in rows]


@tool
def check_slot_availability(doctor_name: str, date_slot: str) -> dict:
    """Check if a specific doctor slot (M/D/YYYY H:MM) is available."""
    session = SessionLocal()
    try:
        target_dt = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    except ValueError:
        session.close()
        return {"found": False, "is_available": False, "patient_id": ""}
    row = session.query(Appointment).join(Doctor).filter(Doctor.name == doctor_name.lower().strip(), Appointment.date_slot == target_dt).first()
    session.close()
    if not row:
        return {"found": False, "is_available": False, "patient_id": ""}
    return {"found": True, "is_available": row.is_available, "patient_id": row.patient_id or ""}


@tool
def list_doctors_by_specialization(specialization: str) -> list:
    """Return distinct doctor names for a given specialization."""
    session = SessionLocal()
    names = session.query(Doctor.name).filter(Doctor.specialization == specialization.lower().strip()).distinct().all()
    session.close()
    return sorted(n[0] for n in names)