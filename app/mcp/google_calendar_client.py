import asyncio
import requests
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN

CALENDAR_MCP_URL = "https://calendarmcp.googleapis.com/mcp/v1"


def _get_access_token() -> str:
    response = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type": "refresh_token",
    })
    response.raise_for_status()
    return response.json()["access_token"]


async def _call_calendar_tool(tool_name: str, arguments: dict) -> str:
    client = MultiServerMCPClient({
        "calendar": {
            "transport": "streamable_http",
            "url": CALENDAR_MCP_URL,
            "headers": {"Authorization": f"Bearer {_get_access_token()}"},
        }
    })
    tools = await client.get_tools()
    tool_obj = next((t for t in tools if t.name == tool_name), None)
    if tool_obj is None:
        raise RuntimeError(f"Calendar MCP server has no tool named {tool_name}")
    return str(await tool_obj.ainvoke(arguments))


@tool
def add_calendar_reminder(date_slot: str, doctor_name: str, patient_id: str) -> str:
    """Creates a Google Calendar event with a reminder for a booked dental appointment."""
    start = datetime.strptime(date_slot, "%m/%d/%Y %H:%M")
    end = start + timedelta(minutes=30)
    event = {
        "summary": f"Dental appointment with Dr. {doctor_name.title()}",
        "description": f"Patient ID: {patient_id}",
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
        "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 60}]},
    }
    try:
        result = asyncio.run(_call_calendar_tool("create_event", event))
        return f"Calendar reminder created: {result}"
    except Exception as exc:
        return f"Could not create calendar reminder: {exc}"