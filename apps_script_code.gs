/**
 * Google Apps Script for FirstCars Demo Tool
 * Handles HTTP requests from Streamlit app and writes data to Google Sheets
 * 
 * Instructions:
 * 1. Go to script.google.com
 * 2. Create a new project
 * 3. Paste this code
 * 4. Deploy as a web app with execute permissions for "Anyone"
 * 5. Copy the web app URL and use it in your Streamlit app
 */

// Configuration - UPDATE THESE VALUES
const SHEET_ID = '1zz1xkvI0-XCkU23eBfSW9jSLK--UfCU94iT-poEkf_E';
const SHEET_NAME = 'Sheet1';

// Column headers for the sheet
const HEADERS = [
  'Corporate', 'Booked By Name', 'Booked By Phone', 'Booked By Email',
  'Passenger Name', 'Passenger Phone', 'Passenger Email',
  'From Location', 'To Location', 'Vehicle Group', 'Duty Type',
  'Start Date', 'End Date', 'Reporting Time', 'Drop Time',
  'Start From Garage', 'Reporting Address', 'Drop Address',
  'Flight/Train Number', 'Dispatch Center', 'Bill To', 'Price',
  'Remarks', 'Labels', 'Timestamp', 'Confidence Score'
];

/**
 * Main function to handle HTTP requests
 */
function doPost(e) {
  try {
    // Parse the incoming data
    const data = JSON.parse(e.postData.contents);
    
    // Handle different actions
    switch (data.action) {
      case 'append_data':
        return appendData(data.bookings);
      case 'test_connection':
        return testConnection();
      case 'get_sheet_info':
        return getSheetInfo();
      case 'initialize_headers':
        return initializeHeaders();
      default:
        return createResponse(false, 'Unknown action: ' + data.action);
    }
    
  } catch (error) {
    console.error('Error in doPost:', error);
    return createResponse(false, 'Error processing request: ' + error.message);
  }
}

/**
 * Handle GET requests for testing
 */
function doGet(e) {
  try {
    const action = e.parameter.action || 'test';
    
    if (action === 'test') {
      return testConnection();
    } else if (action === 'info') {
      return getSheetInfo();
    }
    
    return createResponse(true, 'FirstCars Apps Script is running');
    
  } catch (error) {
    return createResponse(false, 'Error: ' + error.message);
  }
}

/**
 * Append booking data to the sheet
 */
function appendData(bookings) {
  try {
    const sheet = getSheet();
    
    // Initialize headers if the sheet is empty
    if (sheet.getLastRow() === 0) {
      initializeHeaders();
    }
    
    // Prepare rows for insertion
    const rows = [];
    const timestamp = new Date().toLocaleString('en-US', {
      timeZone: 'Asia/Kolkata',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    
    bookings.forEach(booking => {
      const row = [
        booking.corporate || '',
        booking.booked_by_name || '',
        booking.booked_by_phone || '',
        booking.booked_by_email || '',
        booking.passenger_name || '',
        booking.passenger_phone || '',
        booking.passenger_email || '',
        booking.from_location || '',
        booking.to_location || '',
        booking.vehicle_group || '',
        booking.duty_type || '',
        booking.start_date || '',
        booking.end_date || '',
        booking.reporting_time || '',
        booking.drop_time || '',
        booking.start_from_garage || '',
        booking.reporting_address || '',
        booking.drop_address || '',
        booking.flight_train_number || '',
        booking.dispatch_center || '',
        booking.bill_to || '',
        booking.price || '',
        booking.remarks || '',
        booking.labels || '',
        timestamp,
        booking.confidence_score ? booking.confidence_score.toFixed(2) : ''
      ];
      rows.push(row);
    });
    
    // Append rows to the sheet
    if (rows.length > 0) {
      const range = sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, HEADERS.length);
      range.setValues(rows);
    }
    
    const totalRows = sheet.getLastRow() - 1; // Subtract header row
    
    return createResponse(true, `Successfully saved ${bookings.length} booking(s)`, {
      total_rows: totalRows,
      bookings_added: bookings.length
    });
    
  } catch (error) {
    console.error('Error in appendData:', error);
    return createResponse(false, 'Failed to append data: ' + error.message);
  }
}

/**
 * Test connection to the sheet
 */
function testConnection() {
  try {
    const sheet = getSheet();
    const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
    
    return createResponse(true, `Connected to "${spreadsheet.getName()}" -> "${sheet.getName()}"`, {
      sheet_title: spreadsheet.getName(),
      worksheet_title: sheet.getName(),
      sheet_id: SHEET_ID
    });
    
  } catch (error) {
    console.error('Error in testConnection:', error);
    return createResponse(false, 'Connection failed: ' + error.message);
  }
}

/**
 * Get information about the sheet
 */
function getSheetInfo() {
  try {
    const sheet = getSheet();
    const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
    const totalRows = Math.max(0, sheet.getLastRow() - 1); // Subtract header row
    
    return createResponse(true, 'Sheet info retrieved', {
      total_rows: totalRows,
      sheet_title: spreadsheet.getName(),
      worksheet_title: sheet.getName(),
      sheet_url: spreadsheet.getUrl(),
      last_updated: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error in getSheetInfo:', error);
    return createResponse(false, 'Failed to get sheet info: ' + error.message);
  }
}

/**
 * Initialize headers in the sheet
 */
function initializeHeaders() {
  try {
    const sheet = getSheet();
    
    // Check if headers already exist
    if (sheet.getLastRow() > 0) {
      const firstRow = sheet.getRange(1, 1, 1, HEADERS.length).getValues()[0];
      const hasHeaders = firstRow.some(cell => cell !== '');
      if (hasHeaders) {
        return createResponse(true, 'Headers already exist');
      }
    }
    
    // Add headers
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    
    // Format headers
    const headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
    headerRange.setFontWeight('bold');
    headerRange.setBackground('#4285F4');
    headerRange.setFontColor('white');
    
    // Auto-resize columns
    sheet.autoResizeColumns(1, HEADERS.length);
    
    return createResponse(true, 'Headers initialized successfully');
    
  } catch (error) {
    console.error('Error in initializeHeaders:', error);
    return createResponse(false, 'Failed to initialize headers: ' + error.message);
  }
}

/**
 * Helper function to get the sheet
 */
function getSheet() {
  try {
    const spreadsheet = SpreadsheetApp.openById(SHEET_ID);
    return spreadsheet.getSheetByName(SHEET_NAME);
  } catch (error) {
    throw new Error(`Cannot access sheet "${SHEET_NAME}" in spreadsheet "${SHEET_ID}": ${error.message}`);
  }
}

/**
 * Helper function to create standardized responses
 */
function createResponse(success, message, data = null) {
  const response = {
    success: success,
    message: message,
    timestamp: new Date().toISOString()
  };
  
  if (data) {
    response.data = data;
  }
  
  return ContentService
    .createTextOutput(JSON.stringify(response))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Test function for manual testing
 */
function testFunction() {
  // Test data
  const testBookings = [{
    passenger_name: 'Test User',
    passenger_phone: '9876543210',
    start_date: '2025-09-08',
    reporting_time: '10:00',
    vehicle_group: 'Swift Dzire',
    reporting_address: 'Test Address',
    confidence_score: 0.85
  }];
  
  const result = appendData(testBookings);
  console.log(result.getContent());
}
