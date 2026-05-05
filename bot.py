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
        "display_name": "[PL] OrangeStormDST | Classic",
        "type": "Classic",
        "password": "OrangeStorm2101",
        "hard_max_players": 24,
        "show_days": True
    },
    {
        "search_name": "OrangeStormDST | Shipwrecked",
        "display_name": "[PL] OrangeStormDST | Shipwrecked",
        "type": "Shipwrecked",
        "password": "OrangeStorm777",
        "hard_max_players": 12,
        "show_days": True
    },
    {
        "search_name": "OrangeStormDST | Forge",
        "display_name": "[PL] OrangeStormDST | Forge",
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

def translate_season(season_en):
    translations = {
        "Spring": "Wiosna",
        "Summer": "Lato",
        "Autumn": "Jesień",
        "Winter": "Zima"
    }
    return translations.get(season_en, "Nieznany")

def build_embed():
    global_cdn_servers = get_servers_from_klei_cdn()
    fields = []

    for srv in SERVERS:
        search_name = srv["search_name"]
        is_online, players = False, 0
        current_day = "Ukryty"
        season_pl = "Brak danych"

        # Wyciąganie danych z bazy Klei
        if global_cdn_servers:
            for live in global_cdn_servers:
                if search_name in live.get("name", ""):
                    is_online = True
                    players = live.get("connected", 0)
                    
                    # Szukanie dnia (czasami jest pod 'day', czasami głębiej)
                    raw_day = live.get("day")
                    if raw_day is not None:
                        current_day = str(raw_day)
                        
                    # Szukanie sezonu
                    raw_season = live.get("season", "")
                    if raw_season:
                        season_pl = translate_season(raw_season)
                        
                    break

        # Przygotowanie masywnych wskaźników tekstowych
        status_text = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
        
        # Surowy i techniczny układ
        value_lines = [
            f"**STATUS:** {status_text}",
            f"**TYP:** `{srv['type']}`",
            f"**GRACZE:** `{players} / {srv['hard_max_players']}`"
        ]
        
        if srv["show_days"]:
            display_day = current_day if is_online else "-"
            display_season = season_pl if is_online else "-"
            value_lines.append(f"**DZIEŃ:** `{display_day}` ({display_season})")
            
        value_lines.append(f"**HASŁO:** `{srv['password']}`")

        # Pojedynczy blok serwera w formie panelu Embed
        fields.append({
            "name": f"■ {srv['display_name']}",
            "value": "\n".join(value_lines),
            "inline": False
        })

    # Czas i Data z polską strefą czasową
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S")

    # Tworzenie czystego, inżynieryjnego panelu Embed
    embed = {
        "title": "MONITOR SERWERÓW ORANGESTORM",
        "color": 0xDF6900, # Ciężki, ciemno-pomarańczowy kolor
        "fields": fields,
        "footer": {
            "text": f"Ostatnia synchronizacja bazy: {now}"
        }
    }
    
    return embed

def update_discord_message(embed_data):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    url_get = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    response = requests.get(url_get, headers=headers)
    
    if response.status_code != 200:
        return

    messages = response.json()
    bot_message_id = None

    for msg in messages:
        if msg.get("author", {}).get("bot") is True:
            bot_message_id = msg["id"]
            break

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
