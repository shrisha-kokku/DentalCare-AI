from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from app.llm.groq_client import get_llm
from app.graph.state import AppointmentState
from app.tools.appointment_reader import get_available_slots, check_slot_availability
from app.tools.appointment_writer import book_appointment

BOOKING_TOOLS = [get_available_slots, check_slot_availability, book_appointment]

BOOKING_SYSTEM = """You are the Booking Agent for a dental appointment management system.
Your ONLY job is to book NEW appointments.

## Workflow
1. Collect: patient_id, specialization, doctor_name, date_slot (M/D/YYYY H:MM).
2. Call check_slot_availability first. If taken, call get_available_slots for alternatives.
3. Once confirmed available, call book_appointment. This automatically adds a calendar reminder too.
4. Confirm the booking to the user with all details, including that a reminder was added.

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