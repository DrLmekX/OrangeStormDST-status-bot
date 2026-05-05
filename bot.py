import os
import requests
import gzip
import json
from datetime import datetime
import pytz

# Pobieranie tajnych danych z GitHuba
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

# Konfiguracja Serwerów
SERVERS = [
    {
        "search_name": "OrangeStormDST | Classic",
        "display_name": "🏕️ [PL] OrangeStormDST | Classic",
        "type": "Classic",
        "password": "OrangeStorm2101",
        "hard_max_players": 24,
        "show_days": True
    },
    {
        "search_name": "OrangeStormDST | Shipwrecked",
        "display_name": "🏝️ [PL] OrangeStormDST | Shipwrecked",
        "type": "Shipwrecked",
        "password": "OrangeStorm777",
        "hard_max_players": 12,
        "show_days": True
    },
    {
        "search_name": "OrangeStormDST | Forge",
        "display_name": "⚔️ [PL] OrangeStormDST | Forge",
        "type": "The Forge",
        "password": "OrangeStorm2026",
        "hard_max_players": 6,
        "show_days": False
    }
]

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/html, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
}

def get_servers_from_klei_cdn():
    regions = ['eu-central-1', 'us-east-1', 'ap-southeast-1', 'us-west-1']
    platforms = ['Steam', 'steam']
    live_servers = []

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
                    
                    servers = []
                    if isinstance(data, dict):
                        for k, v in data.items():
                            if isinstance(v, list):
                                servers = v
                                break
                    elif isinstance(data, list):
                        servers = data
                        
                    if servers:
                        live_servers.extend(servers)
                        break
            except Exception:
                pass
                
    return live_servers

def build_embed():
    global_cdn_servers = get_servers_from_klei_cdn()
    fields = []

    for srv in SERVERS:
        search_name = srv["search_name"]
        is_online, players, current_day = False, 0, "?"

        # Wyciąganie danych prosto z CDN
        if global_cdn_servers:
            for live in global_cdn_servers:
                if search_name in live.get("name", ""):
                    is_online = True
                    players = live.get("connected", 0)
                    current_day = live.get("day", "?")
                    break

        # Przygotowanie wizualnych wskaźników
        status_icon = "🟢" if is_online else "🔴"
        status_text = "Online" if is_online else "Offline"
        
        # Budowa eleganckich linijek danych
        value_lines = [
            f"**Status:** {status_icon} `{status_text}`",
            f"**Typ:** `{srv['type']}`",
            f"**Gracze:** `{players} / {srv['hard_max_players']}`"
        ]
        
        # Dodawanie dni tylko dla określonych serwerów
        if srv["show_days"]:
            display_day = current_day if is_online else "-"
            value_lines.append(f"**Dzień:** `{display_day}`")
            
        value_lines.append(f"**Hasło:** `{srv['password']}`")

        # Pojedynczy blok serwera dołączany do Embedu
        fields.append({
            "name": f" {srv['display_name']} ",
            "value": "\n".join(value_lines) + "\n\u200b", # Pusty znak \u200b robi ładny odstęp między serwerami
            "inline": False
        })

    # Czas i Data
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S")

    # Tworzenie całego szkieletu Embed
    embed = {
        "title": "📊  Status Serwerów OrangeStormDST",
        "color": 16753920, # Kod koloru pomarańczowego
        "fields": fields,
        "footer": {
            "text": f"Aktualizacja zsynchronizowana: {now}"
        }
    }
    
    return embed

def update_discord_message(embed_data):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    # Pobieranie historii kanału
    url_get = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    response = requests.get(url_get, headers=headers)
    
    if response.status_code != 200:
        print(f"[BŁĄD] Nie można pobrać historii kanału: {response.text}")
        return

    messages = response.json()
    bot_message_id = None

    for msg in messages:
        if msg.get("author", {}).get("bot") is True:
            bot_message_id = msg["id"]
            break

    # Czysty ładunek z wyzerowaniem "content", żeby skasować stary, brzydki tekst
    payload = {
        "content": "", 
        "embeds": [embed_data]
    }

    if bot_message_id:
        url_patch = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{bot_message_id}"
        requests.patch(url_patch, headers=headers, json=payload)
    else:
        url_post = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        requests.post(url_post, headers=headers, json=payload)

if __name__ == "__main__":
    new_embed = build_embed()
    update_discord_message(new_embed)
