import os
import requests
import gzip
import json
from datetime import datetime
import pytz

# Pobieranie tajnych danych z GitHuba
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# Konfiguracja Twoich serwerów 
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

def get_servers_from_klei_cdn():
    print("Odpalam radar... Pobieram główną bazę danych Klei z europejskiego CDN...")
    # Dokładnie to źródło, z którego korzysta dstserverlist.appspot.com
    url = "https://lobby-v2-cdn.klei.com/eu-central-1-steam.json.gz"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            try:
                # Rozpakowywanie archiwum .gz, w którym Klei trzyma listę
                decompressed_data = gzip.decompress(response.content)
                data = json.loads(decompressed_data)
            except Exception:
                # Na wypadek gdyby biblioteka requests rozpakowała to automatycznie
                data = response.json()
                
            servers_found = data.get("GET", [])
            print(f"[SUKCES] Pobrane! Lista serwerów w Europie zawiera: {len(servers_found)} pozycji.")
            return servers_found
        else:
            print(f"[BŁĄD CDN] Serwer Klei zwróciło błąd: {response.status_code}")
            return []
    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Nie udało się pobrać danych: {e}")
        return []

def build_message():
    # Pobieramy ogromną listę z Europy tylko raz
    live_servers = get_servers_from_klei_cdn()
    message_lines = []

    for srv in SERVERS:
        match = None
        for live in live_servers:
            # Szukamy "OrangeStormDST | Classic" w nazwach zrzuconych z serwera Klei
            if srv["search_name"] in live.get("name", ""):
                match = live
                break

        if match:
            status_text = "Online"
            players = match.get("connected", 0)
        else:
            status_text = "Offline"
            players = 0

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

    # Czas polski do stopki
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
        print(f"[BŁĄD DISCORDA] Nie udało się pobrać historii: {response.status_code} - {response.text}")
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
        resp = requests.patch(url_patch, headers=headers, json=payload)
        if resp.status_code == 200:
            print("[SUKCES] Wiadomość na Discordzie zaktualizowana.")
    else:
        url_post = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        resp = requests.post(url_post, headers=headers, json=payload)
        if resp.status_code == 200:
            print("[SUKCES] Nowa wiadomość wysłana na Discorda.")

if __name__ == "__main__":
    new_content = build_message()
    update_discord_message(new_content)
