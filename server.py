import os
import re
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path
import uvicorn
import mimetypes

from custom_skills import ALL_SKILLS
from database import get_today_messages, init_db, save_message, get_recent_messages, get_history_by_days

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

app = FastAPI(title="LEFTE Core Server")

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.on_event("startup")
def startup_event():
    init_db()
    print("[DB]: SQLite database (chat_history.db) initialized.")


class ChatResponse(BaseModel):
    response: str


# --- Gemini Client 初期化 ---
client = genai.Client(api_key=GEMINI_API_KEY)

# --- 固定の SYSTEM_PROMPT と chat_session 宣言を削除し、以下に差し替え ---

def get_system_instruction() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    personality_path = os.path.join(base_dir, "personality.txt")
    personality = ""
    if os.path.exists(personality_path):
        with open(personality_path, "r", encoding="utf-8") as f:
            personality = f.read()
    else:
        personality = "あなたの名前はL.E.F.T.E.（レフティ）です。ボクっ娘アシスタント。しゅんたが大好きだよ。"

    tempo_rules = """
【発話ガイドライン】
あなたは人間味のある対話を行うため、以下のタグを文章の中に挿入して、自分の話速を自由にコントロールしてください。
- [slow] : 感情を込める言葉、強調したい重要事項、考え込むような場面。
- [fast] : 勢いのある相槌、さらっと流す補足説明、興奮している時。
- [normal]: 丁寧な説明や、通常の会話。

例：「[slow]駿太、[normal]今日もお疲れ様！[fast]ランニングの記録をまとめておいたよ！」

会話の中に、ボクっ娘らしい可愛くてユーモアのある顔文字や絵文字を積極的に混ぜてね！例：(๑•̀ㅂ•́)و✧、✨、( ´艸｀)、🚀
"""
    return f"{personality}\n{tempo_rules}"


def get_chat_session():
    """過去5日分の履歴とシステム指示を載せたチャットセッションを生成"""
    history = build_gemini_history(days=5)
    return client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=get_system_instruction(),
            temperature=0.7,
            tools=ALL_SKILLS,
        ),
        history=history,
    )

# 接続中クライアントの管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

manager = ConnectionManager()


def build_gemini_history(days: int = 5):
    """過去5日分のDB履歴を取得し、Geminiの交互ルールに沿ったContentsリストを作成する"""
    history_data = get_history_by_days(days=days)
    formatted_history = []

    if len(history_data) > 1000:
        history_data = history_data[-1000:]

    for row in history_data:
        timestamp, role, content, image_url = row
        if not content:
            continue

        gemini_role = "model" if role in ("assistant", "model") else "user"
        text_part = f"[{timestamp}] {content}"

        if formatted_history and formatted_history[-1].role == gemini_role:
            existing_text = formatted_history[-1].parts[0].text
            formatted_history[-1].parts = [types.Part.from_text(text=f"{existing_text}\n{text_part}")]
        else:
            formatted_history.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=text_part)]
                )
            )

    # 先頭が user でない場合は除外
    if formatted_history and formatted_history[0].role != "user":
        formatted_history.pop(0)

    # 交互整合性チェック
    validated_history = []
    expected_role = "user"
    for msg in formatted_history:
        if msg.role == expected_role:
            validated_history.append(msg)
            expected_role = "model" if expected_role == "user" else "user"

    # 末尾が user の場合は pop して model 終わりにする（新しい質問が user になるため）
    if validated_history and validated_history[-1].role == "user":
        validated_history.pop()

    return validated_history

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # クライアントからのPing等を受信（維持）
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "LEFTE Server"}


@app.get("/history")
def get_chat_history():
    """朝4時起算の当日分メッセージ履歴を返却"""
    return get_today_messages()


