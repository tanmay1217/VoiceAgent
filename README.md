## 🚗 Premium Auto Dealership Voice AI Agent
**Real-Time WebSocket-Powered Luxury Concierge** 

A sophisticated, full-stack AI concierge system designed for luxury auto dealerships. This system utilizes a bi-directional WebSocket architecture to provide near-instantaneous voice and text interactions, high-fidelity neural synthesis, and robust multi-agent orchestration.

## 🌟 Key Features

*   **Real-Time WebSocket Engine**: Powered by Flask-SocketIO, the system maintains a persistent "pipe" between the user and the server, reducing latency and allowing the agent to "push" responses (text + audio) as soon as they are ready.
*   **Voice-First Concierge Hub**: A redesigned UI focusing on a prominent, glowing microphone interface with real-time Pulse Animations, signaling exactly when the system is listening.
*   **Multi-Agent Orchestration**: Specialized agents (Conversational, Knowledge, and Booking) coordinated by a central Orchestrator to handle complex, non-linear dialogues.
*   **State-Aware Logic**: Prevents conversation loops by prioritizing active booking sessions. If a user asks a side question during a booking, the agent answers and then gracefully returns to the exact step in the booking flow.
*   **Immediate Availability Guard**: Validates test-drive slots against the SQLite database the moment a time is mentioned, offering instant alternatives if a slot is taken.
*   **Daily Date-Based Logging**: Automatically generates and stores conversation logs in `logs/YYYY-MM-DD.log`.
*   **Strict Data Validation**: 
    *   **Phone**: Validates for a strict 10-digit format.
    *   **Vehicle**: Automatically maps user slang to canonical names from the Knowledge Base.

---

## 🏗 System Architecture
## 🏗 System Architecture

The project's architecture is described with a Mermaid diagram in the repository so you can view and export a visual diagram locally.

- Diagram source: [docs/architecture.mmd](docs/architecture.mmd)

Key components:
- **Browser UI** — Mic Hub, chat window, and Socket.IO client.
- **Flask + Flask-SocketIO** — Web server that accepts WebSocket events and routes them to the orchestrator.
- **Agent Orchestrator** — Central coordinator that maintains conversation state, booking details, and decides which agent handles the request.
- **ConversationalAgent** — Intent detection, response generation (OpenAI LLM).
- **KnowledgeAgent** — Reads `data/knowledge_base.json` for vehicle info and recommendations.
- **BookingAgent** — Validates and finalizes bookings via `BookingService` (SQLite database).
- **SpeechService** — Azure Cognitive Services for STT and TTS (microphone capture and audio bytes).
- **Logging & Storage** — Daily logs in `logs/` and persistent bookings in `data/bookings.db`.

This diagram reflects the runtime flows: client emits `start_voice` / `send_message`, the server routes to `AgentOrchestrator`, agents consult services (knowledge, booking, speech), responses are synthesized to audio and emitted back to the browser as `assistant_response` events (text + hex audio bytes).

---

## Diagram rendering (local)

Option 1 — Mermaid CLI (export PNG/SVG):

```bash
# install mmdc (requires Node.js)
npm install -g @mermaid-js/mermaid-cli

# render PNG
mmdc -i docs/architecture.mmd -o docs/architecture.png

# render SVG
mmdc -i docs/architecture.mmd -o docs/architecture.svg
```

Option 2 — VS Code

- Install the *Mermaid Preview* extension and open `docs/architecture.mmd` to preview and export.

If you'd like, I can export `docs/architecture.png` and add it to the repo for quick viewing — tell me if you want that.

---
## 📊 Information Flow
*   **Connection:** The browser establishes a WebSocket connection with the server via socket.connect().
*   **Trigger:** User clicks the Mic Hub; the client emits a start_voice event.
*   **Capture:** The server-side Azure SDK captures the microphone input, transcribes it, and passes it to the Orchestrator.
*   **Processing:** The Orchestrator routes the input to the correct agent. If a booking is active, it performs an Immediate Availability Check.
*   **Emission:** The server emits an assistant_response event containing:
*   **user_said:** The transcribed text.
*   **response:** The AI's reply.
*   **audio:"**: Hex-encoded audio bytes for instant playback.
*   **Playback**: The JS client decodes the hex, creates a WAV blob, and plays the "Ava" Neural voice.


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
```
---

## 🛠 Installation & Setup
**Step 1: Environment Setup**
```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows

# Install required packages
pip install flask-socketio eventlet langchain-openai azure-cognitiveservices-speech python-dotenv sqlalchemy python-dateutil
```

**Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate
```

### **Step 3: Install Dependencies**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### **Step 4: Install Dependencies**
```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastus
SPEECH_LANGUAGE=en-US

# Neural Voice Selection (Ava or Andrew recommended)
TTS_VOICE_NAME=en-US-AvaNeural
TTS_SPEAKING_RATE=1.0
```


---


### **🚀 Running the Application**

Web Mode (Recommended)
This launches the luxury browser interface:
```bash
python app.py
```
## Visit http://127.0.0.1:5000 in your browser.
## Click "ENTER SHOWROOM" to start.

---

## Security & Validation
Phone Validator: Rejects any input that isn't a 10-digit string.
Availability Guard: Ensures the user selects an open slot before the system commits to the booking.
Log Management: All interactions are timestamped and saved for quality assurance in the logs/ directory.
---