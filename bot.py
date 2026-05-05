import os
import requests
from datetime import datetime
import pytz

# Pobieranie tajnych danych z GitHuba
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# Konfiguracja Twoich serwerów (Uproszczona - bez portów i IP!)
SERVERS = [
    {
        "search_name": "OrangeStormDST | Classic", # Kawałek nazwy do wyszukania w bazie
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

def get_klei_servers():
    print("Odpalam radar... Szukam serwerów OrangeStormDST w oficjalnej bazie Klei...")
    url = "https://lobby-v2-dst.klei.com/lobby/read"
    payload = {
        "__gameId": "DontStarveTogether",
        "__token": "dev",
        "query": {
            "text": "OrangeStormDST"
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            servers_found = data.get("GET", [])
            print(f"[SUKCES] Baza Klei odpowiedziała. Znaleziono {len(servers_found)} pasujących serwerów w internecie.")
            return servers_found
        else:
            print(f"[BŁĄD] Odpowiedź serwerów Klei: {response.status_code}")
            return []
    except Exception as e:
        print(f"[BŁĄD KRYTYCZNY] Nie można połączyć się z Klei: {e}")
        return []

def build_message():
    # Pobieramy dane z bazy tylko raz dla wszystkich serwerów
    live_servers = get_klei_servers()
    message_lines = []

    for srv in SERVERS:
        # Szukamy naszego serwera na liście pobranej od Klei
        match = None
        for live in live_servers:
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
