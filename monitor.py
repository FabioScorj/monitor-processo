import hashlib
import os
import re
import time
import requests
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GITHUB_TOKEN = os.environ["GH_TOKEN"]
REPO = "FabioScorj/monitor-processo"
HASH_FILE = "last_hash.txt"
URL = "https://sicop.sistemas.mpba.mp.br/Modulos/Consulta/Processo.aspx?L0QifJI5OZay/N8MYuNlm7GOhf3NBvJxPHjDdi6yVUmSr7RNnASmfg=="

BRT = timezone(timedelta(hours=-3))

def now_brt():
    return datetime.now(BRT).strftime("%d/%m/%Y %H:%M")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def get_hash_from_github():
    url = f"https://api.github.com/repos/{REPO}/contents/{HASH_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        import base64
        data = response.json()
        content = base64.b64decode(data["content"]).decode("utf-8").strip()
        return content, data["sha"]
    return None, None

def save_hash_to_github(new_hash, sha=None):
    import base64
    url = f"https://api.github.com/repos/{REPO}/contents/{HASH_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content = base64.b64encode(new_hash.encode("utf-8")).decode("utf-8")
    payload = {"message": "Atualiza hash do monitoramento", "content": content}
    if sha:
        payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

def get_page_content():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(URL)
        time.sleep(5)
        html = driver.page_source
        text = driver.find_element("tag name", "body").text
        return text, html
    finally:
        driver.quit()

def get_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def extract_last_date(html):
    dates = re.findall(r'\d{2}/\d{2}/\d{4}', html)
    return dates[-1] if dates else "data nao encontrada"

def main():
    now = now_brt()
    print(f"[{now}] Verificando...")

    try:
        content, raw_html = get_page_content()
    except Exception as e:
        send_telegram(f"⚠️ <b>Erro ao acessar o processo</b>\n\nHorario: {now}\nErro: {e}")
        return

    current_hash = get_hash(content)
    last_hash, sha = get_hash_from_github()
    last_date = extract_last_date(raw_html)

    if last_hash is None:
        save_hash_to_github(current_hash)
        send_telegram(
            f"✅ <b>Monitoramento iniciado!</b>\n\n"
            f"📋 Processo EMPÓRIO\n"
            f"📅 Ultima data encontrada: {last_date}\n"
            f"🕐 Verificacoes automaticas configuradas\n\n"
            f"Voce sera notificado se houver atualizacoes."
        )
    elif current_hash != last_hash:
        save_hash_to_github(current_hash, sha)
        send_telegram(
            f"🔔 <b>ATUALIZACAO DETECTADA!</b>\n\n"
            f"📋 Processo EMPÓRIO foi atualizado!\n"
            f"📅 Ultima data na pagina: {last_date}\n"
            f"🕐 Detectado em: {now} (Brasilia)"
        )
    else:
        send_telegram(
            f"ℹ️ <b>Sem atualizacoes</b>\n\n"
            f"📋 Processo EMPÓRIO\n"
            f"📅 Ultima data: {last_date}\n"
            f"🕐 Verificado em: {now} (Brasilia)"
        )

if __name__ == "__main__":
    main()
