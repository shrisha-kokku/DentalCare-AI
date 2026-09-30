# DentalCare AI

A conversational multi-agent system for managing dental appointments. A supervisor agent classifies each patient message and routes it to a specialist agent, which reads and writes appointment data in Postgres. Booking, cancelling and rescheduling also keep Google Calendar in sync, including a reminder for each appointment.

## Overview

A patient chats naturally with the assistant, for example:

- *"Show available slots for an orthodontist"*
- *"Book patient 1000082 with Emily Johnson on 5/10/2026 9:00"*
- *"Cancel my appointment on 5/10/2026 at 9:00"*
- *"Reschedule patient 1000082 from 5/10/2026 9:00 to 5/12/2026 10:00"*

A supervisor agent classifies the intent and routes to one of four specialist agents. Each specialist has its own tools and only does its one job. Booking, cancelling and rescheduling keep Google Calendar in sync: the write tools create or delete the calendar event as part of the same operation that updates the database.

## Features

- **Supervisor routing.** One LLM call classifies intent (`get_info`, `book`, `cancel`, `reschedule`, `unknown`, `end`) and picks the specialist agent, using structured output so the routing decision is a typed object, not free text. `unknown` (ambiguous) messages default to the Info Agent.
- **Specialist agents.** Info, Booking, Cancellation, and Rescheduling agents, each scoped to its own tools. This applies the principle of least privilege to agent design.
- **Postgres-backed data.** Doctors and appointments are stored in a relational database (via SQLAlchemy), not a flat file, so the data can be queried, joined, and scaled like a real system.
- **Google Calendar integration, fully synced.** Booking creates a real Calendar API v3 event with a reminder attached; cancelling deletes that event; rescheduling deletes the old event and creates a new one. The event ID is stored on the appointment row so the app always knows which calendar event belongs to which booking. No separate scheduler or cron job is needed, since Google Calendar handles the reminder natively.
- **Simple chat UI.** A Streamlit chat interface that talks to the FastAPI backend.

This project is intentionally kept lighter than a full agentic pipeline (no human-in-the-loop gate, no RAG, no guardrail layer). The routing and tool-use pattern is the focus here, while **ChangeRisk AI** demonstrates the deeper HITL/guardrail/MCP pattern.

## Architecture

```mermaid
flowchart TD
    A[Patient message + conversation history] --> B{Supervisor - Intent Classifier}
    B -->|get_info / unknown| C[Info Agent]
    B -->|book| D[Booking Agent]
    B -->|cancel| E[Cancellation Agent]
    B -->|reschedule| F[Rescheduling Agent]
    B -->|end| G[End]
    C <--> C1[(Postgres - read)]
    D <--> D1[(Postgres - read/write)]
    E <--> E1[(Postgres - read/write)]
    F <--> F1[(Postgres - read/write)]
    D --> D2[Google Calendar API]
    E --> D2
    F --> D2
    C --> G
    D --> G
    E --> G
    F --> G
```

Each specialist agent loops with its own tools (agent → tool → agent) until it has a final answer, then the turn ends. The write tools (`book_appointment`, `cancel_appointment`, `reschedule_appointment`) update Postgres and sync Google Calendar in the same call, so the LLM cannot update one without the other. The full conversation history is passed back and forth between the UI and the backend on every message, so no server-side session state is needed.

## Tech stack

| Area                 | Tool                                                             |
| -------------------- | ---------------------------------------------------------------- |
| Orchestration        | LangGraph, LangChain                                             |
| LLM                  | Groq via`langchain-groq`                                       |
| Database             | PostgreSQL via SQLAlchemy                                        |
| Calendar integration | Google Calendar API v3, OAuth 2.0 (`google-api-python-client`) |
| Backend              | FastAPI                                                          |
| UI                   | Streamlit                                                        |
| Packaging            | Docker                                                           |

## Project structure

```
DentalCare AI/
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes_chat.py            # POST /chat
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                 # environment configuration
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py                 # SQLAlchemy models: Doctor, Appointment
│   │   ├── session.py                # database engine/session
│   │   └── seed.py                   # one-time migration from the CSV into Postgres
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py                  # shared state passed between nodes
│   │   └── build_graph.py            # supervisor + agent graph wiring
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py             # intent classification and routing
│   │   ├── info_agent.py
│   │   ├── booking_agent.py
│   │   ├── cancellation_agent.py
│   │   └── rescheduling_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── appointment_reader.py     # read-only Postgres queries
│   │   └── appointment_writer.py     # Postgres writes + calendar sync (book/cancel/reschedule)
│   ├── calendar/
│   │   ├── __init__.py
│   │   └── google_calendar_client.py # Google Calendar API v3: create/delete events
│   ├── llm/
│   │   ├── __init__.py
│   │   └── groq_client.py
│   └── models/
│       ├── __init__.py
│       └── schemas.py                # API request/response models
├── scripts/
│   └── google_auth_setup.py          # one-time OAuth flow, prints a refresh token
├── ui/
│   └── streamlit_app.py
├── doctor_availability.csv           # source data for the one-time Postgres seed
├── client_secret.json                # Google OAuth client (do not commit)
├── .env                              # secrets and configuration (do not commit)
├── .gitignore
├── .dockerignore
├── requirements.txt
├── Dockerfile
└── README.md
```

