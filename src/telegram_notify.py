import os
import urllib.request
import urllib.parse


def send(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Telegram erlaubt max. 4096 Zeichen pro Nachricht
    for chunk in [text[i:i+4096] for i in range(0, max(len(text), 1), 4096)]:
        payload = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": chunk,
        }).encode()
        try:
            req = urllib.request.Request(url, data=payload)
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            print(f"Telegram Error: {e}")
