from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    customer_name = Column(String)
    customer_phone = Column(String)
    vehicle_id = Column(String)
    vehicle_name = Column(String)
    booking_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String, default='confirmed')


class BookingService:
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info("Booking service initialized")
    
    def create_booking(
        self,
        customer_name: str,
        customer_phone: str,
        vehicle_id: str,
        vehicle_name: str,
        booking_date: datetime
    ) -> Booking:
        try:
            booking = Booking(
                customer_name=customer_name,
                customer_phone=customer_phone,
                vehicle_id=vehicle_id,
                vehicle_name=vehicle_name,
                booking_date=booking_date
            )
            
            self.session.add(booking)
            self.session.commit()
            
            logger.info(f"Booking created: {booking.id} for {customer_name}")
            return booking
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating booking: {str(e)}")
            raise
    
    def get_bookings_by_date(self, date: datetime) -> List[Booking]:
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        bookings = self.session.query(Booking).filter(
            Booking.booking_date >= start_of_day,
            Booking.booking_date < end_of_day,
            Booking.status == 'confirmed'
        ).all()
        
        return bookings
    
    def is_slot_available(self, booking_date: datetime) -> bool:
        hour = booking_date.hour
        if hour < 9 or hour >= 18:
            return False
        
        buffer = timedelta(minutes=15)
        start_window = booking_date - buffer
        end_window = booking_date + buffer
        
        conflicting_bookings = self.session.query(Booking).filter(
            Booking.booking_date >= start_window,
            Booking.booking_date <= end_window,
            Booking.status == 'confirmed'
        ).count()
        
        return conflicting_bookings == 0
    
    def get_available_slots(self, date: datetime, available_hours: List[str]) -> List[str]:
        available_slots = []
        
        for hour_str in available_hours:
            hour, minute = map(int, hour_str.split(':'))
            slot_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if self.is_slot_available(slot_time):
                available_slots.append(hour_str)
        
        return available_slots
    
    def cancel_booking(self, booking_id: int) -> bool:
        try:
            booking = self.session.query(Booking).filter_by(id=booking_id).first()
            
            if booking:
                booking.status = 'cancelled'
                self.session.commit()
                logger.info(f"Booking {booking_id} cancelled")
                return True
            
            return False
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error cancelling booking: {str(e)}")
            return False
    
    def get_booking_summary(self, booking: Booking) -> str:
        date_str = booking.booking_date.strftime("%A, %B %d at %I:%M %p")
        
        summary = f"Test drive booking confirmed for {booking.customer_name}. "
        summary += f"Vehicle: {booking.vehicle_name}. "
        summary += f"Date and time: {date_str}. "
        summary += f"Booking reference: {booking.id}"
        
        return summary
