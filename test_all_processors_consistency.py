#!/usr/bin/env python3
"""
Test all document processors for consistent duty_type output
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_email_processor import UnifiedEmailProcessor
from car_rental_ai_agent import CarRentalAIAgent
from structured_email_agent import StructuredEmailAgent

def test_all_processors():
    """Test all processors for consistent duty_type format"""
    
    # Test email content
    test_email = """
    From: travel@reliance.com
    Subject: Car booking
    
    Dear Team,
    RELIANCE employee needs airport pickup:
    
    Passenger: Jane Smith
    Phone: 9876543210
    From: Mumbai Airport
    To: Mumbai Office
    Date: Tomorrow
    Time: 2:00 PM
    
    Remarks: Airport pickup service
    """
    
    print("Testing All Processors for Consistent Duty Type Output:")
    print("=" * 70)
    print(f"Test Email:\n{test_email}")
    print("=" * 70)
    
    processors = [
        ("CarRentalAIAgent (Main)", CarRentalAIAgent()),
        ("StructuredEmailAgent", StructuredEmailAgent()),
        ("UnifiedEmailProcessor", UnifiedEmailProcessor())
    ]
    
    for processor_name, processor in processors:
        try:
            print(f"\n🔧 Testing {processor_name}:")
            
            if processor_name == "CarRentalAIAgent (Main)":
                # Direct single booking extraction
                result = processor.extract_booking_data(test_email)
                bookings = [result]
            elif processor_name == "StructuredEmailAgent":
                # Intelligent processing
                result = processor.process_email_intelligently(test_email)
                bookings = result.bookings
            else:  # UnifiedEmailProcessor
                # Unified processing
                result = processor.process_email(test_email)
                bookings = result.bookings
            
            if bookings and bookings[0]:
                booking = bookings[0]
                print(f"  ✅ Corporate: {booking.corporate}")
                print(f"  ✅ Corporate Duty Type: {booking.corporate_duty_type}")
                print(f"  ✅ Duty Type: {booking.duty_type}")
                print(f"  ✅ Recommended Package: {booking.recommended_package}")
                print(f"  ✅ Approval Required: {booking.approval_required}")
                
                # Verify format
                if booking.duty_type and '-' in booking.duty_type:
                    prefix, package = booking.duty_type.split('-', 1)
                    if prefix in ['G2G', 'P2P']:
                        print(f"  ✅ Format: CORRECT - {prefix}-{package}")
                    else:
                        print(f"  ❌ Format: INCORRECT - {booking.duty_type}")
                else:
                    print(f"  ❌ Format: INVALID - {booking.duty_type}")
            else:
                print(f"  ❌ No bookings extracted")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✅ Expected: All processors should show 'P2P-04HR 40KMS' format")
    print("✅ RELIANCE is P2P corporate with airport pickup = P2P-04HR 40KMS")
    print("=" * 70)

if __name__ == "__main__":
    test_all_processors()