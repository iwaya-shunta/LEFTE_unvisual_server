import os
import urllib.request
import urllib.parse
import json
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


def reverse_geocode_skill(latitude: float, longitude: float) -> str:
    """
    指定された緯度・経度から、Google Maps を使用して日本の正確な住所および現在地名を取得します。
    """
    if not GOOGLE_MAPS_API_KEY:
        return "Google Maps APIキーが設定されていません。"

    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json?"
        f"latlng={latitude},{longitude}&language=ja&key={GOOGLE_MAPS_API_KEY}"
    )

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("status") != "OK":
                return f"住所の特定に失敗しました (Status: {data.get('status')})"

            results = data.get("results", [])
            if not results:
                return "住所が見つかりませんでした。"

            best_address = results[0].get("formatted_address", "")
            best_address = best_address.replace("日本、", "").strip()
            return f"【現在地住所】: {best_address}"

    except Exception as e:
        logging.error(f"Geocoding エラー: {e}")
        return f"住所取得中にエラーが発生しました: {e}"


def search_nearby_places(latitude: float, longitude: float, keyword: str = "コンビニ", radius: int = 1000) -> str:
    """
    指定した現在地（緯度・経度）の周辺にある店舗や施設（コンビニ、スーパー、飲食店等）を検索します。

    Args:
        latitude: 現在地の緯度
        longitude: 現在地の経度
        keyword: 検索したい施設の種類や名前（例: "コンビニ", "スーパー", "カフェ"）
        radius: 検索範囲の半径（メートル単位、最大50000m、デフォルト1000m）
    """
    if not GOOGLE_MAPS_API_KEY:
        return "Google Maps APIキーが設定されていません。"

    # 自由入力テキストで周辺検索できる Text Search (New) を使用
    url = "https://places.googleapis.com/v1/places:searchText"
    
    payload = {
        "textQuery": keyword,
        "maxResultCount": 5,
        "languageCode": "ja",
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": float(radius)
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating"
    }

    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=6) as res:
            data = json.loads(res.read().decode("utf-8"))
            places = data.get("places", [])

            if not places:
                return f"指定された現在地の周辺に「{keyword}」は見つかりませんでした。"

            lines = [f"【現在地から半径 {radius}m 以内の「{keyword}」】"]
            for p in places:
                name = p.get("displayName", {}).get("text", "名称不明")
                address = p.get("formattedAddress", "").replace("日本、", "").strip()
                rating = p.get("rating")
                rating_str = f" (★{rating})" if rating else ""
                lines.append(f"- {name}{rating_str}（{address}）")

            return "\n".join(lines)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logging.error(f"Places API (New) HTTPエラー: {e.code} - {error_body}")
        return f"周辺検索エラー (HTTP {e.code}): {error_body}"
    except Exception as e:
        logging.error(f"Places 検索エラー: {e}")
        return f"周辺検索中にエラーが発生しました: {e}"