## 🚗 Premium Auto Dealership Voice AI Agent
## Demo video
## Visit https://www.loom.com/share/1ee525c0de5e429db2cea86857898a55

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
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          LAYER 1: CLIENT INTERFACE                           │
│                 [Socket.IO Client] <──> [UI State Manager]                   |
│                                                                              │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │
                    [ TRANSPORT: Persistent TCP Tunnel ]
                    (Protocol: WebSocket via Socket.IO)
 <────────────────────────────────────────────────────────────────────────────>
                                       │
┌──────────────────────────────────────▼───────────────────────────────────────┐
│                       LAYER 2: ORCHESTRATION ENGINE                          │
│   ┌──────────────────────────────────────────────────────────────────────┐   │
│   │                    AGENT ORCHESTRATOR (The Controller)               │   │
│   └───────┬──────────────────────────┬──────────────────────────┬────────┘   │
│           │                          │                          │            │
│   ┌───────▼────────┐         ┌───────▼────────┐         ┌───────▼────────┐   │
│   │ CONVERSATIONAL │         │   KNOWLEDGE    │         │    BOOKING     │   │
│   │     AGENT      │         │     AGENT      │         │     AGENT      │   │
│   │ (NLP Pipeline) │         │ (Search Logic) │         │                │   │
│   └───────┬────────┘         └───────┬────────┘         └───────┬────────┘   │
└───────────┼──────────────────────────┼──────────────────────────┼────────────┘
            │                          │                          │
┌───────────▼───────────┐      ┌───────▼───────────┐      ┌───────▼───────────┐
│   LAYER 3: COGNITION  │      │   LAYER 4: DATA   │      │  LAYER 5: I/O     │
│ • GPT-4o-mini (LLM)   │      │ • Vehicle JSON KB │      │ • Azure STT/TTS   │
│ • Structured Output   │      │ • SQLite DB       │      │ • Date-Log File   │
└───────────────────────┘      └───────────────────┘      └───────────────────┘
```

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

## 🧪 Testing

### **Manual Testing Scenarios**

#### **Test 1: Quick Booking**
```
Input: "Book Toyota Camry for tomorrow at 11 AM"
Expected: Agent collects name → creates booking
```

#### **Test 2: Step-by-Step**
```
Input: "I want to book a test drive"
Expected: Agent asks for vehicle → date → time → name
```

#### **Test 3: Vehicle Inquiry**
```
Input: "What SUVs do you have?"
Expected: Lists 2 SUVs with details
```

#### **Test 4: Option Selection**
```
Input: "What sedans?" → "Option 1"
Expected: Selects Toyota Camry
```

#### **Test 5: Graceful Exit**
```
Input: "Bye"
Expected: Says goodbye and exits
```
---

## Security & Validation
Phone Validator: Rejects any input that isn't a 10-digit string.
Availability Guard: Ensures the user selects an open slot before the system commits to the booking.
Log Management: All interactions are timestamped and saved for quality assurance in the logs/ directory.
---