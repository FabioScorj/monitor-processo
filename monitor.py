import requests
from bs4 import BeautifulSoup
import hashlib
import os
import json
from datetime import datetime

URL = "https://sicop.sistemas.mpba.mp.br/Modulos/Consulta/Processo.aspx?L0QifJI5OZay/N8MYuNlm7GOhf3NBvJxPHjDdi6yVUmSr7RNnASmfg=="
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
HASH_FILE = "last_hash.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, json=payload)

def get_page_content():
    session = requests.Session()
    response = session.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove scripts e estilos para pegar só o conteúdo relevante
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
    """Tenta extrair a última data de atualização da página"""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    import re
    dates = re.findall(r'\d{2}/\d{2}/\d{4}', text)
    return dates[-1] if dates else "data não encontrada"

def main():
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"[{now}] Verificando atualização...")

    try:
        content, raw_html = get_page_content()
    except Exception as e:
        send_telegram(f"⚠️ <b>Erro ao acessar o processo</b>\n\nHorário: {now}\nErro: {e}")
        return

    current_hash = get_hash(content)
    last_hash = load_last_hash()
    last_date = extract_last_date(raw_html)

    if last_hash is None:
        # Primeira execução
        save_hash(current_hash)
        send_telegram(
            f"✅ <b>Monitoramento iniciado!</b>\n\n"
            f"📋 Processo SICOP MP-BA\n"
            f"📅 Última data encontrada na página: {last_date}\n"
            f"🕐 Verificações: 13h e 17h (horário de Brasília)\n\n"
            f"Você será notificado se houver atualizações."
        )
        print("Primeira execução - hash salvo.")
    elif current_hash != last_hash:
        # Página foi atualizada!
        save_hash(current_hash)
        send_telegram(
            f"🔔 <b>ATUALIZAÇÃO DETECTADA!</b>\n\n"
            f"📋 Processo SICOP MP-BA foi atualizado!\n"
            f"📅 Última data na página: {last_date}\n"
            f"🕐 Detectado em: {now}\n\n"
            f"🔗 Acesse: {URL}"
        )
        print("Atualização detectada!")
    else:
        # Sem mudanças
        send_telegram(
            f"ℹ️ <b>Sem atualizações</b>\n\n"
            f"📋 Processo SICOP MP-BA\n"
            f"📅 Última data na página: {last_date}\n"
            f"🕐 Verificado em: {now}"
        )
        print("Sem mudanças.")

if __name__ == "__main__":
    main()
