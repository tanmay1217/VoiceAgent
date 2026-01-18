import os
import sys
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from src.orchestrator.agent_orchestrator import AgentOrchestrator

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def print_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🚗  AUTO DEALERSHIP VOICE ASSISTANT  🚗                ║
    ║                                                           ║
    ║   Multi-Agent Test Drive Booking System                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_voice_mode(orchestrator: AgentOrchestrator):
    print("\n🎤 VOICE MODE ACTIVATED")
    print("=" * 60)
    print("The assistant will listen when you press Enter")
    print("It will automatically stop when you finish speaking (1 sec silence)")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("\nPress Enter to speak (or type 'quit' to exit): ").strip().lower()
        
        if user_input == 'quit':
            print("\n👋 Thank you for using our service. Goodbye!")
            break
        
        try:
            print("\n🎤 Listening... (speak now)")
            response = orchestrator.process_voice_input()
            print(f"\n🤖 Assistant: {response}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in voice mode: {str(e)}")
            print(f"\n❌ Error: {str(e)}\n")


def run_text_mode(orchestrator: AgentOrchestrator):
    print("\n💬 TEXT MODE ACTIVATED")
    print("=" * 60)
    print("Type your message and press Enter")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            print("\n👋 Thank you for using our service. Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            response = orchestrator.process_text_input(user_input)
            print(f"\n🤖 Assistant: {response}\n")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in text mode: {str(e)}")
            print(f"\n❌ Error: {str(e)}\n")


def main():
    print_banner()
    
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return
    
    if not os.getenv('AZURE_SPEECH_KEY'):
        print("❌ Error: AZURE_SPEECH_KEY not found in environment variables")
        return
    
    if not os.getenv('AZURE_SPEECH_REGION'):
        print("❌ Error: AZURE_SPEECH_REGION not found in environment variables")
        return
    
    try:
        print("\n🔧 Initializing agents...")
        orchestrator = AgentOrchestrator()
        print("✅ All agents initialized successfully!\n")
        
        print("Select mode:")
        print("1. Voice Mode (with speech recognition)")
        print("2. Text Mode (keyboard input only)")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == '1':
            run_voice_mode(orchestrator)
        elif choice == '2':
            run_text_mode(orchestrator)
        else:
            print("Invalid choice. Starting in text mode...")
            run_text_mode(orchestrator)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n❌ Fatal error: {str(e)}")
        print("Please check the logs for more details.")


if __name__ == "__main__":
    main()
