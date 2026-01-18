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


## 🏗 System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE LAYER                     │
│  ┌──────────────────────┐    ┌──────────────────────┐       │
│  │   Voice Mode         │    │   Text Mode          │       │
│  │  (Azure STT + TTS)   │    │                      │       │
│  └──────────────────────┘    └──────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATOR LAYER                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Agent Orchestrator (Brain)                        │     │
│  │  • State Management                                │     │
│  │  • Intent Routing                                  │     │
│  │  • Context Preservation                            │     │
│  │  • Conversation Flow Control                       │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          ↓
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Conversational│  │  Knowledge   │  │   Booking    │
│    Agent     │  │    Agent     │  │    Agent     │
│              │  │              │  │              │
│ • Intent     │  │ • Search KB  │  │ • Parse Date │
│   Detection  │  │ • Filter     │  │ • Check Time │
│ • Entity     │  │   Vehicles   │  │ • Validate   │
│   Extraction │  │ • Recommend  │  │ • Book Slot  │
│ • Dialogue   │  │ • Compare    │  │ • Confirm    │
└──────────────┘  └──────────────┘  └──────────────┘
        ↓                 ↓                  ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   OpenAI     │  │ Knowledge    │  │   SQLite     │
│  GPT-4o-mini │  │  Base JSON   │  │   Database   │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 📊 Information Flow

### **1. User Input Processing**
```
User Speech → Azure STT → Text → Orchestrator
                                      ↓
                              Conversation History
                                      ↓
                            Conversational Agent
                                      ↓
                          Intent + Entities Detected
```

### **2. Multi-Agent Coordination**
```
Intent Detection → Route to Agent
                       ↓
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    Greeting       Inquiry         Booking
        ↓              ↓              ↓
  Welcome Msg    Knowledge      Booking Flow
                   Agent              ↓
                     ↓          Collect Details
              Vehicle Info           ↓
                     ↓          Validate Data
              Show Options           ↓
                                Check Availability
                                     ↓
                                Create Booking
```
---


## 🔄 Conversation Flow Examples

### **Example 1: Complete Booking**
```
🤖: Hello! Welcome to Premium Auto Dealership. How can I assist you today?

👤: I want to book a test drive for Toyota Camry tomorrow at 11 AM

🤖: [Detects: intent=booking, vehicle=Toyota Camry, date=tomorrow, time=11 AM]
    [Checks availability: AVAILABLE]
    May I have your name please?

👤: Tanmay Parashar

🤖: [Extracts: name=Tanmay Parashar]
    Test drive booking confirmed for Tanmay Parashar.
    Vehicle: 2024 Toyota Camry XLE
    Date: Saturday, January 19 at 11:00 AM
    Booking reference: 3
    Is there anything else I can help you with?

👤: No, thank you

🤖: You're welcome! Have a great day!

👤: Bye

🤖: Thank you for visiting Premium Auto Dealership! Goodbye!
    [System exits gracefully]
```

### **Example 2: Step-by-Step Booking**
```
🤖: Hello! Welcome to Premium Auto Dealership. How can I assist you?

👤: I want to book a test drive

🤖: Which vehicle would you like to test drive?

👤: What SUVs do you have?

🤖: [Switches to Knowledge Agent]
    We have 2 SUV options available:
    1. 2024 Ford Explorer Limited - $48,500
    2. 2024 Toyota Highlander XLE - $46,000
    Which one interests you most?

👤: The Ford Explorer

🤖: [Stores vehicle, returns to booking flow]
    Great choice! What day would you like to come in?

👤: 25th January

🤖: [Detects date, continues]
    What time works best for you?

👤: 3 PM

🤖: [Checks availability: TAKEN]
    I'm sorry, 3:00 PM is already booked.
    Available times that day: 9:00 AM, 10:00 AM, 2:00 PM, 4:00 PM
    Would any of these work?

👤: 2 PM is fine

🤖: [Stores time: 2 PM]
    Perfect! May I have your name please?

👤: Sarah Johnson

🤖: [Creates booking]
    Test drive booking confirmed for Sarah Johnson...
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

---

## 🛠 Installation & Setup


### **Prerequisites**

- Python 3.9 or higher
- Azure Account (free tier available)
- OpenAI API Key
- Microphone & speakers (for voice mode)

### **Step 1: Clone & Navigate**
```bash
git clone 
cd Auto-Dealership-Voice-Assistant
```

### **Step 2: Create Virtual Environment**
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

### **Step 3: Install Dependencies**
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


Use the Speaker Icon in the header to toggle the agent's voice.
Console Mode (Logic Testing)
```bash
python app.py
```
---

## Security & Validation
Phone Validator: Rejects any input that isn't a 10-digit string.
Availability Guard: Ensures the user selects an open slot before the system commits to the booking.
Log Management: All interactions are timestamped and saved for quality assurance in the logs/ directory.
---