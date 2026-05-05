import os
import requests
import a2s
from datetime import datetime
import pytz

# Pobieranie tajnych danych z GitHub Secrets
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# Konfiguracja Twoich serwerów - DANE Z PLAYIT.GG
SERVERS = [
    {
        "name": "[PL] OrangeStormDST | Classic | Najlepszy Polski Serwer!",
        "type": "Classic",
        "ip": "publication-uneatable.gl.at.ply.gg", 
        "port": 39500, 
        "password": "OrangeStorm2101",
        "hard_max_players": 24
    },
    {
        "name": "[PL] OrangeStormDST | Shipwrecked | Najlepszy Polski Serwer!",
        "type": "Shipwrecked",
        "ip": "register-coming.gl.at.ply.gg",
        "port": 39775, 
        "password": "OrangeStorm777",
        "hard_max_players": 12
    },
    {
        "name": "[PL] OrangeStormDST | Forge | Najlepszy Polski Serwer!",
        "type": "The Forge",
        "ip": "thomas-holland.gl.at.ply.gg",
        "port": 39726, 
        "password": "OrangeStorm2026",
        "hard_max_players": 6
    }
]

def get_server_status(ip, port):
    try:
        # Pytamy przez tunel Playit.gg
        address = (ip, port)
        info = a2s.info(address, timeout=4.0)
        return True, info.player_count
    except Exception:
        return False, 0

def build_message():
    message_lines = []
    for srv in SERVERS:
        is_online, players = get_server_status(srv["ip"], srv["port"])

        status_text = "Online" if is_online else "Offline"
        
        current_players = players if is_online else 0
        player_text = f"{current_players}/{srv['hard_max_players']}"

        block = (
            f"> ### **{srv['name']}**\n"
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

    url_get = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    response = requests.get(url_get, headers=headers)
    
    if response.status_code != 200:
        print(f"Błąd Discorda: {response.status_code} - {response.text}")
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
        print("Wiadomość zaktualizowana.")
    else:
        url_post = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        requests.post(url_post, headers=headers, json=payload)
        print("Nowa wiadomość wysłana.")

if __name__ == "__main__":
    new_content = build_message()
    update_discord_message(new_content)
