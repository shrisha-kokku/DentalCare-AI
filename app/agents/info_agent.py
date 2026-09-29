from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import ToolNode
from app.llm.groq_client import get_llm
from app.graph.state import AppointmentState
from app.tools.appointment_reader import get_available_slots, get_patient_appointments, check_slot_availability, list_doctors_by_specialization

INFO_TOOLS = [get_available_slots, get_patient_appointments, check_slot_availability, list_doctors_by_specialization]

INFO_SYSTEM = """You are the Information Agent for a dental appointment system.
Answer queries about doctor availability, schedules, and appointment status.

## Guidelines
1. Use tools to fetch real data. Never invent slot times or doctor names.
2. If parameters are missing, ask a focused clarifying question.
3. Present results in a clear, friendly, numbered list.
4. Valid specializations: general_dentist, oral_surgeon, orthodontist, cosmetic_dentist, prosthodontist, pediatric_dentist, emergency_dentist.

## Date Format
M/D/YYYY H:MM (e.g., 5/10/2026 9:00)
"""

INFO_PROMPT = ChatPromptTemplate.from_messages([("system", INFO_SYSTEM), ("placeholder", "{messages}")])
info_tool_node = ToolNode(tools=INFO_TOOLS)


def info_agent_node(state: AppointmentState) -> dict:
    llm = get_llm().bind_tools(INFO_TOOLS)
    chain = INFO_PROMPT | llm
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [response], "final_response": response.content if not response.tool_calls else None}