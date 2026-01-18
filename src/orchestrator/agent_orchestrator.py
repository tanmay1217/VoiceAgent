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
        self.llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=settings.OPENAI_TEMPERATURE)
        self.knowledge_service = KnowledgeService()
        self.booking_service = BookingService()
        self.speech_service = SpeechService()
        
        self.conversational_agent = ConversationalAgent(self.llm)
        self.knowledge_agent = KnowledgeAgent(self.llm, self.knowledge_service)
        self.booking_agent = BookingAgent(self.llm, self.booking_service)
        
        self.conversation_history = []
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
        
        intent_data = self.conversational_agent.detect_intent(user_input)
        intent = intent_data.get('intent', 'general')
        entities = intent_data.get('entities', {})
        
        is_booking_active = bool(self.booking_details.get('vehicle_id'))
        logger.info(f"Intent: {intent} | Booking Active: {is_booking_active}")

        # 1. Context Extraction
        if intent == 'booking' or is_booking_active:
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history[-3:]])
            extracted = self.conversational_agent.extract_booking_details(history_str)
            for key, value in extracted.items():
                if value and value not in ["null", "None"]:
                    if key in ['vehicle_id', 'vehicle_name'] and is_booking_active: continue
                    self.booking_details[key] = value

        # 2. Routing
        if intent == 'greeting' and not is_booking_active:
            response = self._handle_greeting()
        elif intent == 'inquiry':
            response = self._handle_inquiry(intent_data)
        elif intent == 'booking' or (is_booking_active and intent in ['confirmation', 'general', 'modification']):
            response = self._handle_booking(intent_data)
        elif intent == 'cancellation':
            response = self._handle_cancellation()
        else:
            context = "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history[-5:]])
            response = self.conversational_agent.generate_response(context, user_input)
        
        self.conversation_history.append({'role': 'assistant', 'content': response})
        return response

    def _handle_greeting(self) -> str:
        return "Hello! Welcome to Premium Auto Dealership. I can help you learn about our vehicles and schedule a test drive. What can I help you with today?"
    
    def _handle_inquiry(self, intent_data: Dict) -> str:
        res = self.knowledge_agent.query_vehicles(intent_data)
        if res['vehicles'] and len(res['vehicles']) == 1:
            v = res['vehicles'][0]
            self.booking_details['vehicle_id'], self.booking_details['vehicle_name'] = v['id'], f"{v['year']} {v['make']} {v['model']}"
            return res['response'] + " Would you like to schedule a test drive?"
        return res['response']
    
    def _handle_booking(self, intent_data: Dict) -> str:
        entities = intent_data.get('entities', {})
        
        # 1. Vehicle Selection
        if 'vehicle_id' not in self.booking_details:
            make = entities.get('vehicle_make')
            model = entities.get('vehicle_model')
            res = self.knowledge_service.search_vehicles(make=make, model=model)
            if len(res) == 1:
                v = res[0]
                self.booking_details['vehicle_id'] = v['id']
                self.booking_details['vehicle_name'] = f"{v['year']} {v['make']} {v['model']}"
            elif len(res) > 1:
                return "We have a few models matching that. Did you mean the " + " or the ".join([f"{v['year']} {v['model']}" for v in res[:2]]) + "?"
            else:
                return "Which vehicle would you like to test drive? We have sedans, SUVs, and trucks."

        # 2. Update basic info
        for key in ['date', 'time', 'customer_name', 'customer_phone']:
            if key in entities and entities[key]: self.booking_details[key] = entities[key]

        # 3. IMMEDIATE AVAILABILITY CHECK
        if self.booking_details.get('date') and self.booking_details.get('time') and not self.booking_details.get('customer_name'):
            d_obj = self.booking_agent.parse_date(self.booking_details['date'])
            t_tup = self.booking_agent.parse_time(self.booking_details['time'])
            if d_obj and t_tup:
                dt_check = d_obj.replace(hour=t_tup[0], minute=t_tup[1], second=0, microsecond=0)
                avail = self.booking_agent.check_availability(dt_check)
                if not avail['available']:
                    self.booking_details['time'] = None
                    return avail['message']

        # 4. Validation
        val = self.booking_agent.validate_booking_details(self.booking_details)
        if not val['valid']:
            if 'invalid_fields' in val:
                if 'customer_phone' in val['invalid_fields']: self.booking_details['customer_phone'] = None
                return val['message']
            
            missing = val.get('missing_fields', [])
            if 'date' in missing: return "What day would you like to come in?"
            if 'time' in missing: return f"What time works best for the {self.booking_details['vehicle_name']}?"
            if 'customer_name' in missing: return f"Perfect, the {self.booking_details['time']} slot is available. May I have your name please?"
            if 'customer_phone' in missing: return f"Thanks {self.booking_details['customer_name']}. And what is a good 10-digit phone number?"

        # 5. Finalize
        result = self.booking_agent.create_booking(self.booking_details)
        if result['success']:
            self.booking_details = {}
            return result['message'] + " Is there anything else I can help you with?"
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
        return "No problem, I've cleared the request. What else can I do for you?"
    
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
