# Deployment Guide: Number Recognition Experiment

This guide will help you deploy your experiment to Streamlit Cloud with Google Sheets integration.

## Step 1: Set Up Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create a new project** (or use existing):
   - Click "Select a project" → "New Project"
   - Name it "Number Recognition Experiment"
   - Click "Create"

## Step 2: Enable Google Sheets API

1. In your Google Cloud project, go to **APIs & Services** → **Library**
2. Search for "Google Sheets API"
3. Click on it and click **Enable**
4. Also enable "Google Drive API" the same way

## Step 3: Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Fill in:
   - Service account name: `experiment-data-writer`
   - Click **Create and Continue**
4. Skip the optional steps and click **Done**

## Step 4: Generate Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create** - a JSON file will download
6. **IMPORTANT**: Keep this file secure! Don't share it publicly

## Step 5: Create Google Sheet

1. Go to Google Sheets: https://docs.google.com/spreadsheets/
2. Create a new blank spreadsheet
3. Name it: **"Number Recognition Results"**
4. **Share the spreadsheet**:
   - Click the "Share" button
   - Copy the `client_email` from the JSON file you downloaded (looks like: `experiment-data-writer@your-project.iam.gserviceaccount.com`)
   - Paste it in the share field
   - Give it **Editor** access
   - Uncheck "Notify people"
   - Click "Share"

## Step 6: Set Up GitHub Repository

1. **Create a GitHub account** if you don't have one: https://github.com/
2. **Create a new repository**:
   - Click "+" → "New repository"
   - Name: `number-recognition-experiment`
   - Make it **Public** (required for free Streamlit Cloud)
   - Click "Create repository"

3. **Push your code to GitHub**:
   ```bash
   cd /Users/dhivya/Desktop/Projects/lita/science_fair
   git init
   git add .
   git commit -m "Initial commit: Number recognition experiment"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/number-recognition-experiment.git
   git push -u origin main
   ```

## Step 7: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io/
2. **Sign in** with your GitHub account
3. Click **"New app"**
4. Fill in:
   - Repository: Select your `number-recognition-experiment` repo
   - Branch: `main`
   - Main file path: `app.py`
5. Click **"Advanced settings"**

## Step 8: Add Google Sheets Credentials to Streamlit

1. In the Advanced settings, you'll see a **Secrets** section
2. Copy the ENTIRE contents of the JSON file you downloaded in Step 4
3. Format it like this in the Secrets box:

```toml
sheet_name = "Number Recognition Results"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id-here"
private_key_id = "your-key-id-here"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-FULL-PRIVATE-KEY-HERE\n-----END PRIVATE KEY-----\n"
client_email = "experiment-data-writer@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

**IMPORTANT**: Replace all the values with the ones from your JSON file!

4. Click **"Deploy"**

## Step 9: Share Your Experiment

1. Once deployed, Streamlit will give you a URL like: `https://your-username-number-recognition-experiment-main.streamlit.app`
2. **Share this URL with your friends!**
3. They can complete the experiment from any device with internet access

## Step 10: View Results

1. **Go to your Google Sheet**: "Number Recognition Results"
2. All participant data will appear here in real-time!
3. You can download the data anytime:
   - File → Download → Comma Separated Values (.csv)
   - Or use Google Sheets for analysis directly

## Troubleshooting

### Error: "Google Sheet not found"
- Make sure you shared the sheet with the service account email
- Check that the sheet name matches exactly: "Number Recognition Results"

### Error: "Permission denied"
- The service account needs Editor access to the sheet
- Re-share the sheet and make sure Editor is selected

### Data not appearing in Google Sheets
- Check if the Google Sheets API and Drive API are enabled
- Verify the credentials are correctly copied in Streamlit secrets
- Check the Streamlit app logs for error messages

### App not deploying
- Make sure requirements.txt is in the repository
- Check that all files are committed and pushed to GitHub
- Look at the deployment logs in Streamlit Cloud for errors

## Local Testing (Optional)

To test locally before deploying:

1. Create `.streamlit/secrets.toml` file (copy from `.streamlit/secrets.toml.example`)
2. Fill in your Google credentials
3. Run: `streamlit run app.py`
4. Test the experiment locally

## Security Notes

- **NEVER** commit `.streamlit/secrets.toml` to GitHub (it's in .gitignore)
- Only add secrets through Streamlit Cloud's web interface
- Keep your service account JSON file secure
- If credentials are exposed, delete the service account and create a new one

## Need Help?

If you run into issues:
1. Check the Streamlit Cloud logs
2. Verify all steps were completed
3. Make sure the Google Sheet is shared with the service account
4. Check that APIs are enabled in Google Cloud

Good luck with your science fair project! 🎉
