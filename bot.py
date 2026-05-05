import os
import requests
import a2s
from datetime import datetime
import pytz
import socket
import time

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

def get_server_status(name, domain, port):
    print(f"--- Pytam serwer: {name} ({domain}:{port}) ---")
    
    # OSTATECZNY FIX 1: Wymuszenie twardego IPv4 
    try:
        ip_v4 = socket.gethostbyname(domain)
        print(f"[DNS] Rozwiązano domenę na czyste IPv4: {ip_v4}")
    except Exception as e:
        print(f"[BŁĄD DNS] Nie można rozwiązać domeny: {e}")
        return False, 0

    address = (ip_v4, int(port))
    
    # OSTATECZNY FIX 2: Agresywne uderzenia (3 próby dla UDP)
    for attempt in range(1, 4):
        try:
            print(f"  -> Próba {attempt}/3...")
            # Pytamy przez wymuszone IPv4 z wydłużonym czasem nasłuchu
            info = a2s.info(address, timeout=4.0)
            print(f"[SUKCES] Odpowiedź poprawna! Graczy: {info.player_count}/{info.max_players}")
            return True, info.player_count
        except TimeoutError:
            print(f"  [X] Próba {attempt} - Timeout (Zgubiony pakiet).")
            time.sleep(1.5) # Czekamy chwilę przed kolejnym atakiem
        except Exception as e:
            print(f"  [X] Próba {attempt} - Błąd: {type(e).__name__} -> {e}")
            time.sleep(1.5)
            
    print(f"[BŁĄD KRYTYCZNY] Serwer nie odpowiedział pomimo 3 prób.")
    return False, 0

def build_message():
    message_lines = []
    print("\nRozpoczynam sprawdzanie wszystkich serwerów...")
    for srv in SERVERS:
        is_online, players = get_server_status(srv["name"], srv["ip"], srv["port"])

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

    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S")
    message_lines.append(f"\n*(Ostatnia aktualizacja: {now})*")
    
    print("Sprawdzanie zakończone. Buduję wiadomość...")
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
            print(f"[BŁĄD DISCORDA] Edycja nie powiodła się: {resp.text}")
    else:
        url_post = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        resp = requests.post(url_post, headers=headers, json=payload)
        if resp.status_code == 200:
            print("[SUKCES] Nowa wiadomość wysłana na Discorda.")
        else:
            print(f"[BŁĄD DISCORDA] Wysyłanie nowej wiadomości nie powiodło się: {resp.text}")

if __name__ == "__main__":
    new_content = build_message()
    update_discord_message(new_content)
