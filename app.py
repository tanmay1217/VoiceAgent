import os
import logging
import sys
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from src.orchestrator.agent_orchestrator import AgentOrchestrator
from dotenv import load_dotenv

load_dotenv()

# 1. DAILY LOGGING SETUP
base_dir = os.path.abspath(os.path.dirname(__file__))
log_dir = os.path.join(base_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PremiumAutoSocket")

# 2. FLASK & SOCKET.IO SETUP
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'web', 'templates'), 
            static_folder=os.path.join(base_dir, 'web', 'static'))

# async_mode='eventlet' or 'gevent' is recommended for production-grade sockets
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=None)

orchestrator = None

def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        logger.info("Initializing Agent Orchestrator...")
        orchestrator = AgentOrchestrator()
    return orchestrator

@app.route('/')
def index():
    logger.info("New browser connection established.")
    return render_template('index.html')

# 3. WEBSOCKET EVENT HANDLERS
@socketio.on('connect')
def handle_connect():
    logger.info("Client connected via WebSocket.")

@socketio.on('request_greeting')
def handle_greeting():
    orch = get_orchestrator()
    greeting = orch._handle_greeting()
    audio = orch.speech_service.text_to_speech(greeting)
    emit('assistant_response', {
        "response": greeting,
        "audio": audio.hex() if audio else None
    })

@socketio.on('send_message')
def handle_message(data):
    user_text = data.get('message')
    logger.info(f"USER_SOCKET_TEXT: {user_text}")
    
    orch = get_orchestrator()
    response_text = orch.process_text_input(user_text)
    
    logger.info(f"AGENT_SOCKET_RESP: {response_text}")
    audio = orch.speech_service.text_to_speech(response_text)
    
    emit('assistant_response', {
        "response": response_text,
        "audio": audio.hex() if audio else None
    })

@socketio.on('start_voice')
def handle_voice():
    orch = get_orchestrator()
    logger.info("Microphone triggered via WebSocket")
    user_input = orch.speech_service.listen_and_transcribe()
    
    if not user_input:
        emit('assistant_response', {
            "response": "I didn't catch that. Could you please repeat?",
            "audio": None
        })
        return

    logger.info(f"USER_SOCKET_VOICE: {user_input}")
    response_text = orch.process_text_input(user_input)
    audio = orch.speech_service.text_to_speech(response_text)
    
    emit('assistant_response', {
        "user_said": user_input,
        "response": response_text,
        "audio": audio.hex() if audio else None
    })

if __name__ == '__main__':
    logger.info(f"--- Application started. Logging to {log_filename} ---")
    socketio.run(app, debug=True, port=5000, use_reloader=False)