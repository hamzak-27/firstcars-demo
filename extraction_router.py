#!/usr/bin/env python3
"""
Extraction Router for Car Rental Bookings
Routes classification results to appropriate extraction agents (single vs multiple)
"""

import logging
import time
from typing import Dict, List, Optional, Any

from base_extraction_agent import ExtractionResult
from single_booking_extraction_agent import SingleBookingExtractionAgent
from multiple_booking_extraction_agent import MultipleBookingExtractionAgent
from gemma_classification_agent import ClassificationResult, BookingType

logger = logging.getLogger(__name__)

class ExtractionRouter:
    """
    Routes booking extraction requests to appropriate specialized agents
    
    Routing Logic:
    - Single booking classification → SingleBookingExtractionAgent
    - Multiple booking classification → MultipleBookingExtractionAgent
    - Handles agent initialization and error fallback
    """
    
    def __init__(self, api_key: str = None):
        """Initialize extraction router with both agents"""
        
        self.api_key = api_key
        
        # Initialize both extraction agents
        try:
            self.single_agent = SingleBookingExtractionAgent(api_key=api_key)
            logger.info("✅ Single booking extraction agent initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize single booking agent: {str(e)}")
            self.single_agent = None
        
        try:
            # Use MultipleBookingExtractionAgent for text-based multiple booking extraction
            self.multiple_agent = MultipleBookingExtractionAgent(api_key=api_key)
            logger.info("✅ Multiple booking extraction agent initialized (AI-powered)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize multiple booking extraction agent: {str(e)}")
            # Fallback to enhanced processor if agent fails
            try:
                from enhanced_multi_booking_processor import EnhancedMultiBookingProcessor
                self.multiple_agent = EnhancedMultiBookingProcessor(gemini_api_key=api_key)
                logger.info("✅ Enhanced multi-booking processor initialized (Textract fallback)")
            except Exception as e2:
                logger.error(f"❌ Failed to initialize any multiple booking processor: {str(e2)}")
                self.multiple_agent = None
        
        # Routing statistics
        self.routing_stats = {
            'total_requests': 0,
            'single_booking_requests': 0,
            'multiple_booking_requests': 0,
            'fallback_requests': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_cost_inr': 0.0,
            'total_processing_time': 0.0
        }
        
        logger.info("ExtractionRouter initialized")
    
    def route_and_extract(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """
        Route extraction request to appropriate agent based on classification
        
        Args:
            content: Email content or OCR extracted text
            classification_result: Result from classification agent
            
        Returns:
            ExtractionResult with booking data in DataFrame format
        """
        
        start_time = time.time()
        self.routing_stats['total_requests'] += 1
        
        logger.info(f"Routing extraction request: {classification_result.booking_type.value} "
                   f"({classification_result.booking_count} bookings)")
        
        # Check if content is already processed by Textract (from file upload)
        if "TABLE EXTRACTION RESULTS" in content and "enhanced_multi_booking" in content:
            logger.info("Content already processed by EnhancedMultiBookingProcessor - creating direct result")
            return self._create_textract_result(content, classification_result)
        
        try:
            # Route based on booking type
            if classification_result.booking_type == BookingType.SINGLE:
                result = self._route_to_single_agent(content, classification_result)
                self.routing_stats['single_booking_requests'] += 1
                
            elif classification_result.booking_type == BookingType.MULTIPLE:
                result = self._route_to_multiple_agent(content, classification_result)
                self.routing_stats['multiple_booking_requests'] += 1
                
            else:
                # Fallback for unknown booking types
                logger.warning(f"Unknown booking type: {classification_result.booking_type}")
                result = self._fallback_extraction(content, classification_result)
                self.routing_stats['fallback_requests'] += 1
            
            # Update statistics
            self._update_stats(result)
            
            # Add routing metadata
            if result.metadata is None:
                result.metadata = {}
            
            result.metadata.update({
                'router_used': True,
                'routing_decision': classification_result.booking_type.value,
                'agent_selected': self._get_agent_name(classification_result.booking_type),
                'classification_confidence': classification_result.confidence_score,
                'total_routing_time': time.time() - start_time
            })
            
            logger.info(f"Extraction routed successfully: {result.extraction_method} "
                       f"({result.booking_count} bookings, ₹{result.cost_inr:.4f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Extraction routing failed: {str(e)}")
            self.routing_stats['failed_extractions'] += 1
            
            # Return error result
            processing_time = time.time() - start_time
            return ExtractionResult(
                success=False,
                bookings_dataframe=self.single_agent._create_dataframe_from_bookings([]) if self.single_agent else None,
                booking_count=0,
                confidence_score=0.0,
                processing_time=processing_time,
                cost_inr=0.0,
                extraction_method="routing_failed",
                error_message=str(e),
                metadata={
                    'router_used': True,
                    'routing_error': str(e),
                    'classification_type': classification_result.booking_type.value
                }
            )
    
    def _route_to_single_agent(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """Route to single booking extraction agent"""
        
        if not self.single_agent:
            raise ValueError("Single booking extraction agent not available")
        
        logger.debug("Routing to single booking extraction agent")
        return self.single_agent.extract(content, classification_result)
    
    def _route_to_multiple_agent(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """Route to multiple booking extraction agent or processor"""
        
        if not self.multiple_agent:
            raise ValueError("Multiple booking extraction agent not available")
        
        logger.debug("Routing to multiple booking extraction agent/processor")
        
        # Prefer the standard extract method if available (MultipleBookingExtractionAgent)
        if hasattr(self.multiple_agent, 'extract'):
            logger.info("Using MultipleBookingExtractionAgent (AI-powered text extraction)")
            return self.multiple_agent.extract(content, classification_result)
        
        # Fallback: Check if this is the EnhancedMultiBookingProcessor (has process_document method)
        elif hasattr(self.multiple_agent, 'process_document'):
            logger.info("Using EnhancedMultiBookingProcessor (Textract-based fallback)")
            
            # For processor, we need to simulate document processing
            # Convert text content to a mock file format
            try:
                import tempfile
                import io
                
                # Create a temporary text file with the content
                content_bytes = content.encode('utf-8')
                result = self.multiple_agent.process_document(content_bytes, "text_content.txt")
                
                # Convert StructuredExtractionResult to ExtractionResult
                from base_extraction_agent import ExtractionResult
                
                # Create DataFrame from bookings
                booking_records = []
                for booking in result.bookings:
                    record = {
                        'Customer': booking.corporate or 'Corporate Client',
                        'Booked By Name': booking.booked_by_name or 'Travel Coordinator', 
                        'Booked By Phone Number': booking.booked_by_phone or '',
                        'Booked By Email': booking.booked_by_email or '',
                        'Passenger Name': booking.passenger_name or 'Guest',
                        'Passenger Phone Number': booking.passenger_phone or '',
                        'Passenger Email': booking.passenger_email or '',
                        'From (Service Location)': booking.from_location or '',
                        'To': booking.to_location or '',
                        'Vehicle Group': booking.vehicle_group or '',
                        'Duty Type': booking.duty_type or 'P2P',
                        'Start Date': booking.start_date or '',
                        'End Date': booking.end_date or '',
                        'Rep. Time': booking.reporting_time or '',
                        'Reporting Address': booking.reporting_address or '',
                        'Drop Address': booking.drop_address or '',
                        'Flight/Train Number': booking.flight_train_number or '',
                        'Dispatch center': booking.dispatch_center or 'Central Dispatch',
                        'Remarks': booking.remarks or f'Extracted by {result.extraction_method}',
                        'Labels': booking.labels or ''
                    }
                    booking_records.append(record)
                
                import pandas as pd
                df = pd.DataFrame(booking_records) if booking_records else pd.DataFrame()
                
                return ExtractionResult(
                    success=True,
                    bookings_dataframe=df,
                    booking_count=len(result.bookings),
                    confidence_score=result.confidence_score,
                    processing_time=0.1,  # Approximate processing time
                    cost_inr=0.0,  # Textract cost not tracked in this interface
                    extraction_method=result.extraction_method,
                    error_message=None,
                    metadata={
                        'processor_used': 'EnhancedMultiBookingProcessor',
                        'textract_based': True,
                        'original_processing_notes': result.processing_notes
                    }
                )
                
            except Exception as e:
                logger.error(f"EnhancedMultiBookingProcessor failed: {e}")
                # Fall back to extract method if available
                if hasattr(self.multiple_agent, 'extract'):
                    return self.multiple_agent.extract(content, classification_result)
                else:
                    raise e
        else:
            # Unknown agent type - try extract method as last resort
            logger.warning("Unknown multiple agent type - trying extract method")
            if hasattr(self.multiple_agent, 'extract'):
                return self.multiple_agent.extract(content, classification_result)
            else:
                raise ValueError(f"Multiple agent has no usable extraction method: {type(self.multiple_agent)}")
    
    def _create_textract_result(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """Create extraction result from pre-processed Textract content"""
        
        logger.info("Creating result from pre-processed Textract multi-booking content")
        
        # Parse the TABLE EXTRACTION RESULTS format
        booking_records = []
        
        # Extract booking information from the formatted text
        import re
        
        # Find all booking sections
        booking_pattern = r'Booking (\d+):\s*([\s\S]*?)(?=\nBooking \d+:|\n\nOriginal processing method:|$)'
        matches = re.findall(booking_pattern, content)
        
        for booking_num, booking_content in matches:
            record = {
                'Customer': 'Corporate Client',
                'Booked By Name': 'Travel Coordinator',
                'Booked By Phone Number': '',
                'Booked By Email': '',
                'Passenger Name': '',
                'Passenger Phone Number': '',
                'Passenger Email': '',
                'From (Service Location)': '',
                'To': '',
                'Vehicle Group': '',
                'Duty Type': 'P2P',
                'Start Date': '',
                'End Date': '',
                'Rep. Time': '',
                'Reporting Address': '',
                'Drop Address': '',
                'Flight/Train Number': '',
                'Dispatch center': 'Central Dispatch',
                'Remarks': f'Extracted from TABLE EXTRACTION RESULTS - Booking {booking_num}',
                'Labels': ''
            }
            
            # Parse individual fields from booking content
            field_patterns = {
                'Passenger Name': r'- Passenger: ([^\n(]+)',
                'Passenger Phone Number': r'\(([\d\s]+)\)',
                'Customer': r'- Company: ([^\n]+)',
                'Start Date': r'- Date: ([^\n]+)',
                'Rep. Time': r'- Time: ([^\n]+)',
                'Vehicle Group': r'- Vehicle: ([^\n]+)',
                'Reporting Address': r'- From: ([^\n]+)',
                'Drop Address': r'- To: ([^\n]+)',
                'Flight/Train Number': r'- Flight: ([^\n]+)'
            }
            
            for field, pattern in field_patterns.items():
                match = re.search(pattern, booking_content)
                if match:
                    value = match.group(1).strip()
                    if value and value != 'N/A':
                        record[field] = value
            
            booking_records.append(record)
        
        # Create DataFrame
        import pandas as pd
        df = pd.DataFrame(booking_records) if booking_records else pd.DataFrame()
        
        logger.info(f"Created {len(booking_records)} booking records from Textract content")
        
        return ExtractionResult(
            success=True,
            bookings_dataframe=df,
            booking_count=len(booking_records),
            confidence_score=0.95,  # High confidence since it's from Textract
            processing_time=0.05,  # Very fast since it's just parsing
            cost_inr=0.0,  # No additional cost
            extraction_method="textract_preprocessed",
            error_message=None,
            metadata={
                'processor_used': 'EnhancedMultiBookingProcessor',
                'textract_based': True,
                'preprocessing_detected': True,
                'original_booking_count': classification_result.booking_count
            }
        )
    
    def _fallback_extraction(self, content: str, classification_result: ClassificationResult) -> ExtractionResult:
        """Fallback extraction when routing fails"""
        
        logger.warning("Using fallback extraction routing")
        
        # Try single agent first as fallback
        if self.single_agent:
            logger.info("Fallback: Using single booking agent")
            return self.single_agent.extract(content, classification_result)
        
        # Try multiple agent as last resort
        elif self.multiple_agent:
            logger.info("Fallback: Using multiple booking agent")
            return self.multiple_agent.extract(content, classification_result)
        
        else:
            raise ValueError("No extraction agents available for fallback")
    
    def _get_agent_name(self, booking_type: BookingType) -> str:
        """Get agent name for booking type"""
        return {
            BookingType.SINGLE: "SingleBookingExtractionAgent",
            BookingType.MULTIPLE: "MultipleBookingExtractionAgent"
        }.get(booking_type, "FallbackAgent")
    
    def _update_stats(self, result: ExtractionResult):
        """Update routing statistics"""
        
        if result.success:
            self.routing_stats['successful_extractions'] += 1
        else:
            self.routing_stats['failed_extractions'] += 1
        
        self.routing_stats['total_cost_inr'] += result.cost_inr
        self.routing_stats['total_processing_time'] += result.processing_time
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        
        stats = self.routing_stats.copy()
        
        # Add derived statistics
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_extractions'] / stats['total_requests']
            stats['avg_cost_per_request'] = stats['total_cost_inr'] / stats['total_requests']
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['avg_cost_per_request'] = 0.0
            stats['avg_processing_time'] = 0.0
        
        # Add agent statistics
        if self.single_agent:
            stats['single_agent_stats'] = self.single_agent.get_cost_summary()
        
        if self.multiple_agent:
            stats['multiple_agent_stats'] = self.multiple_agent.get_cost_summary()
        
        return stats
    
    def reset_stats(self):
        """Reset routing statistics"""
        self.routing_stats = {
            'total_requests': 0,
            'single_booking_requests': 0,
            'multiple_booking_requests': 0,
            'fallback_requests': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_cost_inr': 0.0,
            'total_processing_time': 0.0
        }
        logger.info("Routing statistics reset")

# Test function
def test_extraction_router():
    """Test the extraction router with both single and multiple booking scenarios"""
    
    print("🧪 Testing Extraction Router...")
    
    # Initialize router
    router = ExtractionRouter()
    
    print("📊 Testing single booking routing...")
    
    # Test 1: Single booking
    single_content = """
    Dear Team,
    Please arrange a car for Mr. John Doe (9876543210) tomorrow at 10:00 AM.
    From: Mumbai Office to Mumbai Airport
    Vehicle: Dzire preferred
    Corporate: ABC Company
    """
    
    from gemma_classification_agent import BookingType, DutyType, ClassificationResult
    
    single_classification = ClassificationResult(
        booking_type=BookingType.SINGLE,
        booking_count=1,
        confidence_score=0.9,
        reasoning="Single airport drop booking",
        detected_duty_type=DutyType.DROP_4_40,
        detected_dates=["2024-12-25"],
        detected_vehicles=["Dzire"],
        detected_drops=["Mumbai Airport"]
    )
    
    try:
        single_result = router.route_and_extract(single_content, single_classification)
        print(f"✅ Single booking result: {single_result.success}")
        print(f"📊 Bookings: {single_result.booking_count}")
        print(f"🔧 Method: {single_result.extraction_method}")
        print(f"💰 Cost: ₹{single_result.cost_inr:.4f}")
        
        if single_result.success:
            df = single_result.bookings_dataframe
            print(f"📋 DataFrame shape: {df.shape}")
            if not df.empty:
                print(f"👤 Passenger: {df.iloc[0]['Passenger Name']}")
        
    except Exception as e:
        print(f"❌ Single booking test failed: {str(e)}")
    
    print("\n" + "="*80)
    print("📊 Testing multiple booking routing...")
    
    # Test 2: Multiple bookings
    multiple_content = """
    Multiple bookings required:
    
    1. John Smith (9876543210) - 25th Dec - Delhi to Gurgaon - Dzire
    2. Mary Wilson (9876543211) - 26th Dec - Mumbai to Pune - Innova  
    3. Peter Kumar (9876543212) - 27th Dec - Bangalore to Airport - Crysta
    
    Corporate: TechCorp India
    """
    
    multiple_classification = ClassificationResult(
        booking_type=BookingType.MULTIPLE,
        booking_count=3,
        confidence_score=0.9,
        reasoning="Multiple bookings - separate passengers and dates",
        detected_duty_type=DutyType.DISPOSAL_8_80,
        detected_dates=["2024-12-25", "2024-12-26", "2024-12-27"],
        detected_vehicles=["Dzire", "Innova", "Crysta"],
        detected_drops=["Gurgaon", "Pune", "Airport"]
    )
    
    try:
        multiple_result = router.route_and_extract(multiple_content, multiple_classification)
        print(f"✅ Multiple booking result: {multiple_result.success}")
        print(f"📊 Bookings: {multiple_result.booking_count}")
        print(f"🔧 Method: {multiple_result.extraction_method}")
        print(f"💰 Cost: ₹{multiple_result.cost_inr:.4f}")
        
        if multiple_result.success:
            df = multiple_result.bookings_dataframe
            print(f"📋 DataFrame shape: {df.shape}")
            if not df.empty:
                for i in range(min(3, len(df))):
                    print(f"👤 Booking {i+1}: {df.iloc[i]['Passenger Name']}")
        
    except Exception as e:
        print(f"❌ Multiple booking test failed: {str(e)}")
    
    # Display routing statistics
    print("\n" + "="*80)
    print("📈 Routing Statistics:")
    
    stats = router.get_routing_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Single booking requests: {stats['single_booking_requests']}")
    print(f"Multiple booking requests: {stats['multiple_booking_requests']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    print(f"Average cost per request: ₹{stats['avg_cost_per_request']:.4f}")
    print(f"Average processing time: {stats['avg_processing_time']:.2f}s")
    
    if 'single_agent_stats' in stats:
        print(f"\n🔹 Single Agent: {stats['single_agent_stats']['total_requests']} requests")
    
    if 'multiple_agent_stats' in stats:
        print(f"🔸 Multiple Agent: {stats['multiple_agent_stats']['total_requests']} requests")

if __name__ == "__main__":
    test_extraction_router()