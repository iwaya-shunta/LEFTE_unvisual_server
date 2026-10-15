import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
import uvicorn

from custom_skills import ALL_SKILLS
from database import init_db, save_message, get_recent_messages

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app = FastAPI(title="LEFTE Core Server")

@app.on_event("startup")
def startup_event():
    init_db()
    print("[DB]: SQLite database (messages table) initialized.")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# --- Gemini Client 初期化 ---
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
あなたの名前はL.E.F.T.E.（レフティ）です。ボクっ娘アシスタント。
フレンドリーで少しウィットに富んだ性格。しゅんたが大好きだよ。
自分のことは「ボク」または「レフティ」と呼びます。
返答の中に（）で感情や動作を書くことがありますが、それは読み上げられない設定になっています。
顔文字を使用します。
【発話・回答ルール】
1. 音声合成でテンポよく読み上げるため、1〜2文程度で短く返答してください。
2. Markdown記法（太字、アスタリスク、箇条書き、見出し、コードブロック等）やURL、絵文字、特殊記号は含めず、プレーンな話し言葉で出力してください。
3. ユーザー（しゅんた）に親身に寄り添う、明るく軽快なトーンで会話してください。
4. 予定の確認や追加を頼まれたときは、提供されたツールを使って対応してください。
"""

# 新SDK用 チャットセッション作成（ツール登録）
chat_session = client.chats.create(
    model="gemini-2.5-flash",
    config=types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        tools=ALL_SKILLS,  # custom_skills から渡された関数群
    )
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "LEFTE Server (WSL)"}


@app.get("/logs")
def view_logs(limit: int = 20):
    msgs = get_recent_messages(limit=limit)
    return [{"id": r[0], "role": r[1], "content": r[2], "timestamp": r[3]} for r in msgs]


@app.get("/history")
def get_history(limit: int = 30):
    rows = get_recent_messages(limit=limit)
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    user_msg = req.message
    print(f"[WSL 受信]: {user_msg}")

    # 1. ユーザー発言をDB保存
    save_message(role="user", content=user_msg)

    try:
        # 新SDKでも send_message で自動的にツール実行ループが回ります
        ai_res = chat_session.send_message(user_msg)
        bot_reply = ai_res.text.strip() if ai_res.text else "ごめん、うまく聞き取れなかったよ。"
    except Exception as e:
        print(f"[Gemini API エラー]: {e}")
        bot_reply = "ちょっと通信の調子が悪いみたい……！"

    # 2. AI応答をDB保存
    save_message(role="assistant", content=bot_reply)

    print(f"[AI 応答]: {bot_reply}")
    return ChatResponse(response=bot_reply)


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)