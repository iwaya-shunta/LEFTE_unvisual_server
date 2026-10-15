from google_auth_oauthlib.flow import InstalledAppFlow

# カレンダーの読み書き権限
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    # 認証URLを発行してローカルサーバーで受け取る
    creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("✨ token.json の生成に成功しました！")

if __name__ == '__main__':
    main()