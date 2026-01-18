from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class Intent(BaseModel):
    intent: str = Field(description="The detected intent: greeting, inquiry, booking, confirmation, modification, cancellation, or general")
    entities: Dict[str, str] = Field(default_factory=dict, description="Extracted entities like vehicle_category, date, time, etc.")
    confidence: float = Field(default=0.0, description="Confidence score 0-1")


class BookingDetails(BaseModel):
    vehicle_id: Optional[str] = Field(default=None, description="Vehicle ID")
    vehicle_name: Optional[str] = Field(default=None, description="Full vehicle name")
    date: Optional[str] = Field(default=None, description="Booking date")
    time: Optional[str] = Field(default=None, description="Booking time")
    customer_name: Optional[str] = Field(default=None, description="Customer name")
    customer_phone: Optional[str] = Field(default=None, description="Customer phone number")


class ConversationalAgent:
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.intent_parser = PydanticOutputParser(pydantic_object=Intent)
        self.booking_parser = PydanticOutputParser(pydantic_object=BookingDetails)
        
        self.intent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at understanding customer intent in auto dealership conversations.
            
Analyze the customer's message and identify:
1. Intent: greeting, inquiry, booking, confirmation, modification, cancellation, or general
2. Entities: vehicle_category (sedan/suv/truck/electric), vehicle_make, vehicle_model, date, time, customer_name, customer_phone
3. Confidence: How confident you are (0.0 to 1.0)
             
Analyze the customer's message.
CRITICAL RULES:
- If the user says "yes", "please", "sure", "book it", or "okay", the intent is 'confirmation'.
- If the user says "hi", "hello", "good morning", the intent is 'greeting'. 
- NEVER label "yes" as a greeting.

{format_instructions}"""),
            ("user", "{input}")
        ])
        
        self.response_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly, professional auto dealership customer service representative.
            
Your personality:
- Warm and welcoming
- Efficient and clear
- Ask one question at a time
- Keep responses concise (2-3 sentences max)
- Always professional

Context: {context}"""),
            ("user", "{input}")
        ])
        
        self.booking_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract booking details (vehicle_name, date, time, customer_name, customer_phone) from the conversation.
            Pay attention to the Assistant's questions to understand what the User's short answers mean.
            Example: If Assistant asks "What is your name?" and User says "John", then customer_name is "John".
            
            {format_instructions}"""),
            ("user", "Conversation History:\n{conversation}")
        ])
    
    def detect_intent(self, user_input: str) -> Dict:
        try:
            chain = self.intent_prompt | self.llm
            format_instructions = self.intent_parser.get_format_instructions()
            
            response = chain.invoke({
                "input": user_input,
                "format_instructions": format_instructions
            })
            
            content = response.content
            
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                json_str = content
            
            intent_obj = json.loads(json_str)
            logger.info(f"Detected intent: {intent_obj}")
            
            return intent_obj
            
        except Exception as e:
            logger.error(f"Error detecting intent: {str(e)}")
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return {"intent": "greeting", "entities": {}, "confidence": 0.8}
        
        if any(word in user_input_lower for word in ["book", "schedule", "appointment", "test drive"]):
            entities = {}
            
            if "sedan" in user_input_lower:
                entities["vehicle_category"] = "sedan"
            elif "suv" in user_input_lower:
                entities["vehicle_category"] = "suv"
            elif "truck" in user_input_lower:
                entities["vehicle_category"] = "truck"
            elif "electric" in user_input_lower:
                entities["vehicle_category"] = "electric"
            
            if "tomorrow" in user_input_lower:
                entities["date"] = "tomorrow"
            if any(time in user_input_lower for time in ["am", "pm"]):
                words = user_input_lower.split()
                for i, word in enumerate(words):
                    if "am" in word or "pm" in word:
                        entities["time"] = word
                        break
            
            return {"intent": "booking", "entities": entities, "confidence": 0.7}
        
        if any(word in user_input_lower for word in ["what", "which", "show", "tell me", "available", "have"]):
            entities = {}
            
            if "sedan" in user_input_lower:
                entities["vehicle_category"] = "sedan"
            elif "suv" in user_input_lower:
                entities["vehicle_category"] = "suv"
            elif "truck" in user_input_lower:
                entities["vehicle_category"] = "truck"
            
            return {"intent": "inquiry", "entities": entities, "confidence": 0.7}
        
        if any(word in user_input_lower for word in ["yes", "confirm", "correct", "that's right"]):
            return {"intent": "confirmation", "entities": {}, "confidence": 0.8}
        
        if any(word in user_input_lower for word in ["no", "cancel", "nevermind", "forget"]):
            return {"intent": "cancellation", "entities": {}, "confidence": 0.8}
        
        return {"intent": "general", "entities": {}, "confidence": 0.5}
    
    def generate_response(self, context: str, user_input: str) -> str:
        try:
            chain = self.response_prompt | self.llm
            
            response = chain.invoke({
                "context": context,
                "input": user_input
            })
            
            response_text = response.content.strip()
            logger.info(f"Generated response: {response_text}")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, I'm having trouble processing that. Could you please repeat?"
    
    def extract_booking_details(self, conversation_history: str) -> Dict:
        try:
            chain = self.booking_prompt | self.llm
            format_instructions = self.booking_parser.get_format_instructions()
            
            response = chain.invoke({
                "conversation": conversation_history,
                "format_instructions": format_instructions
            })
            
            content = response.content
            
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "{" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
            else:
                json_str = content
            
            details = json.loads(json_str)
            logger.info(f"Extracted booking details: {details}")
            return details
            
        except Exception as e:
            logger.error(f"Error extracting booking details: {str(e)}")
            return {}