> `client_secret.json` and `.env` contain secrets. Make sure both are listed in `.gitignore` and `.dockerignore`, and avoid keeping the project in a synced folder (such as OneDrive) unless those files are excluded.

## Getting started

### Prerequisites

- Python 3.10 or later
- A local or hosted PostgreSQL instance
- A free Groq API key (console.groq.com)
- A Google Cloud project with the Calendar API enabled, and an OAuth 2.0 Client ID (Web application type)

### Installation

```bash
git clone <repository-url>
cd "DentalCare AI"
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
python -m pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_key
MODEL_NAME=openai/gpt-oss-120b
TEMPERATURE=0

DATABASE_URL=postgresql://postgres:your_password@localhost:5432/dentalcare

GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
```

| Variable                                        | Description                                                |
| ----------------------------------------------- | ---------------------------------------------------------- |
| `GROQ_API_KEY`                                | Groq API key used for all LLM calls                        |
| `MODEL_NAME`                                  | Groq model name                                            |
| `TEMPERATURE`                                 | LLM temperature (defaults to`0`)                         |
| `DATABASE_URL`                                | PostgreSQL connection string                               |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | From your Google Cloud OAuth 2.0 Client ID                 |
| `GOOGLE_REFRESH_TOKEN`                        | Obtained once via`scripts/google_auth_setup.py`          |
| `API_URL`                                     | UI only. Backend URL, defaults to`http://localhost:8000` |

### One-time setup

Run all commands from the project root.

**1. Create the database:**

```sql
CREATE DATABASE dentalcare;
```

**2. Seed it from the CSV (run once, on an empty database):**

```bash
python -m app.db.seed
```

This creates the tables (including the `calendar_event_id` column that links an appointment to its calendar event) and loads the doctors and slots from `doctor_availability.csv`.

> The seed script is not safe to re-run. A second run fails on the unique doctor name constraint or creates duplicate slots. To reseed, drop the `appointments` and `doctors` tables first.

**3. (Only if your `appointments` table was created before the calendar feature) add the calendar column:**

```sql
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR;
```

If you seeded with the current code, the column already exists and you can skip this step.

**4. Authorize Google Calendar access:**

Download your OAuth client's JSON from Google Cloud Console as `client_secret.json` in the project root, add `http://localhost:8080/` to its authorized redirect URIs, then run:

```bash
python scripts/google_auth_setup.py
```

This opens a browser for a one-time consent screen, then prints a refresh token. Copy it into `.env` as `GOOGLE_REFRESH_TOKEN`.

> Google only returns a refresh token on the first consent. If the script prints `None`, remove this app's access at https://myaccount.google.com/permissions and run the script again.

### Run

Start the backend:

```bash
uvicorn app.main:app --reload
```

In a second terminal, start the UI:

```bash
streamlit run ui/streamlit_app.py
```

| Service           | URL                        |
| ----------------- | -------------------------- |
| API documentation | http://localhost:8000/docs |
| UI                | http://localhost:8501      |

## API reference

| Method | Endpoint    | Description                                                                                                |
| ------ | ----------- | ---------------------------------------------------------------------------------------------------------- |
| GET    | `/health` | Health check                                                                                               |
| POST   | `/chat`   | Sends a message and the prior conversation history; returns the assistant's reply and the updated history. |

Example request:

```json
{"message": "Book patient 1000082 with Emily Johnson on 5/10/2026 9:00", "history": []}
```

## Deployment

### Backend (Docker)

```bash
docker build -t dentalcare-ai .
docker run -p 8000:8000 --env-file .env dentalcare-ai
```

The image contains the backend only. Since a cloud host can't reach a database on your local machine, `DATABASE_URL` must point to a hosted Postgres instance (for example, Neon's free tier) when deployed. The connection string is the only thing that changes.

### UI

The Streamlit UI can be hosted separately, for example on Streamlit Community Cloud. Set the `API_URL` environment variable (or Streamlit secret) to the deployed backend URL.

## Limitations

- The chat is stateless on the backend. The full conversation history is passed with every request rather than stored server-side. This is fine for a single-user demo; a multi-user deployment would need per-session storage.
- The conversation history stores plain user and assistant text only, so tool calls and tool results from earlier turns are not remembered on later turns.
- The supervisor re-classifies every message, including short replies in the middle of a multi-step flow (such as "yes" or "10 AM"), so a reply can occasionally be routed to the wrong agent.
- There is no patient authentication. Anyone who knows a patient ID can view, cancel or reschedule that patient's appointments.
- The Google OAuth app is in testing mode, so the refresh token can expire after about 7 days. If calendar events stop being created, re-run `scripts/google_auth_setup.py` to get a new one.
- The Calendar integration is tied to a single Google account (whoever authorized it), not per-patient calendars.
- Calendar events use a hardcoded `Asia/Kolkata` timezone and a fixed 30-minute duration.
- If a calendar call fails, the booking still succeeds in the database and the reply notes that the reminder could not be added.
- Appointments that were already booked in the CSV have no calendar event, so cancelling or rescheduling them does not remove anything from the calendar.
- Calendar sync only happens through this app's own booking/cancel/reschedule tools. If an appointment row is changed directly in the database (bypassing the tools), its calendar event won't update to match.
- There is no human-in-the-loop approval or guardrail layer on bookings/cancellations. Actions execute directly once the agent has the required details, by design, to keep this project's scope distinct from ChangeRisk AI.
