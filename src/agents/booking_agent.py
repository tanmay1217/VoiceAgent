from langchain_openai import ChatOpenAI
from src.services.booking_service import BookingService
from datetime import datetime, timedelta
from dateutil import parser
from typing import Dict, Optional, List
import logging
import re

logger = logging.getLogger(__name__)

class BookingAgent:
    def __init__(self, llm: ChatOpenAI, booking_service: BookingService):
        self.llm = llm
        self.booking_service = booking_service

    def validate_phone(self, phone_str: str) -> bool:
        if not phone_str: return False
        clean_phone = re.sub(r'\D', '', str(phone_str)) # Ensure string conversion
        return len(clean_phone) == 10
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            date_str = date_str.lower().strip()
            if date_str == "today": return datetime.now()
            if date_str == "tomorrow": return datetime.now() + timedelta(days=1)
            # Standard logic for "next monday" etc.
            if "next" in date_str:
                weekdays = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
                for day, num in weekdays.items():
                    if day in date_str:
                        today = datetime.now()
                        days_ahead = num - today.weekday()
                        if days_ahead <= 0: days_ahead += 7
                        return today + timedelta(days=days_ahead)
            return parser.parse(date_str, fuzzy=True)
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
            return None
    
    def parse_time(self, time_str: str) -> Optional[tuple]:
        try:
            time_str = time_str.strip().upper()
            if "AM" in time_str or "PM" in time_str:
                is_pm = "PM" in time_str
                time_str = re.sub(r'[ APM]', '', time_str)
                if ":" in time_str:
                    hour, minute = map(int, time_str.split(":"))
                else:
                    hour, minute = int(time_str), 0
                if is_pm and hour != 12: hour += 12
                elif not is_pm and hour == 12: hour = 0
                return (hour, minute)
            parsed = parser.parse(time_str, fuzzy=True)
            return (parsed.hour, parsed.minute)
        except Exception: return None
    
    def check_availability(self, booking_date: datetime) -> Dict:
        if booking_date < datetime.now():
            return {'available': False, 'message': "That time has already passed. Please choose a future date."}
        
        if self.booking_service.is_slot_available(booking_date):
            return {'available': True, 'message': f"Great! {booking_date.strftime('%I:%M %p')} is available."}
        else:
            standard_hours = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
            avail = self.booking_service.get_available_slots(booking_date, standard_hours)
            if avail:
                formatted = [datetime.strptime(s, "%H:%M").strftime("%I:%M %p") for s in avail[:2]]
                return {
                    'available': False,
                    'message': f"I'm sorry, that time is already booked. Would {' or '.join(formatted)} work instead?",
                    'alternatives': avail
                }
            return {'available': False, 'message': "We are fully booked that day. How about another date?"}
        
    def create_booking(self, booking_details: Dict) -> Dict:
        try:
            d_obj = self.parse_date(booking_details.get('date'))
            t_tup = self.parse_time(booking_details.get('time'))
            if not d_obj or not t_tup: raise ValueError("Invalid date or time")
            
            dt = d_obj.replace(hour=t_tup[0], minute=t_tup[1], second=0, microsecond=0)
            booking = self.booking_service.create_booking(
                customer_name=booking_details.get('customer_name'),
                customer_phone=booking_details.get('customer_phone'),
                vehicle_id=booking_details.get('vehicle_id'),
                vehicle_name=booking_details.get('vehicle_name'),
                booking_date=dt
            )
            return {'success': True, 'message': self.booking_service.get_booking_summary(booking)}
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {'success': False, 'message': "There was an error saving your booking."}
        
    def validate_booking_details(self, details: Dict) -> Dict:
        required = ['vehicle_id', 'vehicle_name', 'date', 'time', 'customer_name', 'customer_phone']
        missing = [f for f in required if not details.get(f) or details.get(f) in ["null", "None", "Not provided"]]
        
        if missing:
            return {'valid': False, 'missing_fields': missing, 'message': f"I still need your {missing[0].replace('customer_', '')}."}

        if not self.validate_phone(details.get('customer_phone', '')):
            return {
                'valid': False, 
                'invalid_fields': ['customer_phone'],
                'message': "That phone number doesn't seem right. Could you please provide a valid 10-digit mobile number?"
            }
        return {'valid': True, 'message': "All details confirmed!"}