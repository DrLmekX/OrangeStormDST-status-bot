import os
import requests
import gzip
import json
from datetime import datetime
import pytz

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_STATUS = os.environ.get('CHANNEL_ID')
CHANNEL_ID_RULES = "1423988013813207164"

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

def build_status_payload():
    global_cdn_servers = get_servers_from_klei_cdn()
    embeds = []

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
        
        extra_spaces = max(0, 16 - len(srv['password']))
        spacer = "\u2800" * (32 + extra_spaces)
        
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

def update_discord_message(channel_id, payload):
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    url_get = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    response = requests.get(url_get, headers=headers)
    
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
        requests.patch(url_patch, headers=headers, json=payload)
    else:
        url_post = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        requests.post(url_post, headers=headers, json=payload)

if __name__ == "__main__":
    status_payload = build_status_payload()
    if CHANNEL_ID_STATUS:
        update_discord_message(CHANNEL_ID_STATUS, status_payload)
        
    rules_payload = build_rules_payload()
    update_discord_message(CHANNEL_ID_RULES, rules_payload)
