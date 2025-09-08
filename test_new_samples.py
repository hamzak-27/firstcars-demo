#!/usr/bin/env python3
"""
Test the Car Rental AI Agent with new email samples
"""

import os
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using system environment variables only.")

from car_rental_ai_agent import CarRentalAIAgent

def test_new_email_samples():
    """Test the agent with the new email samples provided"""
    
    # New email samples for testing
    new_email_samples = [
        # Email 1 - Nisha's Mumbai drop
        """Hi Team,

Required a sedan cab today to drop at home address( Miraroad, Mumbai).

Flight No: AI2678
Pickup time: 10:50 AM.


Regards,
Nisha""",
        
        # Email 2 - Vinod Kumar Bangalore Airport
        """Dear First Car Team

 

Pls book

 

Innova

 

Guest : Mr. Vinod Kumar (Mobile - +91 98880 41305)


6 September, 2025

Pick up time : 1130 AM

Pick up Venue : Bangalore Airport

Drop at : M S Ramaiah, Bangalore

 

2  6E6634 Y 06SEP 6 IXCBLR GK1  0825 1130  06SEP     BUL14L""",
        
        # Email 3 - Prabhjot Indore
        """Hi,

 

Kindly book cab as per details below

 

Date:  6th Sept 

Car Type: Dzire

City: Indore

Pickup Time: 8 AM Fair Field Marriot hotel

Duty : 8hrs 



Regard 

Prabhjot

9999699815""",
        
        # Email 4 - Chennai Airport transfer
        """Team - Please confirm the booking as below. 
 

Reservation 1:

City : Chennai

Type : Etios or similar 

Date :5th September 2025

Pick up Time :07:00 PM

Pick up : Chennai airport 

Flight : 598 from Hyd 

Drop: E303, Landmark Geethanjali apartments, 100ft road, Anna nagar west, Chennai 

Usage : Airport transfers"""
    ]
    
    # Initialize agent
    try:
        agent = CarRentalAIAgent()
        
        print("=" * 80)
        print("TESTING CAR RENTAL AI AGENT - NEW EMAIL SAMPLES")
        print("=" * 80)
        
        # Process all new email samples
        results = agent.extract_multiple_emails(new_email_samples)
        
        for i, (booking, validation) in enumerate(results, 1):
            print(f"\n{'='*60}")
            print(f"EMAIL {i} RESULTS")
            print(f"{'='*60}")
            
            # Show original email (truncated)
            original_email = new_email_samples[i-1].strip()[:150] + "..." if len(new_email_samples[i-1]) > 150 else new_email_samples[i-1].strip()
            print(f"\nORIGINAL EMAIL:")
            print(f"{original_email}")
            print(f"\n{'-'*40}")
            
            print(f"\nEXTRACTED DATA:")
            extracted_data = booking.to_dict()
            
            # Show key fields in a formatted way
            key_fields = [
                ('Passenger Name', 'passenger_name'),
                ('Phone', 'passenger_phone'),
                ('Corporate', 'corporate'),
                ('Start Date', 'start_date'),
                ('Reporting Time', 'reporting_time'),
                ('Vehicle Type', 'vehicle_group'),
                ('From Location', 'from_location'),
                ('To Location', 'to_location'),
                ('Reporting Address', 'reporting_address'),
                ('Drop Address', 'drop_address'),
                ('Flight/Train', 'flight_train_number'),
                ('Duty Type', 'duty_type'),
                ('Remarks', 'remarks'),
                ('Confidence Score', 'confidence_score')
            ]
            
            for display_name, field_name in key_fields:
                value = extracted_data.get(field_name)
                if value:
                    if field_name == 'confidence_score':
                        print(f"• {display_name}: {value:.1%}")
                    else:
                        print(f"• {display_name}: {value}")
            
            print(f"\nVALIDATION:")
            print(f"• Valid: {validation['is_valid']}")
            print(f"• Quality Score: {validation['quality_score']:.1%}")
            if validation.get('missing_critical'):
                print(f"• Missing Critical: {validation['missing_critical']}")
            if validation.get('warnings'):
                print(f"• Warnings: {validation['warnings']}")
            
            print(f"\nSHEETS ROW FORMAT:")
            sheets_row = booking.to_sheets_row()
            # Show non-empty fields only
            non_empty = [(i, field) for i, field in enumerate(sheets_row) if field.strip()]
            if non_empty:
                for idx, field in non_empty[:10]:  # Show first 10 non-empty fields
                    print(f"  [{idx}]: {field}")
                if len(non_empty) > 10:
                    print(f"  ... and {len(non_empty) - 10} more fields")
        
        # Summary statistics
        total_emails = len(results)
        valid_emails = sum(1 for _, v in results if v['is_valid'])
        avg_quality = sum(v['quality_score'] for _, v in results) / total_emails
        avg_confidence = sum(b.confidence_score or 0 for b, _ in results) / total_emails
        
        print(f"\n{'='*60}")
        print("SUMMARY STATISTICS")
        print(f"{'='*60}")
        print(f"Total Emails Processed: {total_emails}")
        print(f"Valid Extractions: {valid_emails}/{total_emails} ({valid_emails/total_emails:.1%})")
        print(f"Average Quality Score: {avg_quality:.1%}")
        print(f"Average Confidence: {avg_confidence:.1%}")
        
        # Cost estimation
        estimated_cost_per_email = 0.014  # Rough estimate based on token usage
        print(f"\nCOST ESTIMATION:")
        print(f"Estimated cost per email: ~${estimated_cost_per_email:.3f}")
        print(f"Total cost for this test: ~${estimated_cost_per_email * total_emails:.3f}")
        
        return results
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        print("Make sure to set OPENAI_API_KEY environment variable or check your .env file")
        return None

if __name__ == "__main__":
    # Run the test
    test_new_email_samples()
