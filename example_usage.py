"""
Example usage of the Car Rental AI Agent
Shows how to use the agent for extracting data from emails
"""

import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using system environment variables only.")

from car_rental_ai_agent import CarRentalAIAgent

def main():
    """Example usage of the AI agent"""
    
    # Set your OpenAI API key
    # You can either set it as an environment variable: OPENAI_API_KEY
    # Or pass it directly when initializing the agent
    
    # Method 1: Using environment variable (recommended)
    # os.environ['OPENAI_API_KEY'] = 'your-api-key-here'
    # agent = CarRentalAIAgent()
    
    # Method 2: Pass directly
    # agent = CarRentalAIAgent(openai_api_key='your-api-key-here')
    
    try:
        # Initialize agent
        agent = CarRentalAIAgent()
        
        # Sample email content
        sample_email = """
        Dear Team,
        Kindly arrange a cab on 27th Aug,
        Name -Nasimsha Nasarulla
        Date-27th Aug, Wednesday 
        Location - Mather Berrywoods, Chembumukku,Cochin
        Time- 7.30am
        Cab Type-Dzire
        Duty- Local Disposal 
        mob- 7358593915
        """
        
        print("Processing email...")
        print("-" * 50)
        print(sample_email)
        print("-" * 50)
        
        # Extract booking data
        booking = agent.extract_booking_data(sample_email)
        
        # Validate the extraction
        validation = agent.validate_extraction(booking)
        
        # Display results
        print("\nEXTRACTED BOOKING DATA:")
        print(f"Passenger Name: {booking.passenger_name}")
        print(f"Phone: {booking.passenger_phone}")
        print(f"Date: {booking.start_date}")
        print(f"Time: {booking.reporting_time}")
        print(f"Vehicle: {booking.vehicle_group}")
        print(f"Address: {booking.reporting_address}")
        print(f"Confidence: {booking.confidence_score:.2%}")
        
        print(f"\nVALIDATION:")
        print(f"Valid: {validation['is_valid']}")
        print(f"Quality Score: {validation['quality_score']:.1%}")
        print(f"Missing Critical Fields: {validation['missing_critical']}")
        
        if validation['warnings']:
            print(f"Warnings: {validation['warnings']}")
        
        print(f"\nREASONING:")
        print(booking.extraction_reasoning[:200] + "..." if len(booking.extraction_reasoning or "") > 200 else booking.extraction_reasoning)
        
        print(f"\nGOOGLE SHEETS ROW FORMAT:")
        print(booking.to_sheets_row())
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Make sure to set your OPENAI_API_KEY environment variable")

if __name__ == "__main__":
    main()
