from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    specialization = Column(String, nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    date_slot = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    patient_id = Column(String, nullable=True)