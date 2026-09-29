from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from app.llm.groq_client import get_llm
from app.graph.state import AppointmentState
from app.tools.appointment_reader import get_patient_appointments
from app.tools.appointment_writer import cancel_appointment

CANCEL_TOOLS = [get_patient_appointments, cancel_appointment]

CANCEL_SYSTEM = """You are the Cancellation Agent. Your ONLY job is to cancel existing appointments.

## Workflow
1. Collect patient_id and date_slot (M/D/YYYY H:MM). If unknown, call get_patient_appointments to list bookings.
2. Confirm with the user before proceeding ("yes/no").
3. On confirmation, call cancel_appointment.
4. Inform the user of the outcome.

## Rules
- Always confirm before cancelling, unless the user already said yes in their message.
"""

CANCEL_PROMPT = ChatPromptTemplate.from_messages([("system", CANCEL_SYSTEM), ("placeholder", "{messages}")])
cancellation_tool_node = ToolNode(tools=CANCEL_TOOLS)


def cancellation_agent_node(state: AppointmentState) -> dict:
    llm = get_llm().bind_tools(CANCEL_TOOLS)
    chain = CANCEL_PROMPT | llm
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "final_response": response.content if not response.tool_calls else None}