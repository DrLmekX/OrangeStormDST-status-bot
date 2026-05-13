import os
import requests
import gzip
import json
import re
import base64
from datetime import datetime
import pytz
import time

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_STATUS = "1429513092538044528"
CHANNEL_ID_RULES = "1423988013813207164"
CHANNEL_ID_OGLOSZENIA = "1441156235708862615"
CHANNEL_ID_CHANGELOG = "1424139654055071815"
CHANNEL_ID_BOT_EDIT = "1501319921743691866"

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
        "password": "OrangeStorm7777",
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

def extract_day(live_info):
    keys = ["day", "days", "cycles", "cycle", "server_day", "world_day"]
    
    def deep_search(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() in keys and isinstance(v, (int, str)) and str(v).isdigit():
                    return str(v)
                res = deep_search(v)
                if res: return res
        elif isinstance(obj, list):
            for item in obj:
                res = deep_search(item)
                if res: return res
        elif isinstance(obj, str):
            s = obj.strip()
            if s.startswith('{'):
                try:
                    res = deep_search(json.loads(s))
                    if res: return res
                except Exception:
                    pass
            if len(s) > 10 and not re.search(r'\s', s):
                try:
                    dec = base64.b64decode(s).decode('utf-8', errors='ignore')
                    if '{' in dec:
                        res = deep_search(json.loads(dec))
                        if res: return res
                except Exception:
                    pass
        return None

    res = deep_search(live_info)
    if res: return res

    s = json.dumps(live_info)
    m = re.search(r'(?i)["\']?(?:day|days|cycles|cycle|world_day)["\']?\s*[:=]\s*["\']?(\d+)["\']?', s)
    if m: return m.group(1)
    
    return None

def get_old_bot_message(channel_id):
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    url_get = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    try:
        response = requests.get(url_get, headers=headers)
        if response.status_code == 200:
            for msg in response.json():
                if msg.get("author", {}).get("bot") is True:
                    return msg
    except Exception:
        pass
    return None

def build_status_payload(old_message):
    global_cdn_servers = get_servers_from_klei_cdn()
    
    old_days = {}
    if old_message and "embeds" in old_message:
        for embed in old_message["embeds"]:
            desc = embed.get("description", "")
            title = embed.get("title", "")
            match = re.search(r"Dzień:\s*([0-9]+|-)", desc)
            if match:
                old_days[title] = match.group(1)

    embeds = []
    for idx, srv in enumerate(SERVERS):
        search_name = srv["search_name"]
        is_online, players, days = False, 0, None
        
        if global_cdn_servers:
            for live in global_cdn_servers:
                if search_name in live.get("name", ""):
                    is_online = True
                    players = live.get("connected", 0)
                    days = extract_day(live)
                    break
        
        if not is_online or days is None:
            days = old_days.get(srv["display_name"], "-")
            
        status_icon = "🟢" if is_online else "🔴"
        status_text = "Online" if is_online else "Offline"
        spacer = "\u2800" * 36
        
        day_line = f"Dzień: {days}\n" if srv["type"] != "The Forge" else ""
        
        description = (
            f"Status: {status_icon} **{status_text}**\n"
            f"Tryb gry: {srv['type']}\n"
            f"{day_line}"
            f"Gracze: {players} / {srv['hard_max_players']}\n"
            f"Hasło: `{srv['password']}`{spacer}"
        )
        
        embed = {
            "title": srv['display_name'],
            "description": description,
            "color": 0xDF6900
        }
        
        if idx == len(SERVERS) - 1:
            tz = pytz.timezone('Europe/Warsaw')
            now = datetime.now(tz).strftime("%d.%m.%Y %H:%M:%S")
            embed["footer"] = {"text": f"Ostatnia synchronizacja bazy: {now}"}
            
        embeds.append(embed)
        
    return {"content": "", "embeds": embeds}

def build_rules_payload():
    description = (
        "Witaj w świecie chaosu i ognia! Aby nasza społeczność funkcjonowała bez zarzutu, "
        "a gra sprawiała wszystkim przyjemność, prosimy o przestrzeganie poniższych zasad:\n\n"
        "> ### **§1. Kultura i Wzajemny Szacunek**\n"
        "> **Zasada:** Szanuj innych graczy i zachowaj zdrowy dystans.\n"
        "> **Szczegóły:** Zabrania się toksycznego zachowania i obrażania. Wszelkie prywatne spory rozwiązuj z umiarem, "
        "bez tworzenia \"spirali zemsty\" i angażowania całego serwera. Jeśli ktoś prosi o zaprzestanie danego żartu - uszanuj to.\n\n"
        "> ### **§2. Organizacja i Komunikacja**\n"
        "> **Zasada:** Utrzymuj porządek na kanałach.\n"
        "> **Szczegóły:** Używaj kanałów tekstowych zgodnie z ich przeznaczeniem. Zakazuje się spamu, w tym nadmiernego "
        "wysyłania wiadomości, GIF-ów oraz celowego zakłócania rozmów na kanałach głosowych.\n\n"
        "> ### **§3. Fair Play w Rozgrywce**\n"
        "> **Zasada:** Wspólna gra oznacza wspólną odpowiedzialność.\n"
        "> **Szczegóły:** Surowo zakazuje się griefingu, trollowania oraz celowego niszczenia pracy innych (np. podpalania bazy). "
        "Gramy kooperacyjnie - lepiej wspólnie ubić bossa, niż działać na szkodę sojuszników.\n\n"
        "> ### **§4. Prawo do Dobrej Zabawy i Atmosfery**\n"
        "> **Zasada:** Gra ma być przyjemnością dla wszystkich.\n"
        "> **Szczegóły:** Zakazuje się celowego psucia klimatu gry oraz irytowania innych uczestników zabawy. Społeczność zastrzega "
        "sobie prawo do usunięcia gracza z serwera poprzez luźne głosowanie, lub po prostu z faktu, że wspólna gra z daną osobą "
        "staje się nieprzyjemna i uciążliwa.\n\n"
        "> ### **§5. Zasady Platformy Discord**\n"
        "> **Zasada:** Bezwzględne przestrzeganie regulaminu platformy.\n"
        "> **Szczegóły:** Na serwerze obowiązuje całkowity zakaz publikowania treści NSFW (18+), homofobii, rasizmu oraz wszelkich "
        "form dyskryminacji. Zdrowy rozsądek to podstawa.\n\n"
        "> ### **§6. Aktywność Społeczności**\n"
        "> **Zasada:** Budujmy to miejsce razem.\n"
        "> **Szczegóły:** Nie wymagamy obecności 24/7, jednak fajnie, jeśli od czasu do czasu dasz znać, że żyjesz i dołączysz do wspólnej zabawy.\n\n"
        "**Podsumowując:** Stawiamy na luźny klimat, dobrą zabawę i trochę kontrolowanego chaosu - w końcu to **OrangeStormDST**!"
    )
    embed = {
        "title": "━━ REGULAMIN SERWERA ORANGE STORM DST ━━",
        "description": description,
        "color": 0xDF6900
    }
    return {"content": "", "embeds": [embed]}

def build_instructions_payload():
    embed = {
        "title": "⚙️ PANEL STEROWANIA BOTEM",
        "description": (
            "Witaj w panelu zarządzania! Ten kanał służy do wydawania poleceń botowi.\n\n"
            "Aby opublikować ładnie sformatowaną wiadomość na oficjalnych kanałach, napisz tutaj "
            "tekst zaczynający się od odpowiedniego prefiksu:\n\n"
            "**`!ogloszenie [treść]`** - Publikuje ogłoszenie na kanale <#1441156235708862615> (oznacza @everyone)\n"
            "**`!changelog [treść]`** - Publikuje listę zmian na kanale <#1424139654055071815>\n\n"
            "*Przykład użycia:*\n"
            "`!ogloszenie Serwer został zaktualizowany! Zapraszamy do gry.`\n\n"
            "> **Uwaga:** Po odebraniu polecenia bot automatycznie skasuje Twoją roboczą wiadomość "
            "z tego kanału i opublikuje jej treść we wskazanej lokalizacji. **Należy odczekać około 1 minutę na reakcję bota.**"
        ),
        "color": 0x333333
    }
    return {"content": "", "embeds": [embed]}

def build_post_payload(title, text, author_name, icon, ping_content=""):
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
    embed = {
        "title": f"{icon} {title}",
        "description": text,
        "color": 0xDF6900,
        "footer": {"text": f"Opublikowano przez: {author_name} | {now}"}
    }
    return {"content": ping_content, "embeds": [embed]}

def delete_discord_message(channel_id, message_id):
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
    requests.delete(url, headers=headers)
    time.sleep(1)

def clean_channel(channel_id):
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for msg in response.json():
            if not msg.get("author", {}).get("bot"):
                delete_discord_message(channel_id, msg["id"])

def discord_post_new(channel_id, payload):
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    url_post = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    requests.post(url_post, headers=headers, json=payload)
    time.sleep(1)

def update_discord_message(channel_id, payload, existing_msg=None):
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    bot_message_id = existing_msg["id"] if existing_msg else None
    
    if not bot_message_id:
        url_get = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        response = requests.get(url_get, headers=headers)
        if response.status_code == 200:
            for msg in response.json():
                if msg.get("author", {}).get("bot") is True:
                    bot_message_id = msg["id"]
                    break
                    
    if bot_message_id:
        url_patch = f"https://discord.com/api/v10/channels/{channel_id}/messages/{bot_message_id}"
        requests.patch(url_patch, headers=headers, json=payload)
    else:
        url_post = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        requests.post(url_post, headers=headers, json=payload)
    time.sleep(1)

def process_admin_commands():
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID_BOT_EDIT}/messages"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return
    for msg in response.json():
        if msg.get("author", {}).get("bot"):
            continue
        content = msg.get("content", "").strip()
        low = content.lower()
        author_name = msg.get("author", {}).get("global_name") or msg.get("author", {}).get("username") or "Admin"
        if low.startswith("!ogloszenie "):
            text = content[12:].strip()
            discord_post_new(CHANNEL_ID_OGLOSZENIA, build_post_payload("NOWE OGŁOSZENIE", text, author_name, "📢", "@everyone"))
        elif low.startswith("!changelog "):
            text = content[11:].strip()
            discord_post_new(CHANNEL_ID_CHANGELOG, build_post_payload("CHANGELOG", text, author_name, "🛠️", ""))
        delete_discord_message(CHANNEL_ID_BOT_EDIT, msg["id"])

if __name__ == "__main__":
    clean_channel(CHANNEL_ID_OGLOSZENIA)
    clean_channel(CHANNEL_ID_CHANGELOG)
    process_admin_commands()
    update_discord_message(CHANNEL_ID_BOT_EDIT, build_instructions_payload())
    if CHANNEL_ID_STATUS:
        old_msg = get_old_bot_message(CHANNEL_ID_STATUS)
        payload = build_status_payload(old_msg)
        update_discord_message(CHANNEL_ID_STATUS, payload, old_msg)
    update_discord_message(CHANNEL_ID_RULES, build_rules_payload())
