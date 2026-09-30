from datetime import datetime
from langchain_core.tools import tool
from app.db.session import SessionLocal
from app.db.models import Doctor, Appointment
from app.calendar.google_calendar_client import create_calendar_event, delete_calendar_event


@tool
def book_appointment(patient_id: str, doctor_name: str, date_slot: str) -> dict:
    """Book an appointment: mark slot unavailable, assign patient_id, and add a calendar reminder."""
    session = SessionLocal()
    try:
        target_dt = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    except ValueError:
        session.close()
        return {"success": False, "message": f"Invalid date_slot format: {date_slot}"}

    row = session.query(Appointment).join(Doctor).filter(
        Doctor.name == doctor_name.lower().strip(), Appointment.date_slot == target_dt
    ).first()
    if not row:
        session.close()
        return {"success": False, "message": "Slot not found for this doctor."}
    if not row.is_available:
        session.close()
        return {"success": False, "message": "Slot is already booked."}

    event_id = create_calendar_event(date_slot, doctor_name, patient_id)

    row.is_available = False
    row.patient_id = str(patient_id).strip()
    row.calendar_event_id = event_id
    session.commit()
    session.close()

    note = "" if event_id else " (calendar reminder could not be added)"
    return {"success": True, "message": f"Appointment booked for patient {patient_id} with {doctor_name} at {date_slot}.{note}"}


@tool
def cancel_appointment(patient_id: str, date_slot: str) -> dict:
    """Cancel an appointment: mark slot available, clear patient_id, and remove its calendar reminder."""
    session = SessionLocal()
    try:
        target_dt = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    except ValueError:
        session.close()
        return {"success": False, "message": f"Invalid date_slot format: {date_slot}"}

    pid = str(patient_id).strip()
    row = session.query(Appointment).filter(
        Appointment.patient_id == pid, Appointment.date_slot == target_dt, Appointment.is_available == False
    ).first()
    if not row:
        session.close()
        return {"success": False, "message": f"No booked appointment found for patient {pid} at {date_slot}."}

    if row.calendar_event_id:
        delete_calendar_event(row.calendar_event_id)

    row.is_available = True
    row.patient_id = None
    row.calendar_event_id = None
    session.commit()
    session.close()
    return {"success": True, "message": f"Appointment at {date_slot} for patient {pid} has been cancelled and removed from your calendar."}


@tool
def reschedule_appointment(patient_id: str, current_date_slot: str, new_date_slot: str, doctor_name: str) -> dict:
    """Reschedule: cancel the old slot's calendar event, book the new one, and create a new calendar event."""
    session = SessionLocal()
    try:
        current_dt = datetime.strptime(current_date_slot, "%m/%d/%Y %H:%M")
        new_dt = datetime.strptime(new_date_slot, "%m/%d/%Y %H:%M")
    except ValueError as exc:
        session.close()
        return {"success": False, "message": f"Date parse error: {exc}"}

    doc = doctor_name.lower().strip()
    pid = str(patient_id).strip()

    old_row = session.query(Appointment).filter(
        Appointment.patient_id == pid, Appointment.date_slot == current_dt, Appointment.is_available == False
    ).first()
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

    if old_row.calendar_event_id:
        delete_calendar_event(old_row.calendar_event_id)
    new_event_id = create_calendar_event(new_date_slot, doctor_name, pid)

    old_row.is_available = True
    old_row.patient_id = None
    old_row.calendar_event_id = None
    new_row.is_available = False
    new_row.patient_id = pid
    new_row.calendar_event_id = new_event_id
    session.commit()
    session.close()
    return {
        "success": True,
        "message": f"Appointment for patient {pid} rescheduled from {current_date_slot} to {new_date_slot} with {doctor_name}, and your calendar reminder was updated.",
    }