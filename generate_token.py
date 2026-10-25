from google_auth_oauthlib.flow import InstalledAppFlow

# カレンダーとGmailの両方のスコープを定義
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',  # メールの読み取り
    'https://www.googleapis.com/auth/gmail.send',      # メールの送信
]

def main():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("✨ Gmail権限を含んだ token.json を再生成したよ！")

if __name__ == '__main__':
    main()