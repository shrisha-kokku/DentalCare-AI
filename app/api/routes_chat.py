from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage
from app.models.schemas import ChatRequest, ChatResponse, ChatMessage
from app.graph.build_graph import build_graph

router = APIRouter()
graph = build_graph()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    history_messages = [HumanMessage(m.content) if m.role == "user" else AIMessage(m.content) for m in request.history]
    result = graph.invoke({"messages": history_messages + [HumanMessage(request.message)]}, config={"recursion_limit": 20})
    reply = result["messages"][-1].content
    updated_history = request.history + [ChatMessage(role="user", content=request.message), ChatMessage(role="assistant", content=reply)]
    return ChatResponse(reply=reply, history=updated_history)