from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from app.llm.groq_client import get_llm
from app.graph.state import AppointmentState, RouteTarget


class SupervisorDecision(BaseModel):
    intent: str = Field(description="One of: get_info, book, cancel, reschedule, unknown, end.")
    next_agent: RouteTarget = Field(description="The agent to route to.")
    reasoning: str = Field(description="Brief explanation of the routing decision.")


SUPERVISOR_SYSTEM = """You are the supervisor and router for a dental appointment management system.
Analyze the user's latest message, classify intent, and route to the correct specialist agent.

## Routing Rules
- get_info   → info_agent         : questions about slots, doctors, specializations, schedules.
- book       → booking_agent      : wants a NEW appointment.
- cancel     → cancellation_agent : wants to cancel an existing appointment.
- reschedule → rescheduling_agent : wants to move an existing appointment.
- end        → end                : says goodbye/thanks/done, or their question is already answered.
- unknown    → info_agent         : ambiguous intent, default to info_agent.

Do NOT answer the user directly. Only classify and route.
"""

SUPERVISOR_PROMPT = ChatPromptTemplate.from_messages([("system", SUPERVISOR_SYSTEM), ("placeholder", "{messages}")])


def supervisor_node(state: AppointmentState) -> dict:
    llm = get_llm().with_structured_output(SupervisorDecision)
    chain = SUPERVISOR_PROMPT | llm
    decision: SupervisorDecision = chain.invoke({"messages": state["messages"]})
    return {"intent": decision.intent, "next_agent": decision.next_agent}