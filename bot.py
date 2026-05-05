import os
import requests
import gzip
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Tajne klucze
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# Konfiguracja Serwerów
SERVERS = [
    {
        "search_name": "OrangeStormDST | Classic",
        "display_name": "[PL] OrangeStormDST | Classic | Najlepszy Polski Serwer!",
        "type": "Classic",
        "password": "OrangeStorm2101",
        "hard_max_players": 24
    },
    {
        "search_name": "OrangeStormDST | Shipwrecked",
        "display_name": "[PL] OrangeStormDST | Shipwrecked | Najlepszy Polski Serwer!",
        "type": "Shipwrecked",
        "password": "OrangeStorm777",
        "hard_max_players": 12
    },
    {
        "search_name": "OrangeStormDST | Forge",
        "display_name": "[PL] OrangeStormDST | Forge | Najlepszy Polski Serwer!",
        "type": "The Forge",
        "password": "OrangeStorm2026",
        "hard_max_players": 6
    }
]

# Powszechne nagłówki przeglądarki dla ominięcia Zapory WAF (Błędu 403 / Captcha)
BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
}

def get_servers_from_klei_cdn():
    """WARSTWA 1: Baza Klei CDN (Z obejściem WAF 403)"""
    regions = ['eu-central-1', 'us-east-1', 'ap-southeast-1', 'us-west-1']
    platforms = ['Steam', 'steam']
    live_servers = []

    print("--- [WARSTWA 1] Szukam w oficjalnych bazach Klei CDN ---")
    for region in regions:
        for platform in platforms:
            url = f"https://lobby-v2-cdn.klei.com/{region}-{platform}.json.gz"
            try:
                response = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
                if response.status_code == 200:
                    try:
                        dec = gzip.decompress(response.content)
                        data = json.loads(dec)
                    except Exception:
                        data = response.json()
                    
                    # Wypakowywanie listy z JSON
                    servers = []
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                servers = v
                                break
                    elif isinstance(data, list):
                        servers = data
                        
                    if servers:
                        print(f" [OK] Pobrano archiwum {region}-{platform} ({len(servers)} serwerów)")
                        live_servers.extend(servers)
                        break # Uciekamy, bo trafiliśmy w odpowiednią wielkość liter
                elif response.status_code == 403:
                    pass # Odrzucamy 403 (Zły region lub wielkość liter)
            except Exception:
                pass
                
    return live_servers

def get_players_from_battlemetrics(search_term):
    """WARSTWA 2: Oficjalne publiczne API BattleMetrics (Brak kluczy, 100% pewności)"""
    url = f"https://api.battlemetrics.com/servers?filter[search]={requests.utils.quote(search_term)}"
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=8)
        if response.status_code == 200:
            for server in response.json().get("data", []):
                attrs = server.get("attributes", {})
                if search_term in attrs.get("name", "") and attrs.get("status") == "online":
                    return True, attrs.get("players", 0)
    except Exception:
        pass
    return False, 0

def get_players_from_website(search_term):
    """WARSTWA 3: Wykradanie ze strony dstserverlist (Z obejściem Captcha)"""
    url = f"https://dstserverlist.appspot.com/?name={requests.utils.quote(search_term)}"
    try:
        response = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup.find_all(['tr', 'div', 'li']):
                text = element.get_text(separator=' ', strip=True)
                if search_term in text:
                    match = re.search(r'\b(\d+)\s*/\s*(\d+)\b', text)
                    if match:
                        return True, int(match.group(1))
    except Exception:
        pass
    return False, 0

def build_message():
    print("\nInicjalizacja Trzystopniowej Tarczy Detekcji...")
    global_cdn_servers = get_servers_from_klei_cdn()
    message_lines = []

    for srv in SERVERS:
        search_name = srv["search_name"]
        print(f"\n=> Szukam: {search_name}")
        is_online, players = False, 0

        # Krok 1: Przeszukaj pobraną listę Klei
        if global_cdn_servers:
            for live in global_cdn_servers:
                if search_name in live.get("name", ""):
                    is_online, players = True, live.get("connected", 0)
                    print(" [SUKCES] Odczytano bezpośrednio z Klei CDN!")
                    break
        
        # Krok 2: Jeśli CDN zawiedzie, uderz w BattleMetrics
        if not is_online:
            print(" [INFO] Brak w CDN. Uderzam w BattleMetrics API...")
            is_online, players = get_players_from_battlemetrics(search_name)
            if is_online:
                print(" [SUKCES] Odczytano z BattleMetrics!")

        # Krok 3: Jeśli BM zawiedzie, scrapuj stronę
        if not is_online:
            print(" [INFO] Brak w API. Scrapuję stronę dstserverlist...")
            is_online, players = get_players_from_website(search_name)
            if is_online:
                print(" [SUKCES] Wyciągnięto dane omijając Captchę!")

        if not is_online:
            print(" [OFFLINE] Żadne z 3 źródeł nie widzi tego serwera.")

        status_text = "Online" if is_online else "Offline"
        player_text = f"{players}/{srv['hard_max_players']}"

        block = (
            f"> ### **{srv['display_name']}**\n"
            f"> **Status:** `{status_text}`\n"
            f"> **Typ rozgrywki:** {srv['type']}\n"
            f"> **Gracze:** {player_text}\n"
            f"> **Hasło:** `{srv['password']}`\n"
            f"> ──────────────────────────────────────────────"
        )
        message_lines.append(block)

    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S")
    message_lines.append(f"\n*(Ostatnia aktualizacja: {now})*")

    return "\n\n".join(message_lines)

def update_discord_message(content):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    print("\nŁączę się z Discordem...")
    url_get = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    response = requests.get(url_get, headers=headers)
    
    if response.status_code != 200:
        print(f"[BŁĄD DISCORDA] {response.text}")
        return

    messages = response.json()
    bot_message_id = None

    for msg in messages:
        if msg.get("author", {}).get("bot") is True:
            bot_message_id = msg["id"]
            break

    payload = {"content": content}

    if bot_message_id:
        url_patch = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{bot_message_id}"
        requests.patch(url_patch, headers=headers, json=payload)
        print("[SUKCES] Zaktualizowano na Discordzie.")
    else:
        url_post = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        requests.post(url_post, headers=headers, json=payload)
        print("[SUKCES] Wysłano nową wiadomość na Discord.")

if __name__ == "__main__":
    new_content = build_message()
    update_discord_message(new_content)