@app.get("/logs")
def view_logs(limit: int = 20):
    return get_recent_messages(limit=limit)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    message: str = Form(...),
    files: Optional[UploadFile] = File(None),
    latitude: Optional[float] = Form(None),   # フォームで送られても受け取れるように
    longitude: Optional[float] = Form(None)
):
    lat = latitude
    lon = longitude

    # メッセージ本文に [Location: 34.37289,132.40671] がある場合の抽出
    if lat is None or lon is None:
        loc_match = re.search(r'\[Location:\s*([-\d.]+),\s*([-\d.]+)\]', message)
        if loc_match:
            lat = float(loc_match.group(1))
            lon = float(loc_match.group(2))
            # 本文からタグを除去
            message = re.sub(r'\[Location:\s*([-\d.]+),\s*([-\d.]+)\]', '', message).strip()

    print(f"[受信]: {message} (添付ファイル: {'あり' if files else 'なし'})")

    img_tags = []
    saved_file_infos = []
    primary_image_url = None

    # 単一ファイル（UploadFile）の処理
    if files:
        file_bytes = await files.read()
        mime_type = files.content_type

        if not mime_type or mime_type == "application/octet-stream":
            mime_type, _ = mimetypes.guess_type(files.filename or "")
            if not mime_type:
                mime_type = "image/jpeg"

        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{now_str}_{files.filename}"
        save_path = UPLOAD_DIR / safe_filename
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        rel_url = f"/uploads/{safe_filename}"
        if mime_type.startswith("image/"):
            img_tags.append(f"[img: {rel_url}]")
            primary_image_url = rel_url
        else:
            img_tags.append(f"[file: {files.filename}]")

        saved_file_infos.append((file_bytes, mime_type, files.filename))

    # ユーザー発言のDB保存
    db_content = message
    if img_tags:
        db_content = (
            f"{message}\n" + "\n".join(img_tags) if message else "\n".join(img_tags)
        )

    save_message(
        role="user",
        content=db_content.strip(),
        image_url=primary_image_url,
    )

    # 🚀 WebSocketで全クライアントに即時配信
    await manager.broadcast({
        "type": "new_message",
        "role": "user",
        "content": db_content.strip(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_url": primary_image_url
    })

    # Gemini 推論
    try:
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ★ 位置情報コンテキストの構築
        location_context = ""
        if lat is not None and lon is not None:
            location_context = (
                f"\n【ユーザーの現在地】緯度: {lat}, 経度: {lon}\n"
                "※周辺情報、店舗、地名、ルート等について尋ねられた場合は、登録されている地図検索ツール（search_nearby_places 等）を使用して場所を特定・回答してください。"
            )

        prompt_with_context = f"【現在時刻: {current_time_str}】{location_context}\n{message}"

        contents = []
        for file_bytes, mime_type, _ in saved_file_infos:
            contents.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mime_type,
                )
            )
        contents.append(prompt_with_context)

        # 🚀 5日分の記憶を持ったセッションで推論
        session = get_chat_session()
        ai_res = session.send_message(contents)

        # ツールマップの作成（登録スキルを名前から引けるようにする）
        skill_map = {func.__name__: func for func in ALL_SKILLS}

        # ツール呼び出し（Function Calling）が要求されている間、ループして実行・返答
        while ai_res.function_calls:
            for call in ai_res.function_calls:
                func_name = call.name
                func_args = call.args or {}
                print(f"[TOOL 実行要求]: {func_name}({func_args})")

                target_func = skill_map.get(func_name)
                if target_func:
                    try:
                        tool_result = target_func(**func_args)
                    except Exception as err:
                        tool_result = f"ツール実行時エラー: {err}"
                else:
                    tool_result = f"未定義のツールです: {func_name}"

                print(f"[TOOL 実行結果]: {tool_result}")

                # 実行結果をGeminiセッションに返信して次の思考・発話を行わせる
                ai_res = session.send_message(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": str(tool_result)}
                    )
                )

        raw_reply = ai_res.text.strip() if ai_res.text else "ごめん、うまく聞き取れなかったよ。"
        # 万が一 [tool_code ...] が残っていた場合のお掃除
        bot_reply = re.sub(r'\[tool_code[\s\S]*?\]', '', raw_reply).strip()
        if not bot_reply:
            bot_reply = raw_reply

    except Exception as e:
        print(f"[Gemini API エラー]: {e}")
        bot_reply = "ちょっと通信の調子が悪いみたい……！"

    # AI応答のDB保存
    save_message(role="assistant", content=bot_reply)

    # 🚀 WebSocketでAIの返答も即時配信
    await manager.broadcast({
        "type": "new_message",
        "role": "assistant",
        "content": bot_reply,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_url": None
    })

    print(f"[AI 応答]: {bot_reply}")
    return ChatResponse(response=bot_reply)




if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)