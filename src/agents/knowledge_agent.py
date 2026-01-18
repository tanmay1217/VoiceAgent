from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.services.knowledge_service import KnowledgeService
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class KnowledgeAgent:
    
    def __init__(self, llm: ChatOpenAI, knowledge_service: KnowledgeService):
        self.llm = llm
        self.knowledge_service = knowledge_service
        
        self.recommendation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a knowledgeable vehicle specialist at an auto dealership.
            
Based on customer requirements, recommend the best 2-3 vehicles from the available inventory.
Explain why each vehicle is a good fit.
Keep the response conversational and under 100 words.
Be specific about features that match their needs.

Available vehicles:
{vehicle_info}"""),
            ("user", "Customer requirements: {requirements}")
        ])
    
    def query_vehicles(self, intent_data: Dict) -> Dict:
        entities = intent_data.get('entities', {})
        
        category = entities.get('vehicle_category')
        make = entities.get('vehicle_make')
        model = entities.get('vehicle_model')
        max_price = entities.get('max_price')
        
        if category:
            vehicles = self.knowledge_service.get_vehicles_by_category(category)
        else:
            vehicles = self.knowledge_service.search_vehicles(
                make=make,
                model=model,
                max_price=max_price
            )
        
        response_text = self.knowledge_service.format_vehicle_list(vehicles)
        
        return {
            'vehicles': vehicles,
            'count': len(vehicles),
            'response': response_text,
            'category': category
        }
    
    def get_vehicle_details(self, vehicle_id: str) -> Optional[Dict]:
        vehicle = self.knowledge_service.get_vehicle_by_id(vehicle_id)
        
        if not vehicle:
            logger.warning(f"Vehicle not found: {vehicle_id}")
            return None
        
        return vehicle
    
    def get_vehicle_recommendation(self, requirements: str) -> str:
        all_vehicles = self.knowledge_service.get_all_vehicles()
        available_vehicles = [v for v in all_vehicles if v.get('available', False)]
        
        if not available_vehicles:
            return "I apologize, but we don't have any vehicles available at the moment."
        
        vehicle_info = "\n".join([
            f"- {self.knowledge_service.get_vehicle_summary(v)}"
            for v in available_vehicles
        ])
        
        try:
            chain = self.recommendation_prompt | self.llm
            
            response = chain.invoke({
                "vehicle_info": vehicle_info,
                "requirements": requirements
            })
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            categories = self.knowledge_service.get_available_categories()
            return f"I can help you find the right vehicle. We have {', '.join(categories)} available. What interests you most?"
    
    def compare_vehicles(self, vehicle_ids: List[str]) -> str:
        vehicles = [
            self.knowledge_service.get_vehicle_by_id(vid)
            for vid in vehicle_ids
        ]
        
        vehicles = [v for v in vehicles if v is not None]
        
        if len(vehicles) < 2:
            return "I need at least two vehicles to compare."
        
        comparison = "Here's how these vehicles compare:\n\n"
        
        for i, vehicle in enumerate(vehicles, 1):
            comparison += f"{i}. {self.knowledge_service.get_vehicle_summary(vehicle)}\n"
        
        return comparison
    
    def get_available_categories(self) -> List[str]:
        return self.knowledge_service.get_available_categories()
    
    def answer_vehicle_question(self, question: str, vehicle_id: str) -> str:
        vehicle = self.get_vehicle_details(vehicle_id)
        
        if not vehicle:
            return "I couldn't find information about that vehicle."
        
        question_lower = question.lower()
        
        if "price" in question_lower or "cost" in question_lower:
            return f"The {vehicle['year']} {vehicle['make']} {vehicle['model']} is priced at ${vehicle['price']:,}."
        
        elif "features" in question_lower:
            features = ", ".join(vehicle.get('features', [])[:5])
            return f"Key features include: {features}."
        
        elif "color" in question_lower:
            colors = ", ".join(vehicle.get('colors', []))
            return f"Available colors: {colors}."
        
        elif "fuel" in question_lower or "gas" in question_lower:
            return f"This vehicle runs on {vehicle.get('fuel_type', 'gasoline')}."
        
        elif "transmission" in question_lower:
            return f"It has a {vehicle.get('transmission', 'automatic')} transmission."
        
        else:
            return self.knowledge_service.get_vehicle_summary(vehicle)
