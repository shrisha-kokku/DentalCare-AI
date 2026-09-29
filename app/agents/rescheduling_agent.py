from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from app.llm.groq_client import get_llm
from app.graph.state import AppointmentState
from app.tools.appointment_reader import get_patient_appointments, get_available_slots
from app.tools.appointment_writer import reschedule_appointment

RESCHEDULE_TOOLS = [get_patient_appointments, get_available_slots, reschedule_appointment]

RESCHEDULE_SYSTEM = """You are the Rescheduling Agent. Your ONLY job is to move an existing appointment.

## Workflow
1. Collect patient_id, current_date_slot, new_date_slot, doctor_name.
2. If unknown, call get_patient_appointments or get_available_slots to help the user choose.
3. Call reschedule_appointment.
4. Confirm: old slot → new slot, doctor name.

## Rules
- Same doctor by default unless the user asks for a different one.
"""

RESCHEDULE_PROMPT = ChatPromptTemplate.from_messages([("system", RESCHEDULE_SYSTEM), ("placeholder", "{messages}")])
rescheduling_tool_node = ToolNode(tools=RESCHEDULE_TOOLS)


def rescheduling_agent_node(state: AppointmentState) -> dict:
    llm = get_llm().bind_tools(RESCHEDULE_TOOLS)
    chain = RESCHEDULE_PROMPT | llm
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "final_response": response.content if not response.tool_calls else None}