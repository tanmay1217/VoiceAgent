import os
import logging
import sys
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from src.orchestrator.agent_orchestrator import AgentOrchestrator
from dotenv import load_dotenv

load_dotenv()

# 1. DATE-BASED LOGGING SETUP
base_dir = os.path.abspath(os.path.dirname(__file__))
log_dir = os.path.join(base_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Create log filename based on current date: logs/YYYY-MM-DD.log
log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PremiumAutoWeb")

# 2. FLASK SETUP
app = Flask(__name__, 
            template_folder=os.path.join(base_dir, 'web', 'templates'), 
            static_folder=os.path.join(base_dir, 'web', 'static'))

orchestrator = None

def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        orchestrator = AgentOrchestrator()
    return orchestrator

@app.route('/')
def index():
    logger.info("New web session started.")
    return render_template('index.html')

@app.route('/get_greeting', methods=['GET'])
def get_greeting():
    orch = get_orchestrator()
    greeting = orch._handle_greeting()
    audio = orch.speech_service.text_to_speech(greeting)
    return jsonify({"response": greeting, "audio": audio.hex() if audio else None})

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    logger.info(f"USER_TEXT: {user_input}")
    
    orch = get_orchestrator()
    response_text = orch.process_text_input(user_input)
    logger.info(f"AGENT_RESP: {response_text}")
    
    audio = orch.speech_service.text_to_speech(response_text)
    return jsonify({"response": response_text, "audio": audio.hex() if audio else None})

@app.route('/voice', methods=['POST'])
def voice():
    orch = get_orchestrator()
    user_input = orch.speech_service.listen_and_transcribe()
    
    if not user_input:
        return jsonify({"user_said": "...", "response": "I didn't catch that.", "audio": None})

    logger.info(f"USER_VOICE: {user_input}")
    response_text = orch.process_text_input(user_input)
    logger.info(f"AGENT_RESP: {response_text}")
    
    audio = orch.speech_service.text_to_speech(response_text)
    return jsonify({
        "user_said": user_input, 
        "response": response_text, 
        "audio": audio.hex() if audio else None
    })

if __name__ == '__main__':
    logger.info(f"Log file created at: {log_filename}")
    app.run(debug=True, port=5000, use_reloader=False)