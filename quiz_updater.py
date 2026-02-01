import gspread
from google.oauth2.service_account import Credentials
import config
import random

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def fetch_quizzes():
    creds = Credentials.from_service_account_file(config.GOOGLE_CREDENTIALS, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(config.GOOGLE_SHEET_ID).sheet1
    data = sheet.get_all_records()  # [{'Question':..., 'Answer':...}]
    for d in data:
        d['Answer'] = d['Answer'][:10]  # max 10-char
    return data

def get_random_quiz():
    quizzes = fetch_quizzes()
    return random.choice(quizzes)
