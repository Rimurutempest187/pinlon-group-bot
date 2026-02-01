from googleapiclient.discovery import build
from google.oauth2 import service_account
import config
import datetime

def get_upcoming_events():
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    creds = service_account.Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS, scopes=SCOPES
    )
    service = build('calendar', 'v3', credentials=creds)

    now = datetime.datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId=config.GOOGLE_CALENDAR_ID,
        timeMin=now,
        maxResults=10,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])
