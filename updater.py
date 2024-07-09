# send_email.py
import requests
import pandas as pd
from datetime import datetime
import base64
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# GitHub repository details
GITHUB_REPO = 'SimplifyJobs/Summer2025-Internships'
README_PATH = 'README.md'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # Use GitHub secret

# Fetch the README file from GitHub
def fetch_github_readme():
    url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{README_PATH}'
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    content = response.json()
    return base64.b64decode(content['content']).decode('utf-8')

# Parse the README content and extract today's internship roles
def parse_md_file_for_today_jobs(content):
    columns = ["Company", "Role", "Location", "Application/Link", "Date Posted"]
    lines = content.split('\n')
    table_started = False
    data = []
    today = datetime.now().strftime("%b %d")
    print(today)
    lastcompany = ""

    for line in lines:
        if "| ------- | ---- | -------- | ---------------- | ----------- |" in line:
            table_started = True
            continue

        if table_started:
            print(line)
            split_line = [element.strip() for element in line.split('|') if element.strip()]

            if len(split_line) == 0:
                break

            split_line[3] = extract_url(split_line)[3]

            split_line[0] = extract_company_name(split_line[0])

            if (split_line[0] != "↳"):
                lastcompany = split_line[0]
            else:
                split_line[0] = lastcompany

            split_line[2] = strip_html_tags(split_line[2])

            if len(split_line) == len(columns):
                if split_line[-1] == today:
                    data.append(split_line)
                else:
                    break

    df = pd.DataFrame(data, columns=columns)
    return df

def extract_company_name(text):
    match = re.match(r'\[(.*?)\]\(.*?\)', text)
    if match:
        return match.group(1)
    return text

def extract_url(entry):
    url_pattern = re.compile(r'href="(.*?)"')    
    match = url_pattern.search(entry[3])
    if match:
        entry[3] = match.group(1)
    return entry

def strip_html_tags(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator="\n")

def fetch_html_dynamic(url):
    service = Service("geckodriver")
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    
    driver.get(url)
    time.sleep(5)
    html_content = driver.page_source
    driver.quit()
    return html_content

def parse_salary_table(html_content, company_name):
    soup = BeautifulSoup(html_content, 'html.parser')
    rows = soup.find_all('tr', {'data-index': True})
    
    for row in rows:
        company_td = row.find('td', class_='company-name-th')
        if company_td and company_name in ''.join(company_td.get_text(strip=True).split()).lower():
            salary_td = row.find('td', class_='hourly-salary-td')
            if salary_td:
                salary_text_h = salary_td.find('h6', class_='cashInText')
                if salary_text_h:
                    salary_text = salary_text_h.get_text(strip=True)
                    if salary_text == "Add compensation":
                        return "Add compensation"
                    hourly_salary = float(salary_text.split('/')[0].strip('$'))
                    return hourly_salary
    return None

def filter_dataframe_by_salary(df, urls, salary_threshold):
    indices_to_drop = []
    html_contents = [fetch_html_dynamic(url) for url in urls]
    
    for index, row in df.iterrows():
        company_name = row['Company']
        company_name_short = ''.join(company_name.split()).lower()
        hourly_salary = None
        
        for i in range(len(html_contents)):
            hourly_salary = parse_salary_table(html_contents[i], company_name_short)
            if hourly_salary is not None and hourly_salary != "Add compensation":
                break
        
        if hourly_salary is None or hourly_salary == "Add compensation":
            df.at[index, 'Company'] = f"**{company_name}**"
        elif hourly_salary < salary_threshold:
            indices_to_drop.append(index)
    
    df.drop(indices_to_drop, inplace=True)
    return df

# Append the filtered data to Google Sheets
def append_to_google_sheet(df, sheet_id):
    # Set up Google Sheets API credentials
    # Path to the service account JSON file
    SERVICE_ACCOUNT_FILE = 'YOUR_FILE_NAME_HERE'
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    
    # Open the Google Sheet
    sheet = client.open_by_key(sheet_id).worksheet('Tracker')  # Adjust worksheet name if needed
    
    # Find the first empty row
    def first_empty_row(worksheet):
        str_list = list(filter(None, worksheet.col_values(1)))  # Get non-empty values in the first column
        return len(str_list) + 2
    
    start_row = first_empty_row(sheet)
    
    # Prepare the data to append
    rows = []
    for _, row in df.iterrows():
        role = row['Role']
        link = row['Application/Link']
        date_posted = datetime.strptime(row['Date Posted'], '%b %d').strftime('2024-%m-%d')
        formatted_date = datetime.strptime(date_posted, '%Y-%m-%d').strftime('%m/%d/%Y')
        company = row['Company']
        location = row['Location']
        
        # Create a hyperlink for the role
        hyperlink = f'=HYPERLINK("{link}", "{role}")'
        
        rows.append([hyperlink, formatted_date, '', company, location])
    
    # Append the data to the Google Sheet
    cell_list = sheet.range(f'A{start_row}:E{start_row + len(rows) - 1}')
    flat_list = [item for sublist in rows for item in sublist]
    for i, val in enumerate(flat_list):
        cell_list[i].value = val
    
    sheet.update_cells(cell_list, value_input_option='USER_ENTERED')

GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')  # Use GitHub secret
urls = [
    'https://www.levels.fyi/internships/?track=Software%20Engineer&timeframe=Summer%20-%202024',
    'https://www.levels.fyi/internships/?track=Software%20Engineer&timeframe=Summer%20-%202023',
    'https://www.levels.fyi/internships/?track=Software%20Engineer&timeframe=Summer%20-%202022'
]
salary_threshold = 40  # Example threshold

df = parse_md_file_for_today_jobs(fetch_github_readme())
print(df)
if len(df) > 0:
    filtered_df = filter_dataframe_by_salary(df, urls, salary_threshold)
    print(filtered_df)
    append_to_google_sheet(filtered_df, GOOGLE_SHEET_ID)
