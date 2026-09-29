from typing import TypedDict, Annotated, Literal, Optional, List
from langchain_core.messages import BaseMessage
import operator

IntentType = Literal["get_info", "book", "cancel", "reschedule", "unknown", "end"]
RouteTarget = Literal["info_agent", "booking_agent", "cancellation_agent", "rescheduling_agent", "end"]


class AppointmentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    intent: Optional[IntentType]
    next_agent: Optional[RouteTarget]
    final_response: Optional[str]