# Internship Updater

This repository contains a Python script that fetches internship details from a GitHub repository, filters them based on a salary threshold, and appends the filtered data to a Google Sheet. The script is set up to run automatically using GitHub Actions. If the salary of an internship cannot be found, it is added to the google sheet with asterisks.

## Setup Instructions

Follow these steps to set up the project on your own GitHub account:

### 1. Make the Google Sheet

1. Go to the following [Google Sheet](https://docs.google.com/spreadsheets/d/1F7P3qVb8OLyy_tnA9LNKzF5iGTd9tZBjePP-HmX4PCI/edit?gid=0#gid=0)
2. Click the second tab on the bottom to view the "How To" sheet, which has the instructions for cloning the sheet.
3. Follow all of those steps, and take note of the google sheet ID for your new personal sheet (the copy).
4. The Google Sheet ID is the long string of letters and numbers between /d/ and /edit in the URL (for example, in the URL https://docs.google.com/spreadsheets/d/abcd/edit?gid=0#gid=0 the Google Sheet ID is "abcd").

### 2. Fork the Repository

1. Go to the [Internship Updater repository](https://github.com/abennur33/Internship-Updater).
2. Click on the "Fork" button at the top right to create a copy of this repository in your own GitHub account.

### 3. Set Up Google Sheets API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the Google Sheets API and Google Drive API for your project.
4. Create a service account and download the JSON key file.
5. Rename the JSON key file to `service_account.json`.
6. Upload the `service_account.json` file to the root directory of your forked GitHub repository.

### 4. Configure GitHub Secrets

1. Go to your forked repository on GitHub.
2. Click on "Settings" > "Secrets and variables" > "Actions".
3. Click on "New repository secret" and add the following secrets:
   - `TOKEN`: Your GitHub personal access token.
   - `GOOGLE_SHEET_ID`: The ID of your Google Sheet.
   
### 5. Update `updater.py`

1. Open the `updater.py` file in your repository.
2. Replace `'YOUR_FILE_NAME_HERE'` with the name of your service account JSON file (`service_account.json`).
3. Replace the value of `salary_threshold` to the salary threshold you want to set (defaults to 40).

### 6. Configure GitHub Actions Workflow

The GitHub Actions workflow is already configured to run the script daily at 11:50 PM CST. The configuration is defined in the `.github/workflows/schedule.yaml` file.


## Environment Variables

Make sure you have set the following environment variables as GitHub secrets:

- `TOKEN`: Your GitHub personal access token.
- `GOOGLE_SHEET_ID`: The ID of your Google Sheet.

## Dependencies

The required Python packages are listed in the `requirements.txt` file and are configured to automatically download every time you run the github action within `schedule.yaml`:

```plaintext
requests
pandas
selenium
beautifulsoup4
gspread
oauth2client
```

## File Structure

Your repository should have the following structure:

```
.
├── .github
│   └── workflows
│       └── schedule.yaml
├── geckodriver
├── updater.py
├── requirements.txt
└── service_account.json
```

- The script is scheduled to run daily at 11:50 PM CST. You can change the schedule by modifying the `cron` expression in `.github/workflows/schedule.yaml`.
- Ensure that your Google Sheet is shared with the service account email found in your `service_account.json` file.

By following these steps, you should have a fully functional setup that automatically updates your Google Sheet with filtered internship roles every day.
```
