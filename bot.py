import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz

# Pobieranie tajnych danych z GitHuba
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# Konfiguracja Twoich serwerów (Uproszczona - bez portów i IP!)
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

def get_players_from_website(search_term):
    """Metoda 1: 'Wykradanie' danych ze strony dstserverlist (Scraping)"""
    # Budujemy link z wyszukiwaniem konkretnego serwera
    url = f"https://dstserverlist.appspot.com/?name={requests.utils.quote(search_term)}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Bot przeszukuje strukturę strony w poszukiwaniu nazwy serwera
            for element in soup.find_all(['tr', 'div', 'li']):
                text = element.get_text(separator=' ', strip=True)
                if search_term in text:
                    # Magia Regex: Szukamy formatu np. "12/24" lub "12 / 24" w pobliżu nazwy
                    match = re.search(r'\b(\d+)\s*/\s*(\d+)\b', text)
                    if match:
                        return True, int(match.group(1))
    except Exception as e:
        print(f"[SCRAPER BŁĄD] Nie udało się przefiltrować strony dla {search_term}: {e}")
    
    return False, 0

def get_players_from_klei_eu(search_term):
    """Metoda 2: Zapasowe uderzenie w nowe API Klei dla Europy"""
    url = "https://lobby-v2-eu.klei.com/lobby/read"
    payload = {
        "__gameId": "DontStarveTogether",
        "__token": "dev",
        "query": {"text": search_term}
    }
    try:
        response = requests.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            data = response.json()
            for srv in data.get("GET", []):
                if search_term in srv.get("name", ""):
                    return True, srv.get("connected", 0)
    except Exception as e:
        print(f"[API BŁĄD] Klei EU odrzuciło zapytanie: {e}")
    return False, 0

def get_server_status(search_term):
    print(f"\n--- Sprawdzam: {search_term} ---")
    
    # 1. Próba scrapowania (Twój pomysł)
    print("[1/2] Przeszukuję dstserverlist.appspot.com...")
    is_online, players = get_players_from_website(search_term)
    if is_online:
        print(f"[SUKCES] Wyciągnięto ze strony! Graczy: {players}")
        return True, players
        
    # 2. Awaryjne API (jeśli strona by padła)
    print("[2/2] Scraper nie znalazł danych. Odpalam połączenie z oficjalnym serwerem Klei EU...")
    is_online, players = get_players_from_klei_eu(search_term)
    if is_online:
        print(f"[SUKCES] Znaleziono w bazie Klei API! Graczy: {players}")
        return True, players
        
    print("[BŁĄD] Serwer niewidoczny ani na stronie, ani w nowym API.")
    return False, 0

def build_message():
    message_lines = []
    print("\nOdpalam radary...")
    for srv in SERVERS:
        is_online, players = get_server_status(srv["search_name"])

        status_text = "Online" if is_online else "Offline"
        current_players = players if is_online else 0
        player_text = f"{current_players}/{srv['hard_max_players']}"

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

    print("\nSprawdzanie zakończone. Buduję wiadomość...")
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
