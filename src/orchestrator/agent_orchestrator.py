from langchain_openai import ChatOpenAI
from src.agents.conversational_agent import ConversationalAgent
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.booking_agent import BookingAgent
from src.services.knowledge_service import KnowledgeService
from src.services.booking_service import BookingService
from src.services.speech_service import SpeechService
from config.settings import settings
from typing import Dict, List
import logging
import re

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE
        )
        
        self.knowledge_service = KnowledgeService()
        self.booking_service = BookingService()
        self.speech_service = SpeechService()
        
        self.conversational_agent = ConversationalAgent(self.llm)
        self.knowledge_agent = KnowledgeAgent(self.llm, self.knowledge_service)
        self.booking_agent = BookingAgent(self.llm, self.booking_service)
        
        self.conversation_history: List[Dict] = []
        self.current_intent = None
        self.booking_details = {}
        
        logger.info("Agent orchestrator initialized")
    
    def process_voice_input(self) -> str:
        logger.info("Listening for user input...")
        user_input = self.speech_service.listen_and_transcribe()
        
        if not user_input:
            response = "I'm sorry, I didn't catch that. Could you please repeat?"
            self.speech_service.speak(response)
            return response
        
        logger.info(f"User said: {user_input}")
        
        response = self.process_text_input(user_input)
        self.speech_service.speak(response)
        
        return response
    
    def process_text_input(self, user_input: str) -> str:
        self.conversation_history.append({'role': 'user', 'content': user_input})
        
        # 1. Detect Intent
        intent_data = self.conversational_agent.detect_intent(user_input)
        intent = intent_data.get('intent', 'general')
        entities = intent_data.get('entities', {})
        
        logger.info(f"Detected Intent: {intent}")

        # 2. STATE GUARD: If we have a vehicle selected, handle "Yes/Sure/Ok" as booking confirmation
        affirmative_words = ['yes', 'yeah', 'sure', 'ok', 'okay', 'please', 'correct', 'book it']
        if self.booking_details.get('vehicle_id') and user_input.lower().strip() in affirmative_words:
            intent = 'booking'
        
        # 3. CONTEXT EXTRACTION: Update booking details from the conversation history
        # This helps the LLM realize "tomorrow" refers to the 'date' field
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history[-3:]])
        extracted = self.conversational_agent.extract_booking_details(history_str)
        
        for key, value in extracted.items():
            if value and value != "null" and value != "None":
                self.booking_details[key] = value

        # 4. Route to the correct handler
        if intent == 'greeting' and not self.booking_details.get('vehicle_id'):
            response = self._handle_greeting()
        
        elif intent == 'inquiry':
            response = self._handle_inquiry(intent_data)
        
        # Force booking flow if we have a vehicle or if the intent is booking/confirmation
        elif intent in ['booking', 'confirmation'] or self.booking_details.get('vehicle_id'):
            response = self._handle_booking(intent_data)
        
        elif intent == 'cancellation':
            response = self._handle_cancellation()
        
        else:
            # Fallback for general questions or chat
            context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history[-5:]])
            response = self.conversational_agent.generate_response(context, user_input)
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        return response
    

    def _handle_greeting(self) -> str:
        return ("Hello! Welcome to Premium Auto Dealership. "
                "I can help you learn about our vehicles and schedule a test drive. "
                "What can I help you with today?")
    
    def _handle_inquiry(self, intent_data: Dict) -> str:
        query_result = self.knowledge_agent.query_vehicles(intent_data)
        vehicles = query_result['vehicles']
        
        if not vehicles:
            return ("I'm sorry, we don't have any vehicles matching those criteria. "
                    "Would you like to hear about our other available vehicles?")
        
        response = query_result['response']
        
        if len(vehicles) == 1:
            self.booking_details['vehicle_id'] = vehicles[0]['id']
            self.booking_details['vehicle_name'] = (
                f"{vehicles[0]['year']} {vehicles[0]['make']} {vehicles[0]['model']}"
            )
            response += " Would you like to schedule a test drive?"
        else:
            response += " Which one interests you most?"
        
        return response
    
    def _handle_booking(self, intent_data: Dict) -> str:
        entities = intent_data.get('entities', {})
        
        # 1. SMART VEHICLE LOOKUP: 
        # If we don't have a vehicle_id but the user mentioned a make/model/category
        if 'vehicle_id' not in self.booking_details:
            make = entities.get('vehicle_make') or entities.get('make')
            model = entities.get('vehicle_model') or entities.get('model')
            cat = entities.get('vehicle_category') or entities.get('category')
            
            search_results = self.knowledge_service.search_vehicles(
                make=make, 
                model=model, 
                category=cat
            )
            
            if len(search_results) == 1:
                v = search_results[0]
                self.booking_details['vehicle_id'] = v['id']
                self.booking_details['vehicle_name'] = f"{v['year']} {v['make']} {v['model']}"
                logger.info(f"Auto-selected vehicle: {self.booking_details['vehicle_id']}")
            elif len(search_results) > 1:
                return "We have a few models matching that. Did you mean the " + " or the ".join([f"{v['year']} {v['model']}" for v in search_results[:2]]) + "?"

        # 2. UPDATE ENTITIES: Update the state with any entities found in the current turn
        for key in ['date', 'time', 'customer_name', 'customer_phone']:
            if key in entities and entities[key]:
                self.booking_details[key] = entities[key]

        # 3. VALIDATION: Check what is still missing
        validation = self.booking_agent.validate_booking_details(self.booking_details)
        
        if not validation['valid']:
            missing = validation['missing_fields']
            
            # Ask for the next missing piece of information
            if 'vehicle_id' in missing or 'vehicle_name' in missing:
                return "Which vehicle would you like to test drive?"
            elif 'date' in missing:
                return "What day would you like to come in for the test drive?"
            elif 'time' in missing:
                return f"Great, I have you down for the {self.booking_details.get('vehicle_name')}. What time works best for you?"
            elif 'customer_name' in missing:
                return "Perfect. May I have your name please?"
            elif 'customer_phone' in missing:
                return f"Thanks {self.booking_details.get('customer_name')}. And what is a good phone number to reach you at?"

        # 4. FINALIZATION: If everything is valid, create the booking
        logger.info(f"All details present. Creating booking: {self.booking_details}")
        result = self.booking_agent.create_booking(self.booking_details)
        
        if result['success']:
            # Clear details after successful booking
            self.booking_details = {}
            return result['message'] + " Is there anything else I can help you with?"
        else:
            return result['message']
        
    def _handle_confirmation(self) -> str:
        if self.booking_details and 'vehicle_id' in self.booking_details:
            result = self.booking_agent.create_booking(self.booking_details)
            
            if result['success']:
                self.booking_details = {}
                return result['message']
            else:
                return result['message']
        
        return "What would you like to confirm?"
    
    def _handle_cancellation(self) -> str:
        self.booking_details = {}
        return "No problem. Is there anything else I can help you with?"
    
    def _handle_general(self, user_input: str) -> str:
        if self.booking_details:
            logger.info(f"In booking process. Current details: {self.booking_details}")
            
            validation = self.booking_agent.validate_booking_details(self.booking_details)
            skip_words = ["yes", "sure", "ok", "please", "yep", "correct"]
            if user_input.lower() in skip_words:
                    return self._handle_booking({'intent': 'booking', 'entities': {}})
            if not validation['valid']:
                missing = validation['missing_fields']
                
                if 'customer_name' in missing:
                    name_patterns = [
                        r"(?:my )?name is ([A-Za-z\s]+)",
                        r"(?:i'?m|it'?s) ([A-Za-z\s]+)",
                        r"^([A-Za-z\s]+)$"
                    ]
                    
                    for pattern in name_patterns:
                        match = re.search(pattern, user_input.lower())
                        if match:
                            name = match.group(1).strip().title()
                            self.booking_details['customer_name'] = name
                            logger.info(f"Extracted name: {name}")
                            break
                
                elif 'customer_phone' in missing:
                    phone_pattern = r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\d{10})'
                    match = re.search(phone_pattern, user_input)
                    if match:
                        phone = match.group(1)
                        self.booking_details['customer_phone'] = phone
                        logger.info(f"Extracted phone: {phone}")
                
                return self._handle_booking({'intent': 'booking', 'entities': {}})
        
        context = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_history[-5:]
        ])
        
        return self.conversational_agent.generate_response(context, user_input)
    
    def reset_conversation(self):
        self.conversation_history = []
        self.current_intent = None
        self.booking_details = {}
        logger.info("Conversation reset")
    
    def get_conversation_summary(self) -> str:
        if not self.conversation_history:
            return "No conversation yet."
        
        summary = "Conversation Summary:\n\n"
        for msg in self.conversation_history:
            role = "Customer" if msg['role'] == 'user' else "Assistant"
            summary += f"{role}: {msg['content']}\n"
        
        return summary
