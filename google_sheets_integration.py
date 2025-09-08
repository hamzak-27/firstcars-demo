#!/usr/bin/env python3
"""
Google Sheets Integration for FirstCars Demo Tool
Handles saving booking data to Google Sheets using Google Apps Script
"""

import json
import requests
import streamlit as st
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Apps Script configuration
DEFAULT_APPS_SCRIPT_URL = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"

class AppsScriptSheetsManager:
    """Manages Google Sheets operations via Google Apps Script"""
    
    def __init__(self):
        """Initialize Apps Script client"""
        self.apps_script_url = self._get_apps_script_url()
        self.is_connected = False
    
    def _get_apps_script_url(self):
        """Get Apps Script URL from secrets or environment"""
        try:
            # Try Streamlit secrets first
            return st.secrets["APPS_SCRIPT_URL"]
        except (KeyError, FileNotFoundError):
            # Fallback to environment variable
            import os
            url = os.getenv('APPS_SCRIPT_URL')
            if url:
                return url
            
            logger.warning("Apps Script URL not found in secrets or environment")
            return DEFAULT_APPS_SCRIPT_URL
    
    def _make_request(self, action, data=None, method='POST'):
        """Make HTTP request to Apps Script"""
        try:
            payload = {'action': action}
            if data:
                payload.update(data)
            
            if method == 'POST':
                response = requests.post(
                    self.apps_script_url,
                    json=payload,
                    timeout=30
                )
            else:
                response = requests.get(
                    f"{self.apps_script_url}?action={action}",
                    timeout=30
                )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            return {'success': False, 'message': f'Request failed: {str(e)}'}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {'success': False, 'message': f'Invalid response format: {str(e)}'}
    
    def initialize_headers(self):
        """Initialize Google Sheets with column headers"""
        try:
            result = self._make_request('initialize_headers')
            if result.get('success'):
                logger.info("Headers initialized in Google Sheets")
                return True
            else:
                logger.error(f"Failed to initialize headers: {result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize headers: {str(e)}")
            return False
    
    def append_booking_data(self, bookings_list):
        """
        Append booking data to Google Sheets via Apps Script
        
        Args:
            bookings_list: List of BookingExtraction objects
            
        Returns:
            tuple: (success: bool, message: str, total_rows: int)
        """
        try:
            # Convert BookingExtraction objects to dictionaries
            bookings_data = []
            for booking in bookings_list:
                booking_dict = {
                    'corporate': booking.corporate,
                    'booked_by_name': booking.booked_by_name,
                    'booked_by_phone': booking.booked_by_phone,
                    'booked_by_email': booking.booked_by_email,
                    'passenger_name': booking.passenger_name,
                    'passenger_phone': booking.passenger_phone,
                    'passenger_email': booking.passenger_email,
                    'from_location': booking.from_location,
                    'to_location': booking.to_location,
                    'vehicle_group': booking.vehicle_group,
                    'duty_type': booking.duty_type,
                    'start_date': booking.start_date,
                    'end_date': booking.end_date,
                    'reporting_time': booking.reporting_time,
                    'drop_time': booking.drop_time,
                    'start_from_garage': booking.start_from_garage,
                    'reporting_address': booking.reporting_address,
                    'drop_address': booking.drop_address,
                    'flight_train_number': booking.flight_train_number,
                    'dispatch_center': booking.dispatch_center,
                    'bill_to': booking.bill_to,
                    'price': booking.price,
                    'remarks': booking.remarks,
                    'labels': booking.labels,
                    'confidence_score': booking.confidence_score
                }
                bookings_data.append(booking_dict)
            
            # Make request to Apps Script
            result = self._make_request('append_data', {'bookings': bookings_data})
            
            if result.get('success'):
                data = result.get('data', {})
                total_rows = data.get('total_rows', 0)
                logger.info(f"Successfully saved {len(bookings_list)} booking(s) to Google Sheets")
                return True, result.get('message', 'Success'), total_rows
            else:
                error_message = result.get('message', 'Unknown error')
                logger.error(f"Failed to save to Google Sheets: {error_message}")
                return False, error_message, 0
            
        except Exception as e:
            error_message = f"Failed to save to Google Sheets: {str(e)}"
            logger.error(error_message)
            return False, error_message, 0
    
    def get_sheet_info(self):
        """Get information about the Google Sheet via Apps Script"""
        try:
            result = self._make_request('get_sheet_info')
            
            if result.get('success'):
                data = result.get('data', {})
                return {
                    "total_rows": data.get('total_rows', 0),
                    "sheet_title": data.get('sheet_title', 'Unknown'),
                    "worksheet_title": data.get('worksheet_title', 'Unknown'),
                    "sheet_url": data.get('sheet_url', '')
                }
            else:
                logger.error(f"Failed to get sheet info: {result.get('message')}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to get sheet info: {str(e)}")
            return None
    
    def test_connection(self):
        """Test the Apps Script connection"""
        try:
            result = self._make_request('test_connection', method='GET')
            
            if result.get('success'):
                message = result.get('message', 'Connection successful')
                self.is_connected = True
                return True, message
            else:
                error_message = result.get('message', 'Connection failed')
                self.is_connected = False
                return False, error_message
            
        except Exception as e:
            self.is_connected = False
            return False, f"Connection failed: {str(e)}"

# Global instance
sheets_manager = AppsScriptSheetsManager()
