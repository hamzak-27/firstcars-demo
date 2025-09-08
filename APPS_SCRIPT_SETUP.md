# Google Apps Script Setup Guide

This guide will help you set up Google Apps Script to integrate with your FirstCars Demo Tool.

## Step 1: Create Google Apps Script Project

1. Go to [script.google.com](https://script.google.com)
2. Click "New Project"
3. Delete the default code
4. Copy and paste the code from `apps_script_code.gs`

## Step 2: Configure the Script

1. In the Apps Script editor, update the configuration at the top:
   ```javascript
   const SHEET_ID = '1zz1xkvI0-XCkU23eBfSW9jSLK--UfCU94iT-poEkf_E';  // Your sheet ID
   const SHEET_NAME = 'Sheet1';  // Your sheet name
   ```

2. Save the project (Ctrl+S or Cmd+S)

## Step 3: Test the Script

1. In the Apps Script editor, select the `testFunction` function
2. Click the "Run" button to test
3. Grant necessary permissions when prompted
4. Check the execution log for any errors

## Step 4: Deploy as Web App

1. Click "Deploy" → "New deployment"
2. Choose "Web app" as the type
3. Set the following options:
   - **Execute as**: Me (your email)
   - **Who has access**: Anyone
4. Click "Deploy"
5. **Copy the Web App URL** - you'll need this for Streamlit

## Step 5: Configure Streamlit Secrets

### For Local Development:
Create/update your `.env` file:
```
APPS_SCRIPT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

### For Streamlit Cloud Deployment:
In your Streamlit Cloud dashboard:
1. Go to your app settings
2. Click "Secrets"
3. Add:
```toml
APPS_SCRIPT_URL = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"
```

## Step 6: Test the Integration

1. Run your Streamlit app
2. Try processing an email
3. Click "Save to Google Sheets"
4. Check your Google Sheet to see if data was added

## Troubleshooting

### Common Issues:

1. **"Script not found" error**
   - Make sure the Web App URL is correct
   - Ensure the script is deployed as a web app

2. **Permission denied**
   - Check that "Who has access" is set to "Anyone"
   - Re-deploy the script if needed

3. **Sheet not found**
   - Verify the SHEET_ID in your Apps Script
   - Make sure the sheet is accessible

### Testing the Apps Script Directly:

You can test the Apps Script by visiting the URL in your browser:
```
https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec?action=test
```

This should return a JSON response indicating success.

## Security Notes

- The Apps Script runs with your Google account permissions
- Only share the Web App URL with trusted applications
- Monitor your Google Apps Script usage in the Google Cloud Console

## Next Steps

Once everything is working:
1. Update your Streamlit app's secrets with the correct URL
2. Deploy your Streamlit app to Streamlit Cloud
3. Test the complete flow from Streamlit to Google Sheets

Your FirstCars Demo Tool is now integrated with Google Sheets via Apps Script! 🎉
