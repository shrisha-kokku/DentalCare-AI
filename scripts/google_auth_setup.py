from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.calendarlist.readonly",
]

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
    creds = flow.run_local_server(port=8080)
    print("\nSave this in your .env as GOOGLE_REFRESH_TOKEN:\n")
    print(creds.refresh_token)