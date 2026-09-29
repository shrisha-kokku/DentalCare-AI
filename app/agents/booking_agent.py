from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from app.llm.groq_client import get_llm
from app.graph.state import AppointmentState
from app.tools.appointment_reader import get_available_slots, check_slot_availability
from app.tools.appointment_writer import book_appointment
from app.mcp.google_calendar_client import add_calendar_reminder

BOOKING_TOOLS = [get_available_slots, check_slot_availability, book_appointment, add_calendar_reminder]

BOOKING_SYSTEM = """You are the Booking Agent for a dental appointment management system.
Your ONLY job is to book NEW appointments.

## Workflow
1. Collect: patient_id, specialization, doctor_name, date_slot (M/D/YYYY H:MM).
2. Call check_slot_availability first. If taken, call get_available_slots for alternatives.
3. Once confirmed available, call book_appointment.
4. After a successful booking, call add_calendar_reminder with the same date_slot, doctor_name, patient_id.
5. Confirm the booking, including that a reminder was added. If the reminder step fails, still confirm the booking and mention the reminder could not be added.

## Rules
- NEVER book without verifying availability first.
- Ask for ONE missing piece of information at a time.
"""

BOOKING_PROMPT = ChatPromptTemplate.from_messages([("system", BOOKING_SYSTEM), ("placeholder", "{messages}")])
booking_tool_node = ToolNode(tools=BOOKING_TOOLS)


def booking_agent_node(state: AppointmentState) -> dict:
    llm = get_llm().bind_tools(BOOKING_TOOLS)
    chain = BOOKING_PROMPT | llm
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "final_response": response.content if not response.tool_calls else None}