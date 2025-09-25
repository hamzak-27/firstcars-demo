"""
Multi-Agent Car Rental Booking System
4-Agent Architecture for Enhanced Booking Processing

Agent 1: Booking Classification Agent (single vs multiple + count)
Agent 2: Single Booking Extraction Agent  
Agent 3: Multiple Booking Extraction Agent
Agent 4: Business Rules Validation Agent
"""

__version__ = "1.0.0"
__author__ = "FirstCars AI Team"

# Import only what's currently implemented
try:
    from .agents.classification_agent import BookingClassificationAgent
    CLASSIFICATION_AVAILABLE = True
except ImportError:
    CLASSIFICATION_AVAILABLE = False

__all__ = []

if CLASSIFICATION_AVAILABLE:
    __all__.append('BookingClassificationAgent')

# Other imports will be added as they are implemented
# from .orchestrator import MultiAgentOrchestrator
# from .agents.single_booking_agent import SingleBookingAgent  
# from .agents.multiple_booking_agent import MultipleBookingAgent
# from .agents.validation_agent import ValidationAgent
