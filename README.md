# 🚗 Premium Auto Dealership Voice Assistant

A sophisticated, multi-agent AI concierge system designed to handle vehicle inquiries and test drive bookings for a luxury auto dealership. This system integrates high-fidelity neural voice synthesis, structured data extraction, and real-time availability validation to provide a seamless customer experience.

## 🌟 Key Features

*   **Multi-Agent Orchestration**: Specialized agents (Conversational, Knowledge, and Booking) coordinated by a central Orchestrator.
*   **State-Aware Logic**: Prevents conversation loops by prioritizing active booking sessions over general inquiries.
*   **Real-Time Availability Check**: Validates test-drive slots immediately after the user selects a time, offering alternatives if the slot is taken.
*   **Premium Web UI**: A high-end Flask interface with a "Luxury Obsidian & Gold" theme.
*   **Voice Toggle**: A dedicated UI trigger to enable or disable the Assistant's voice output in real-time.
*   **Daily Date-Based Logging**: Automatically generates and stores conversation logs in `logs/YYYY-MM-DD.log`.
*   **Strict Data Validation**: 
    *   **Phone**: Validates for a strict 10-digit format.
    *   **Vehicle**: Automatically maps user slang to canonical names from the Knowledge Base.

---

## 🏗 Architecture & Flow

### 1. The Multi-Agent System
- **Orchestrator**: The "Nervous System." Manages state and routes logic based on intent and active sessions.
- **Conversational Agent**: The "Personality." Detects intent and extracts entities using OpenAI GPT-4o-mini.
- **Knowledge Agent**: The "Specialist." Queries the inventory in `knowledge_base.json`.
- **Booking Agent**: The "Coordinator." Handles date/time parsing and database transactions.

### 2. Information Flow
1.  **User Input**: Received via the Web UI (Text) or the Azure-powered Microphone (Voice).
2.  **Intent Detection**: The system identifies if the user wants to browse, book, or cancel.
3.  **Context Extraction**: Pydantic-based extraction pulls entities like names, dates, and 10-digit phone numbers.
4.  **Immediate Validation**: If a time is provided, the system checks the `bookings.db` immediately before asking for the customer's name.
5.  **Output**: Response text is displayed and high-fidelity audio is played via Azure Neural TTS.

---

## 📁 Project Structure

```text
VoiceAgent/
├── app.py                  # Flask Web Entry Point
├── config/
│   └── settings.py         # Configuration & Environment Management
├── data/
│   ├── knowledge_base.json  # Vehicle Inventory & Dealership Info
│   └── bookings.db          # SQLite Database (Auto-generated)
├── logs/
│   └── YYYY-MM-DD.log      # Daily Conversation Logs (Auto-generated)
├── src/
│   ├── agents/             # LLM logic (Conversational, Knowledge, Booking)
│   ├── services/           # Backend (Speech, Database, KB Services)
│   └── orchestrator/       # Nervous System (Agent Coordination)
├── web/
│   ├── static/             # CSS (Luxury Theme) & JS (UI Logic)
│   └── templates/          # HTML Templates (Index & Overlays)
├── .env                    # API Keys & Secrets (Must be created)
└── requirements.txt        # Project Dependencies



