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
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        intent_data = self.conversational_agent.detect_intent(user_input)
        intent = intent_data.get('intent', 'general')
        entities = intent_data.get('entities', {})
        
        logger.info(f"Intent: {intent}, Entities: {entities}")
        logger.info(f"Current booking details: {self.booking_details}")
        
        if intent == 'greeting':
            if entities.get('customer_name') and self.booking_details and 'customer_name' not in self.booking_details:
                self.booking_details['customer_name'] = entities['customer_name']
                response = self._handle_booking({'intent': 'booking', 'entities': entities})
            else:
                response = self._handle_greeting()
        
        elif intent == 'inquiry':
            response = self._handle_inquiry(intent_data)
        
        elif intent == 'booking':
            response = self._handle_booking(intent_data)
        
        elif intent == 'confirmation':
            response = self._handle_confirmation()
        
        elif intent == 'cancellation':
            response = self._handle_cancellation()
        
        else:
            response = self._handle_general(user_input)
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })
        
        logger.info(f"Response: {response}")
        logger.info(f"Updated booking details: {self.booking_details}")
        
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
        
        if 'vehicle_category' in entities:
            if 'vehicle_id' not in self.booking_details:
                vehicles = self.knowledge_service.get_vehicles_by_category(entities['vehicle_category'])
                if vehicles:
                    vehicle = vehicles[0]
                    self.booking_details['vehicle_id'] = vehicle['id']
                    self.booking_details['vehicle_name'] = (
                        f"{vehicle['year']} {vehicle['make']} {vehicle['model']}"
                    )
        
        if 'date' in entities:
            self.booking_details['date'] = entities['date']
        if 'time' in entities:
            self.booking_details['time'] = entities['time']
        if 'customer_name' in entities:
            self.booking_details['customer_name'] = entities['customer_name']
        if 'customer_phone' in entities:
            self.booking_details['customer_phone'] = entities['customer_phone']
        
        validation = self.booking_agent.validate_booking_details(self.booking_details)
        
        if not validation['valid']:
            missing = validation['missing_fields']
            
            if 'vehicle_id' in missing or 'vehicle_name' in missing:
                return "Which vehicle would you like to test drive?"
            elif 'date' in missing:
                return "What day would you like to come in?"
            elif 'time' in missing:
                return "What time works best for you?"
            elif 'customer_name' in missing:
                return "May I have your name please?"
            elif 'customer_phone' in missing:
                return "And your phone number?"
        
        logger.info(f"Creating booking with details: {self.booking_details}")
        result = self.booking_agent.create_booking(self.booking_details)
        
        if result['success']:
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
