from langchain_openai import ChatOpenAI
from src.services.booking_service import BookingService
from datetime import datetime, timedelta
from dateutil import parser
from typing import Dict, Optional
import logging
import re


logger = logging.getLogger(__name__)


class BookingAgent:
    
    def __init__(self, llm: ChatOpenAI, booking_service: BookingService):
        self.llm = llm
        self.booking_service = booking_service

    def validate_phone(self, phone_str: str) -> bool:
        """
        Validates that the phone number contains exactly 10 digits.
        Removes common formatting characters like -, ( ), and spaces.
        """
        if not phone_str:
            return False
            
        # Remove non-numeric characters
        clean_phone = re.sub(r'\D', '', phone_str)
        
        # Check if it's exactly 10 digits
        return len(clean_phone) == 10
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            date_str = date_str.lower().strip()
            
            if date_str == "today":
                return datetime.now()
            elif date_str == "tomorrow":
                return datetime.now() + timedelta(days=1)
            elif "next" in date_str:
                weekdays = {
                    'monday': 0, 'tuesday': 1, 'wednesday': 2,
                    'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
                }
                for day, num in weekdays.items():
                    if day in date_str:
                        today = datetime.now()
                        days_ahead = num - today.weekday()
                        if days_ahead <= 0:
                            days_ahead += 7
                        return today + timedelta(days=days_ahead)
            
            return parser.parse(date_str, fuzzy=True)
            
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
            return None
    
    def parse_time(self, time_str: str) -> Optional[tuple]:
        try:
            time_str = time_str.strip().upper()
            
            if "AM" in time_str or "PM" in time_str:
                time_str = time_str.replace(" ", "")
                is_pm = "PM" in time_str
                time_str = time_str.replace("AM", "").replace("PM", "")
                
                if ":" in time_str:
                    hour, minute = map(int, time_str.split(":"))
                else:
                    hour = int(time_str)
                    minute = 0
                
                if is_pm and hour != 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                
                return (hour, minute)
            
            parsed = parser.parse(time_str, fuzzy=True)
            return (parsed.hour, parsed.minute)
            
        except Exception as e:
            logger.error(f"Error parsing time '{time_str}': {str(e)}")
            return None
    
    def check_availability(self, booking_date: datetime) -> Dict:
        """
        Checks if a specific datetime is available for a test drive.
        """
        if booking_date < datetime.now():
            return {
                'available': False,
                'message': "That time has already passed. Please choose a future date and time."
            }
        
        is_available = self.booking_service.is_slot_available(booking_date)
        
        if is_available:
            return {
                'available': True,
                'message': f"Great! {booking_date.strftime('%I:%M %p')} is available."
            }
        else:
            # Get available slots from Knowledge Base settings (or hardcoded here)
            standard_hours = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]
            available_slots = self.booking_service.get_available_slots(booking_date, standard_hours)
            
            if available_slots:
                # Format the first few slots for a cleaner voice response
                formatted_slots = [datetime.strptime(s, "%H:%M").strftime("%I:%M %p") for s in available_slots[:2]]
                slots_str = " or ".join(formatted_slots)
                return {
                    'available': False,
                    'message': f"I'm sorry, that time is already booked. Would {slots_str} work for you instead?",
                    'alternatives': available_slots
                }
            else:
                return {
                    'available': False,
                    'message': "We are fully booked for that day. Could you try a different date?"
                }
            
            
    def create_booking(self, booking_details: Dict) -> Dict:
        try:
            date_obj = self.parse_date(booking_details.get('date', 'tomorrow'))
            time_tuple = self.parse_time(booking_details.get('time', '11:00'))
            
            if not date_obj or not time_tuple:
                return {
                    'success': False,
                    'message': "I couldn't understand the date or time. Could you please specify again?"
                }
            
            hour, minute = time_tuple
            booking_datetime = date_obj.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            availability = self.check_availability(booking_datetime)
            
            if not availability['available']:
                return {
                    'success': False,
                    'message': availability['message'],
                    'alternatives': availability.get('alternatives')
                }
            
            booking = self.booking_service.create_booking(
                customer_name=booking_details.get('customer_name', 'Guest'),
                customer_phone=booking_details.get('customer_phone', ''),
                vehicle_id=booking_details.get('vehicle_id', ''),
                vehicle_name=booking_details.get('vehicle_name', ''),
                booking_date=booking_datetime
            )
            
            confirmation = self.booking_service.get_booking_summary(booking)
            
            return {
                'success': True,
                'message': confirmation,
                'booking_id': booking.id,
                'booking_date': booking_datetime
            }
            
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {
                'success': False,
                'message': "I'm sorry, there was an error creating your booking. Please try again."
            }
    
    def validate_booking_details(self, details: Dict) -> Dict:
        """
        Validates all required fields and specific formats for the booking.
        """
        required_fields = ['vehicle_id', 'vehicle_name', 'date', 'time', 'customer_name', 'customer_phone']
        
        # 1. Check for missing fields
        missing = [
            field for field in required_fields 
            if not details.get(field) or details.get(field) in ["Not provided", "null", "None"]
        ]
        
        if missing:
            return {
                'valid': False,
                'missing_fields': missing,
                'message': f"I still need your {missing[0].replace('customer_', '')}."
            }

        # 2. Specific Validation: Phone Number
        phone = details.get('customer_phone', '')
        if not self.validate_phone(phone):
            return {
                'valid': False,
                'invalid_fields': ['customer_phone'],
                'message': "That phone number doesn't seem right. Could you please provide a valid 10-digit mobile number?"
            }
        
        return {
            'valid': True,
            'message': "All details confirmed!"
        }
    
    def get_available_time_slots(self, date_str: str) -> Dict:
        date_obj = self.parse_date(date_str)
        
        if not date_obj:
            return {
                'success': False,
                'message': "I couldn't understand that date. Could you specify it differently?"
            }
        
        available_hours = ["9:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
        slots = self.booking_service.get_available_slots(date_obj, available_hours)
        
        if not slots:
            return {
                'success': False,
                'message': f"Unfortunately, we don't have any availability on {date_obj.strftime('%A, %B %d')}. Would you like to try a different day?"
            }
        
        slots_str = ", ".join(slots)
        return {
            'success': True,
            'slots': slots,
            'message': f"Available times on {date_obj.strftime('%A, %B %d')}: {slots_str}"
        }
