from datetime import datetime
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.db.models import Doctor, Appointment


@tool
def book_appointment(patient_id: str, doctor_name: str, date_slot: str) -> dict:
    """Book an appointment: mark slot unavailable and assign patient_id."""
    session = SessionLocal()
    try:
        target_dt = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    except ValueError:
        session.close()
        return {"success": False, "message": f"Invalid date_slot format: {date_slot}"}
    row = session.query(Appointment).join(Doctor).filter(Doctor.name == doctor_name.lower().strip(), Appointment.date_slot == target_dt).first()
    if not row:
        session.close()
        return {"success": False, "message": "Slot not found for this doctor."}
    if not row.is_available:
        session.close()
        return {"success": False, "message": "Slot is already booked."}
    row.is_available = False
    row.patient_id = str(patient_id).strip()
    session.commit()
    session.close()
    return {"success": True, "message": f"Appointment booked for patient {patient_id} with {doctor_name} at {date_slot}."}


@tool
def cancel_appointment(patient_id: str, date_slot: str) -> dict:
    """Cancel an appointment: mark slot available and clear patient_id."""
    session = SessionLocal()
    try:
        target_dt = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    except ValueError:
        session.close()
        return {"success": False, "message": f"Invalid date_slot format: {date_slot}"}
    pid = str(patient_id).strip()
    row = session.query(Appointment).filter(Appointment.patient_id == pid, Appointment.date_slot == target_dt, Appointment.is_available == False).first()
    if not row:
        session.close()
        return {"success": False, "message": f"No booked appointment found for patient {pid} at {date_slot}."}
    row.is_available = True
    row.patient_id = None
    session.commit()
    session.close()
    return {"success": True, "message": f"Appointment at {date_slot} for patient {pid} has been cancelled."}


@tool
def reschedule_appointment(patient_id: str, current_date_slot: str, new_date_slot: str, doctor_name: str) -> dict:
    """Reschedule: cancel the old slot and book the new one."""
    session = SessionLocal()
    try:
        current_dt = datetime.strptime(current_date_slot, "%m/%d/%Y %H:%M")
        new_dt = datetime.strptime(new_date_slot, "%m/%d/%Y %H:%M")
    except ValueError as exc:
        session.close()
        return {"success": False, "message": f"Date parse error: {exc}"}
    doc = doctor_name.lower().strip()
    pid = str(patient_id).strip()
    old_row = session.query(Appointment).filter(Appointment.patient_id == pid, Appointment.date_slot == current_dt, Appointment.is_available == False).first()
    if not old_row:
        session.close()
        return {"success": False, "message": f"No existing booking found for patient {pid} at {current_date_slot}."}
    new_row = session.query(Appointment).join(Doctor).filter(Doctor.name == doc, Appointment.date_slot == new_dt).first()
    if not new_row:
        session.close()
        return {"success": False, "message": f"Slot {new_date_slot} does not exist for {doctor_name}."}
    if not new_row.is_available:
        session.close()
        return {"success": False, "message": f"Slot {new_date_slot} is already taken."}
    old_row.is_available = True
    old_row.patient_id = None
    new_row.is_available = False
    new_row.patient_id = pid
    session.commit()
    session.close()
    return {"success": True, "message": f"Appointment for patient {pid} rescheduled from {current_date_slot} to {new_date_slot} with {doctor_name}."}