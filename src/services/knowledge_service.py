import json
from typing import List, Dict, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class KnowledgeService:
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self) -> Dict:
        try:
            with open(settings.KNOWLEDGE_BASE_PATH, 'r') as f:
                data = json.load(f)
            logger.info("Knowledge base loaded successfully")
            return data
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            raise
    
    def get_all_vehicles(self) -> List[Dict]:
        return self.knowledge_base.get('vehicles', [])
    
    def get_vehicles_by_category(self, category: str) -> List[Dict]:
        category_lower = category.lower()
        vehicles = [
            v for v in self.get_all_vehicles()
            if v.get('category', '').lower() == category_lower and v.get('available', False)
        ]
        logger.info(f"Found {len(vehicles)} {category} vehicles")
        return vehicles
    
    def get_vehicle_by_id(self, vehicle_id: str) -> Optional[Dict]:
        for vehicle in self.get_all_vehicles():
            if vehicle.get('id') == vehicle_id:
                return vehicle
        return None
    
    def search_vehicles(self, 
                        make: Optional[str] = None, 
                        model: Optional[str] = None,
                        category: Optional[str] = None,
                        max_price: Optional[float] = None) -> List[Dict]:
        
        results = self.get_all_vehicles()
        
        if make:
            results = [v for v in results if v.get('make', '').lower() == make.lower()]
        
        if model:
            results = [v for v in results if v.get('model', '').lower() == model.lower()]
        
        if category:
            results = [v for v in results if v.get('category', '').lower() == category.lower()]
        
        if max_price:
            results = [v for v in results if v.get('price', float('inf')) <= max_price]
        
        results = [v for v in results if v.get('available', False)]
        
        logger.info(f"Search returned {len(results)} vehicles")
        return results
    
    def get_vehicle_summary(self, vehicle: Dict) -> str:
        summary = f"{vehicle['year']} {vehicle['make']} {vehicle['model']} {vehicle['variant']}"
        summary += f" - ${vehicle['price']:,}"
        
        if vehicle.get('fuel_type'):
            summary += f", {vehicle['fuel_type']}"
        
        if vehicle.get('features'):
            key_features = ', '.join(vehicle['features'][:3])
            summary += f". Key features: {key_features}"
        
        return summary
    
    def get_available_categories(self) -> List[str]:
        categories = set(v['category'] for v in self.get_all_vehicles() if v.get('available', False))
        return sorted(list(categories))
    
    def get_test_drive_info(self) -> Dict:
        return self.knowledge_base.get('test_drive_slots', {})
    
    def format_vehicle_list(self, vehicles: List[Dict], max_items: int = 3) -> str:
        if not vehicles:
            return "We don't have any vehicles matching those criteria at the moment."
        
        if len(vehicles) == 1:
            return f"We have the {self.get_vehicle_summary(vehicles[0])} available."
        
        result = f"We have {len(vehicles)} options available. "
        
        shown = vehicles[:max_items]
        for i, vehicle in enumerate(shown, 1):
            result += f"{i}. {self.get_vehicle_summary(vehicle)}. "
        
        if len(vehicles) > max_items:
            result += f"And {len(vehicles) - max_items} more options."
        
        return result
