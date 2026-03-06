import requests
from bs4 import BeautifulSoup
import hashlib
import os
import re
from datetime import datetime

URL = "https://sicop.sistemas.mpba.mp.br/Modulos/Consulta/Processo.aspx?L0QifJI5OZay/N8MYuNlm7GOhf3NBvJxPHjDdi6yVUmSr7RNnASmfg=="
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
HASH_FILE = "last_hash.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_page_content():
    session = requests.Session()
    session.headers.update(HEADERS)
    response = session.get(URL, timeout=30, allow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True), response.text

def get_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def load_last_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            return f.read().strip()
    return None

def save_hash(h):
    with open(HASH_FILE, "w") as f:
        f.write(h)

def extract_last_date(html):
    dates = re.findall(r'\d{2}/\d{2}/\d{4}', html)
    return dates[-1] if dates else "data nao encontrada"

def main():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"[{now}] Verificando atualizacao...")

    try:
        content, raw_html = get_page_content()
    except Exception as e:
        send_telegram(
            f"⚠️ <b>Erro ao acessar o processo</b>\n\n"
            f"Horario: {now}\n"
            f"Erro: {e}"
        )
        return

    current_hash = get_hash(content)
    last_hash = load_last_hash()
    last_date = extract_last_date(raw_html)

    if last_hash is None:
        save_hash(current_hash)
        send_telegram(
            f"✅ <b>Monitoramento iniciado!</b>\n\n"
            f"📋 Processo SICOP MP-BA\n"
            f"📅 Ultima data encontrada: {last_date}\n"
            f"🕐 Verificacoes: 13h e 17h\n\n"
            f"Voce sera notificado se houver atualizacoes."
        )
    elif current_hash != last_hash:
        save_hash(current_hash)
        send_telegram(
            f"🔔 <b>ATUALIZACAO DETECTADA!</b>\n\n"
            f"📋 Processo SICOP MP-BA foi atualizado!\n"
            f"📅 Ultima data na pagina: {last_date}\n"
            f"🕐 Detectado em: {now}"
        )
    else:
        send_telegram(
            f"ℹ️ <b>Sem atualizacoes</b>\n\n"
            f"📋 Processo SICOP MP-BA\n"
            f"📅 Ultima data na pagina: {last_date}\n"
            f"🕐 Verificado em: {now}"
        )

if __name__ == "__main__":
    main()
