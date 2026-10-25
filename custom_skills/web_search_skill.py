from typing import Optional
from ddgs import DDGS
import trafilatura

def search_web(query: str, max_results: int = 3) -> str:
    """
    インターネットを検索して、最新の情報やWebサイトの概要（タイトル、URL、スニペット）を取得します。
    最新のニュース、天気、店舗情報、トレンド、事実確認、技術的な調べ物などに使用します。

    Args:
        query: 検索キーワード。自然文ではなく「単語 スペース 単語」の検索キーワード（例: "広島 天気 明日"）を指定してください。
        max_results: 取得する検索結果の件数（デフォルト: 3）。
    """
    try:
        ddgs = DDGS()
        # まずは日本リージョンで検索
        results = list(ddgs.text(query, region="jp-jp", max_results=max_results))
        
        # もしヒットしなければ地域縛りを外して再試行
        if not results:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"「{query}」に関する検索結果は見つからなかったよ。"

        output = []
        for i, r in enumerate(results, start=1):
            title = r.get("title", "無題")
            link = r.get("href", "")
            body = r.get("body", "")
            output.append(f"[{i}] {title}\nURL: {link}\n概要: {body}\n")

        return "\n".join(output)
    except Exception as e:
        return f"Web検索中にエラーが発生しちゃった：{e}"


def fetch_web_page(url: str) -> str:
    """
    指定されたURLのWebページにアクセスし、広告やメニューを除いた本文テキストを読み取ります。
    検索結果の概要だけでは情報が不足しており、ページ全体を詳しく確認したい場合に使用します。

    Args:
        url: 読み取りたいWebページのURL。
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return "ページのデータを取得できなかったよ。"

        text = trafilatura.extract(downloaded)
        if not text:
            return "ページの本文を抽出できなかったよ。"

        return f"【ページ内容（抜粋）】:\n{text[:1500]}"
    except Exception as e:
        return f"ページの読み込み中にエラーが発生しちゃった：{e}"