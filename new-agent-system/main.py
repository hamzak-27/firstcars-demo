"""
Main Entry Point for Multi-Agent Booking Extraction System
Demonstrates processing of both email content and table images
"""

import os
import logging
import pandas as pd
from typing import Optional

from core.multi_agent_orchestrator import MultiAgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class BookingExtractionSystem:
    """
    Main system class for booking data extraction
    """
    
    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini"):
        """Initialize the booking extraction system"""
        self.orchestrator = MultiAgentOrchestrator(openai_api_key, model)
        logger.info("Booking extraction system initialized")
    
    def process_email(self, email_content: str, sender_email: str = "") -> pd.DataFrame:
        """
        Process unstructured email content
        
        Args:
            email_content: Raw email text content
            sender_email: Optional sender email for company identification
            
        Returns:
            Processed DataFrame with extracted booking data
        """
        logger.info("Processing email content")
        try:
            result_df = self.orchestrator.process_unstructured_email(email_content, sender_email)
            logger.info(f"Email processing completed. {len(result_df)} bookings extracted")
            return result_df
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return pd.DataFrame()
    
    def process_table_image(self, image_path: str) -> pd.DataFrame:
        """
        Process table data from image or PDF
        
        Args:
            image_path: Path to image/PDF file containing table
            
        Returns:
            Processed DataFrame with extracted and enriched booking data
        """
        logger.info(f"Processing table image: {image_path}")
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return pd.DataFrame()
            
            result_df = self.orchestrator.process_table_data(image_path)
            logger.info(f"Table processing completed. {len(result_df)} bookings extracted")
            return result_df
        except Exception as e:
            logger.error(f"Error processing table image: {e}")
            return pd.DataFrame()
    
    def save_results(self, df: pd.DataFrame, output_path: str, include_metadata: bool = True):
        """
        Save processing results to CSV
        
        Args:
            df: Processed DataFrame
            output_path: Path for output CSV file
            include_metadata: Whether to include system metadata
        """
        try:
            if df.empty:
                logger.warning("No data to save - DataFrame is empty")
                return
            
            # Save main data
            df.to_csv(output_path, index=False)
            logger.info(f"Results saved to: {output_path}")
            
            # Save metadata if requested
            if include_metadata:
                metadata_path = output_path.replace('.csv', '_metadata.txt')
                with open(metadata_path, 'w') as f:
                    f.write(f"Multi-Agent Booking Extraction System Results\n")
                    f.write(f"=" * 50 + "\n")
                    f.write(f"Total bookings processed: {len(df)}\n")
                    f.write(f"Columns extracted: {len(df.columns)}\n")
                    f.write(f"Agent system summary: {self.orchestrator.get_processing_summary()}\n")
                    f.write(f"\nColumn list:\n")
                    for i, col in enumerate(df.columns, 1):
                        f.write(f"{i:2d}. {col}\n")
                
                logger.info(f"Metadata saved to: {metadata_path}")
                
        except Exception as e:
            logger.error(f"Error saving results: {e}")

def demo_email_processing(system: BookingExtractionSystem):
    """Demonstrate email processing with sample content"""
    
    sample_email = """
    Subject: Car Service for VIP Guest Visit
    
    Hi,
    
    We need car service for our VIP corporate guest visiting next week:
    
    Guest: Ms. Priya Sharma (VIP guest) from TechCorp
    Contact: priya.s@techcorp.com, +91-9988776655
    Flight: AI 405 arriving at Mumbai airport on Jan 15, 2024 at 2:37 PM
    
    Pickup Instructions:
    1. First pickup at Terminal 2 at 2:30 PM
    2. Then pickup second passenger from Hotel Taj at 4:15 PM  
    3. Finally pickup from office at 6:45 PM
    
    Drop at: Hotel Grand (airport drop service)
    Vehicle: SUV preferred (Toyota Innova if available)
    
    Special Requirements:
    - Driver should speak English and be professional
    - Please ensure AC is working properly
    - Contact passenger 30 minutes before pickup
    - VIP treatment required
    
    Return flight: SG 567 next day
    Rate: Rs. 1800 total
    
    Thanks,
    Sarah Johnson
    TechCorp Travel Desk
    """
    
    sender_email = "sarah.johnson@techcorp.com"
    
    print("\\n" + "="*60)
    print("DEMO: Processing Email Content")
    print("="*60)
    
    result_df = system.process_email(sample_email, sender_email)
    
    if not result_df.empty:
        print(f"\\nExtracted {len(result_df)} bookings:")
        print(result_df.to_string(index=False))
        
        # Save results
        system.save_results(result_df, "demo_email_results.csv")
    else:
        print("No bookings extracted from email")

def demo_table_processing(system: BookingExtractionSystem):
    """Demonstrate table processing (requires image file)"""
    
    print("\\n" + "="*60)
    print("DEMO: Processing Table Image")
    print("="*60)
    
    # Look for sample table images in current directory
    sample_images = [
        "sample_booking_table.png",
        "booking_table.jpg", 
        "table_screenshot.png"
    ]
    
    image_found = None
    for img in sample_images:
        if os.path.exists(img):
            image_found = img
            break
    
    if image_found:
        print(f"Processing image: {image_found}")
        result_df = system.process_table_image(image_found)
        
        if not result_df.empty:
            print(f"\\nExtracted {len(result_df)} bookings:")
            print(result_df.to_string(index=False))
            
            # Save results
            system.save_results(result_df, "demo_table_results.csv")
        else:
            print("No bookings extracted from table")
    else:
        print("No sample table images found.")
        print("To test table processing, place an image file with booking table data in the current directory.")
        print(f"Expected filenames: {', '.join(sample_images)}")

def main():
    """Main function to run the booking extraction system"""
    
    print("Multi-Agent Booking Extraction System")
    print("=" * 50)
    
    # Get OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Initialize system
    try:
        system = BookingExtractionSystem(api_key)
        print(f"System initialized with 6 specialized agents using model: gpt-4o-mini")
        
        # Run demonstrations
        demo_email_processing(system)
        demo_table_processing(system)
        
        print("\\n" + "="*60)
        print("SYSTEM SUMMARY")
        print("="*60)
        summary = system.orchestrator.get_processing_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        print("\\nDemo completed successfully!")
        print("Check the generated CSV files for detailed results.")
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()