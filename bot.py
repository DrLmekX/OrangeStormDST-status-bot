import os
import requests
import gzip
import json
from datetime import datetime
import pytz

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')

CHANNEL_ID_STATUS = os.environ.get('CHANNEL_ID')
CHANNEL_ID_RULES = "1423988013813207164"
CHANNEL_ID_ANNOUNCEMENTS = "1441156235708862615"
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

API_HEADERS = {
    "Authorization": f"Bot {DISCORD_TOKEN}",
    "Content-Type": "application/json"
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

def build_status_payload():
    global_cdn_servers = get_servers_from_klei_cdn()
    embeds = []
    spacer = "\u2800" * 45

    for idx, srv in enumerate(SERVERS):
        search_name = srv["search_name"]
        is_online, players = False, 0

        if global_cdn_servers:
            for live in global_cdn_servers:
                if search_name in live.get("name", ""):
                    is_online = True
                    players = live.get("connected", 0)
                    break

        status_icon = "🟢" if is_online else "🔴"
        status_text = "Online" if is_online else "Offline"
        
        description = (
            f"Status: {status_icon} **{status_text}**\n"
            f"Tryb gry: {srv['type']}\n"
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
            embed["footer"] = {
                "text": f"Ostatnia synchronizacja bazy: {now}"
            }

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

def update_static_message(channel_id, payload):
    url_get = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    response = requests.get(url_get, headers=API_HEADERS)
    
    if response.status_code != 200:
        return

    messages = response.json()
    bot_message_id = None

    for msg in messages:
        if msg.get("author", {}).get("bot") is True:
            bot_message_id = msg["id"]
            break

    if bot_message_id:
        url_patch = f"https://discord.com/api/v10/channels/{channel_id}/messages/{bot_message_id}"
        requests.patch(url_patch, headers=API_HEADERS, json=payload)
    else:
        url_post = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        requests.post(url_post, headers=API_HEADERS, json=payload)

def enforce_clean_channel(channel_id):
    url_get = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    response = requests.get(url_get, headers=API_HEADERS)
    if response.status_code == 200:
        for msg in response.json():
            if not msg.get("author", {}).get("bot"):
                url_delete = f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg['id']}"
                requests.delete(url_delete, headers=API_HEADERS)

def process_bot_edit_commands():
    url_get = f"https://discord.com/api/v10/channels/{CHANNEL_ID_BOT_EDIT}/messages"
    response = requests.get(url_get, headers=API_HEADERS)
    
    if response.status_code != 200:
        return

    messages = response.json()
    instruction_found = False

    for msg in reversed(messages):
        is_bot = msg.get("author", {}).get("bot")
        
        if is_bot:
            if msg.get("embeds") and "⚙️ INSTRUKCJA" in msg["embeds"][0].get("title", ""):
                instruction_found = True
            else:
                requests.delete(f"https://discord.com/api/v10/channels/{CHANNEL_ID_BOT_EDIT}/messages/{msg['id']}", headers=API_HEADERS)
            continue

        content = msg.get("content", "").strip()
        target_channel = None
        title = ""
        prefix = ""

        if content.lower().startswith("!ogloszenie"):
            target_channel = CHANNEL_ID_ANNOUNCEMENTS
            title = "📢 NOWE OGŁOSZENIE"
            prefix = "!ogloszenie"
        elif content.lower().startswith("!changelog"):
            target_channel = CHANNEL_ID_CHANGELOG
            title = "🛠️ AKTUALIZACJA SERWERA"
            prefix = "!changelog"

        if target_channel:
            actual_text = content[len(prefix):].strip()
            author_name = msg["author"].get("global_name") or msg["author"].get("username")
            tz = pytz.timezone('Europe/Warsaw')
            now = datetime.now(tz).strftime("%d.%m.%Y %H:%M")

            embed = {
                "title": title,
                "description": actual_text,
                "color": 0xDF6900,
                "footer": {
                    "text": f"Dodał: {author_name} • {now}"
                }
            }
            
            requests.post(f"https://discord.com/api/v10/channels/{target_channel}/messages", headers=API_HEADERS, json={"embeds": [embed]})

        requests.delete(f"https://discord.com/api/v10/channels/{CHANNEL_ID_BOT_EDIT}/messages/{msg['id']}", headers=API_HEADERS)

    if not instruction_found:
        inst_embed = {
            "title": "⚙️ INSTRUKCJA OBSŁUGI - PANEL ADMINA",
            "description": (
                "Ten kanał służy do wysyłania ogłoszeń i changelogów przez bota.\n\n"
                "**Jak to działa?**\n"
                "Napisz wiadomość zaczynając od odpowiedniego polecenia:\n"
                "`!ogloszenie [twoja treść]`\n"
                "`!changelog [twoja treść]`\n\n"
                "**Przykład:**\n"
                "> !ogloszenie Dziś o 20:00 wielki restart i event!\n\n"
                "*Bot automatycznie przeczyta wiadomość, sformatuje ją, wyśle na odpowiedni kanał "
                "i usunie twój oryginalny wpis z tego kanału, aby utrzymać tu porządek.*"
            ),
            "color": 0x333333
        }
        requests.post(f"https://discord.com/api/v10/channels/{CHANNEL_ID_BOT_EDIT}/messages", headers=API_HEADERS, json={"embeds": [inst_embed]})

if __name__ == "__main__":
    if CHANNEL_ID_STATUS:
        status_payload = build_status_payload()
        update_static_message(CHANNEL_ID_STATUS, status_payload)
        
    rules_payload = build_rules_payload()
    update_static_message(CHANNEL_ID_RULES, rules_payload)
    
    enforce_clean_channel(CHANNEL_ID_ANNOUNCEMENTS)
    enforce_clean_channel(CHANNEL_ID_CHANGELOG)
    
    process_bot_edit_commands()
