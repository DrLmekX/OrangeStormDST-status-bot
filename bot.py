import os
import requests
import gzip
import json
from datetime import datetime
import pytz

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')

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

def build_message():
    global_cdn_servers = get_servers_from_klei_cdn()
    message_lines = []

    for srv in SERVERS:
        search_name = srv["search_name"]
        is_online, players = False, 0

        if global_cdn_servers:
            for live in global_cdn_servers:
                if search_name in live.get("name", ""):
                    is_online, players = True, live.get("connected", 0)
                    break

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

    payload = {"content": content}

    if bot_message_id:
        url_patch = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{bot_message_id}"
        requests.patch(url_patch, headers=headers, json=payload)
    else:
        url_post = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
        requests.post(url_post, headers=headers, json=payload)

if __name__ == "__main__":
    new_content = build_message()
    update_discord_message(new_content)
