import os
import json
import html
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, TypeHandler, ApplicationHandlerStop, filters, ContextTypes
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest

try:
    # python-telegram-bot v22.1+ : one-tap copy button
    from telegram import CopyTextButton
except Exception:
    CopyTextButton = None

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SMSBOWER_API_KEY = os.getenv("SMSBOWER_API_KEY", "YOUR_API_KEY_HERE")

# 🔒 Only this Telegram ID can use the bot. Put your own ID below.
OWNER_ID = 5253876797
ALLOWED_IDS = {OWNER_ID}

API_URL = "https://smsbower.page/stubs/handler_api.php"
DB_FILE = "activations.json"
SETTINGS_FILE = "settings.json"

# ============================ ⚙️ TUNING SETTINGS ============================
LOCAL_TZ = timezone(timedelta(hours=6))   # Asia/Dhaka (UTC+6)

SEARCH_DELAY = 0.3          # wait between searches when no number is found (lower = faster)
BUY_COOLDOWN = 0.15         # pause after a successful buy
POLL_INTERVAL = 1.0         # how often to check for a new OTP (seconds)
POLL_TIMEOUT = 20 * 60      # max seconds to wait for OTP per number
API_TIMEOUT = 8             # API request timeout (seconds)

# 🗑 Auto-delete (seconds). Use None or -1 to disable
NOTIFY_DELETE_SECONDS = 8         # small status messages (Saved, Started, Stopped...)
PROMPT_DELETE_SECONDS = 120       # input prompts
INFO_DELETE_SECONDS = 30 * 60     # Home / History / Multi List messages (30 min)
NUMBER_MSG_DELETE_SECONDS = 30 * 60   # number+OTP message, 30 min after it finishes (None = never)
DELETE_USER_MESSAGES = True       # delete your own button presses / inputs instantly
# ========================================================================

COUNTRY_LIST = {
    "afghanistan": ("74", "Afghanistan"), "albania": ("155", "Albania"), "algeria": ("58", "Algeria"),
    "angola": ("76", "Angola"), "anguilla": ("181", "Anguilla"), "antigua and barbuda": ("169", "Antigua and Barbuda"),
    "argentina": ("39", "Argentina"), "armenia": ("148", "Armenia"), "aruba": ("179", "Aruba"),
    "australia": ("175", "Australia"), "austria": ("50", "Austria"), "azerbaijan": ("35", "Azerbaijan"),
    "bahamas": ("122", "Bahamas"), "bahrain": ("145", "Bahrain"), "bangladesh": ("60", "Bangladesh"),
    "barbados": ("118", "Barbados"), "belarus": ("51", "Belarus"), "belgium": ("82", "Belgium"),
    "belize": ("124", "Belize"), "benin": ("120", "Benin"), "bermuda": ("1003", "Bermuda"),
    "bhutan": ("158", "Bhutan"), "bolivia": ("92", "Bolivia"), "bosnia and herzegovina": ("108", "Bosnia and Herzegovina"),
    "botswana": ("123", "Botswana"), "brazil": ("73", "Brazil"), "brunei darussalam": ("121", "Brunei Darussalam"),
    "bulgaria": ("83", "Bulgaria"), "burkina faso": ("152", "Burkina Faso"), "burundi": ("119", "Burundi"),
    "central african republic": ("125", "Central African Republic"), "cambodia": ("24", "Cambodia"),
    "cameroon": ("41", "Cameroon"), "canada": ("36", "Canada"), "cape verde": ("186", "Cape Verde"),
    "cayman islands": ("170", "Cayman Islands"), "chad": ("42", "Chad"), "chile": ("151", "Chile"),
    "china": ("3", "China"), "colombia": ("33", "Colombia"), "comoros": ("133", "Comoros"),
    "congo": ("150", "Congo"), "congo (dem. republic)": ("18", "Congo (Dem. Republic)"),
    "costa rica": ("93", "Costa Rica"), "cote d`ivoire ivory coast": ("27", "Cote d`Ivoire Ivory Coast"),
    "croatia": ("45", "Croatia"), "cuba": ("113", "Cuba"), "cyprus": ("77", "Cyprus"),
    "czech republic": ("63", "Czech Republic"), "denmark": ("172", "Denmark"), "djibouti": ("168", "Djibouti"),
    "dominica": ("126", "Dominica"), "dominican republic": ("109", "Dominican Republic"),
    "ecuador": ("105", "Ecuador"), "egypt": ("21", "Egypt"), "el salvador": ("101", "El Salvador"),
    "equatorial guinea": ("167", "Equatorial Guinea"), "eritrea": ("176", "Eritrea"), "estonia": ("34", "Estonia"),
    "ethiopia": ("71", "Ethiopia"), "fiji": ("189", "Fiji"), "finland": ("163", "Finland"),
    "france": ("78", "France"), "french guiana": ("162", "French Guiana"), "gabon": ("154", "Gabon"),
    "gambia": ("28", "Gambia"), "georgia": ("128", "Georgia"), "germany": ("43", "Germany"),
    "ghana": ("38", "Ghana"), "gibraltar": ("201", "Gibraltar"), "greece": ("129", "Greece"),
    "greenland": ("1008", "Greenland"), "grenada": ("127", "Grenada"), "guadeloupe": ("160", "Guadeloupe"),
    "guatemala": ("94", "Guatemala"), "guinea": ("68", "Guinea"), "guinea-bissau": ("130", "Guinea-Bissau"),
    "guyana": ("131", "Guyana"), "haiti": ("26", "Haiti"), "honduras": ("88", "Honduras"),
    "hong kong": ("14", "Hong Kong"), "hungary": ("84", "Hungary"), "iceland": ("132", "Iceland"),
    "india": ("22", "India"), "indonesia": ("6", "Indonesia"), "iran": ("57", "Iran"),
    "iraq": ("47", "Iraq"), "ireland": ("23", "Ireland"), "israel": ("13", "Israel"),
    "italy": ("86", "Italy"), "jamaica": ("103", "Jamaica"), "japan": ("1001", "Japan"),
    "jordan": ("116", "Jordan"), "kazakhstan": ("2", "Kazakhstan"), "kenya": ("8", "Kenya"),
    "korea": ("1002", "Korea"), "kosovo": ("1004", "Kosovo"), "kuwait": ("100", "Kuwait"),
    "kyrgyzstan": ("11", "Kyrgyzstan"), "lao people`s": ("25", "Lao People`s"), "latvia": ("49", "Latvia"),
    "lebanon": ("153", "Lebanon"), "lesotho": ("136", "Lesotho"), "liberia": ("135", "Liberia"),
    "libya": ("102", "Libya"), "liechtenstein": ("1005", "Liechtenstein"), "lithuania": ("44", "Lithuania"),
    "luxembourg": ("165", "Luxembourg"), "macau": ("20", "Macau"), "macedonia": ("183", "Macedonia"),
    "madagascar": ("17", "Madagascar"), "malawi": ("137", "Malawi"), "malaysia": ("7", "Malaysia"),
    "maldives": ("159", "Maldives"), "mali": ("69", "Mali"), "malta": ("199", "Malta"),
    "martinique": ("1011", "Martinique"), "mauritania": ("114", "Mauritania"), "mauritius": ("157", "Mauritius"),
    "mexico": ("54", "Mexico"), "moldova, republic of": ("85", "Moldova, Republic of"), "monaco": ("144", "Monaco"),
    "mongolia": ("72", "Mongolia"), "montenegro": ("171", "Montenegro"), "montserrat": ("180", "Montserrat"),
    "morocco": ("37", "Morocco"), "mozambique": ("80", "Mozambique"), "myanmar": ("5", "Myanmar"),
    "namibia": ("138", "Namibia"), "nepal": ("81", "Nepal"), "netherlands": ("48", "Netherlands"),
    "new caledonia": ("185", "New Caledonia"), "new zealand": ("67", "New Zealand"), "nicaragua": ("90", "Nicaragua"),
    "niger": ("139", "Niger"), "nigeria": ("19", "Nigeria"), "niue": ("204", "Niue"), "norway": ("174", "Norway"),
    "oman": ("107", "Oman"), "pakistan": ("66", "Pakistan"), "palestine": ("188", "Palestine"),
    "panama": ("112", "Panama"), "papua new gvineya": ("79", "Papua new gvineya"), "paraguay": ("87", "Paraguay"),
    "peru": ("65", "Peru"), "philippines": ("4", "Philippines"), "poland": ("15", "Poland"),
    "portugal": ("117", "Portugal"), "puerto rico": ("97", "Puerto Rico"), "qatar": ("111", "Qatar"),
    "reunion": ("146", "Reunion"), "romania": ("32", "Romania"), "russian federation": ("0", "Russian Federation"),
    "russia": ("0", "Russian Federation"), "rwanda": ("140", "Rwanda"), "saint kitts and nevis": ("134", "Saint Kitts and Nevis"),
    "saint lucia": ("164", "Saint Lucia"), "saint vincent": ("166", "Saint Vincent"),
    "sao tome and principe": ("178", "Sao Tome and Principe"), "saudi arabia": ("53", "Saudi Arabia"),
    "senegal": ("61", "Senegal"), "serbia": ("29", "Serbia"), "seychelles": ("184", "Seychelles"),
    "sierra leone": ("115", "Sierra Leone"), "singapore": ("196", "Singapore"), "sint maarten": ("1006", "Sint Maarten"),
    "slovakia": ("141", "Slovakia"), "slovenia": ("59", "Slovenia"), "somalia": ("149", "Somalia"),
    "south africa": ("31", "South Africa"), "south sudan": ("177", "South Sudan"), "spain": ("56", "Spain"),
    "sri lanka": ("64", "Sri Lanka"), "sudan": ("1010", "Sudan"), "suriname": ("142", "Suriname"),
    "swaziland": ("106", "Swaziland"), "sweden": ("46", "Sweden"), "switzerland": ("173", "Switzerland"),
    "syrian arab republic": ("1333", "Syrian Arab Republic"), "taiwan": ("55", "Taiwan"),
    "tajikistan": ("143", "Tajikistan"), "tanzania": ("9", "Tanzania"), "thailand": ("52", "Thailand"),
    "timor-leste": ("91", "Timor-Leste"), "togo": ("99", "Togo"), "trinidad and tobago": ("104", "Trinidad and Tobago"),
    "tunisia": ("89", "Tunisia"), "turkey": ("62", "Turkey"), "turkmenistan": ("161", "Turkmenistan"),
    "united arab emirates": ("95", "United Arab Emirates"), "uae": ("95", "United Arab Emirates"),
    "uganda": ("75", "Uganda"), "ukraine": ("1", "Ukraine"), "united kingdom": ("16", "United Kingdom"),
    "uk": ("16", "United Kingdom"), "uruguay": ("156", "Uruguay"), "united states": ("187", "United States"),
    "usa": ("187", "United States"), "united states (virtual)": ("12", "United States (virtual)"),
    "uzbekistan": ("40", "Uzbekistan"), "vanuatu": ("1007", "Vanuatu"), "venezuela": ("70", "Venezuela"),
    "viet nam": ("10", "Viet Nam"), "vietnam": ("10", "Viet Nam"), "yemen": ("30", "Yemen"),
    "zambia": ("147", "Zambia"), "zimbabwe": ("96", "Zimbabwe")
}

# 📌 Reverse lookup: country ID -> name
COUNTRY_ID_MAP = {id_code: name for id_code, name in COUNTRY_LIST.values()}

DEFAULT_MULTI_COUNTRIES = [
    {"id": "39", "name": "Argentina", "max_price": 0.35, "prefix": ""},
    {"id": "117", "name": "Portugal", "max_price": 0.30, "prefix": ""},
]

# ---- button labels ----
BTN_HOME = "🏠 Home"
BTN_CLEAR = "🧹 Clear All"
BTN_SINGLE_AUTO = "▶️ Single Auto"
BTN_MULTI_AUTO = "🌐 Multi Auto"
BTN_STOP = "🛑 Stop"
BTN_SINGLE_COUNTRY = "🌍 Single Country"
BTN_MANAGE = "🌐 Manage Multi List"
BTN_BALANCE = "💳 Balance"
BTN_HISTORY = "📊 History"
BTN_SERVICE = "📲 Service"

# old keyboard buttons still work if they are on screen
LEGACY_HOME = {"▶️ Start", "/start"}
LEGACY_HISTORY = {"📊 History (24h)"}
LEGACY_REMOVED = {"🔢 Single Prefix", "💰 Max Price"}

ALL_BUTTONS = {
    BTN_HOME, BTN_CLEAR, BTN_SINGLE_AUTO, BTN_MULTI_AUTO, BTN_STOP, BTN_SINGLE_COUNTRY,
    BTN_MANAGE, BTN_BALANCE, BTN_HISTORY, BTN_SERVICE,
} | LEGACY_HOME | LEGACY_HISTORY | LEGACY_REMOVED

# statuses that "Clear All" will cancel (active + expired + stuck)
CLEARABLE = {"waiting_code", "code_received", "waiting_another_code", "expired", "wrong_prefix"}


@dataclass
class UserState:
    country: str = "1003"
    country_name: str = "Bermuda"
    service: str = "tg"
    max_price: float = 0.0
    prefix: str = ""
    awaiting_input: str = ""
    multi_countries: List[dict] = field(default_factory=lambda: list(DEFAULT_MULTI_COUNTRIES))


# ----------------------------- GLOBAL STATE -----------------------------
auto_runs: Dict[int, dict] = {}       # uid -> {"mode": "single"/"multi", "id": int}
run_counter = 0
poll_tasks: Dict[str, asyncio.Task] = {}
act_meta: Dict[str, dict] = {}        # act_id -> live message data
info_msgs: Dict[tuple, int] = {}      # (uid, kind) -> message_id (replace old with new)
http_session: aiohttp.ClientSession = None
session_lock = asyncio.Lock()
_bg_tasks = set()


def spawn(coro):
    t = asyncio.create_task(coro)
    _bg_tasks.add(t)
    t.add_done_callback(_bg_tasks.discard)
    return t


def esc(x) -> str:
    return html.escape(str(x))


# ----------------------------- SETTINGS FILE -----------------------------
def load_settings() -> Dict[str, UserState]:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {k: UserState(**v) for k, v in raw.items()}
    except Exception:
        return {}


def save_settings(data: Dict[str, UserState]):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({k: asdict(v) for k, v in data.items()}, f, indent=2)


user_settings: Dict[str, UserState] = load_settings()


def get_state(user_id: int) -> UserState:
    uid = str(user_id)
    if uid not in user_settings:
        user_settings[uid] = UserState()
        save_settings(user_settings)
    return user_settings[uid]


# ----------------------------- COUNTRY LOOKUP / PARSE -----------------------------
def find_country(input_text: str):
    """Find a country by name or by ID"""
    query = input_text.strip().lower()
    if query in COUNTRY_ID_MAP:
        return query, COUNTRY_ID_MAP[query]
    if query in COUNTRY_LIST:
        return COUNTRY_LIST[query]
    return None, None


def clean_prefixes(prefix_str: str) -> List[str]:
    return [p for p in str(prefix_str or "").replace(" ", "").split(",") if p]


def parse_country_line(text: str):
    """'Colombia 0.35 57300' / '12 0.30' / 'United States 0.4 1,44' -> (id, name, price, prefix)"""
    tokens = text.split()
    for k in range(1, len(tokens)):
        cid, cname = find_country(" ".join(tokens[:k]))
        if not cid:
            continue
        try:
            price = float(tokens[k].replace(",", "."))
        except ValueError:
            continue
        if price <= 0:
            return None
        prefix = "".join(tokens[k + 1:])
        if prefix.lower() in ("off", "all", "none", "remove", "0"):
            prefix = ""
        return cid, cname, price, prefix
    return None


# ----------------------------- DATABASE (in-memory cache) -----------------------------
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


DB: List[dict] = load_db()


def save_db():
    tmp = DB_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(DB, f, indent=2)
        os.replace(tmp, DB_FILE)
    except Exception as e:
        print(f"DB save error: {e}")


def add_activation(record):
    DB.append(record)
    save_db()


def update_activation(act_id, **kwargs):
    for item in reversed(DB):
        if item.get("id") == act_id:
            item.update(kwargs)
            break
    save_db()


# ----------------------------- TIME FORMAT -----------------------------
def parse_iso(s):
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fmt_dt(dt: datetime) -> str:
    """Format like: Sat 3:45 PM (Dhaka time)"""
    l = dt.astimezone(LOCAL_TZ)
    return f"{l.strftime('%a')} {int(l.strftime('%I'))}:{l.strftime('%M %p')}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ----------------------------- API (fast, single shared session) -----------------------------
async def get_session():
    global http_session
    if http_session is None or http_session.closed:
        async with session_lock:
            if http_session is None or http_session.closed:
                http_session = aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(limit=100, keepalive_timeout=60, ttl_dns_cache=300),
                    timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
                )
    return http_session


async def api_async(params):
    params = dict(params)
    params["api_key"] = SMSBOWER_API_KEY
    try:
        session = await get_session()
        async with session.get(API_URL, params=params) as resp:
            return (await resp.text()).strip()
    except Exception as e:
        return f"ERROR: {e}"


# ----------------------------- MESSAGE HELPERS -----------------------------
async def _delete_later(bot, chat_id, msg_id, delay):
    if delay and delay > 0:
        await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, msg_id)
    except Exception:
        pass


def schedule_delete(bot, chat_id, msg_id, delay):
    if delay is None or delay < 0:
        return
    spawn(_delete_later(bot, chat_id, msg_id, delay))


async def notify(bot, chat_id, text, delay=NOTIFY_DELETE_SECONDS, markup=None):
    """Send a short message and auto-delete it after a while"""
    # NOTE: never attach the reply keyboard to auto-deleted messages,
    # deleting the message that carried it removes the keyboard from the chat.
    try:
        m = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
        schedule_delete(bot, chat_id, m.message_id, delay)
        return m
    except Exception:
        return None


async def send_info(bot, chat_id, uid, kind, text, markup=None, delay=INFO_DELETE_SECONDS):
    """Home/History/Manage: replace the previous message of the same kind"""
    old = info_msgs.pop((uid, kind), None)
    if old:
        schedule_delete(bot, chat_id, old, 0)
    try:
        m = await bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)
    except Exception:
        return None
    info_msgs[(uid, kind)] = m.message_id
    schedule_delete(bot, chat_id, m.message_id, delay)
    return m


# ----------------------------- KEYBOARD -----------------------------
def bottom_keyboard():
    kb = [
        [KeyboardButton(BTN_HOME), KeyboardButton(BTN_CLEAR)],
        [KeyboardButton(BTN_SINGLE_AUTO), KeyboardButton(BTN_MULTI_AUTO), KeyboardButton(BTN_STOP)],
        [KeyboardButton(BTN_SINGLE_COUNTRY), KeyboardButton(BTN_MANAGE)],
        [KeyboardButton(BTN_BALANCE), KeyboardButton(BTN_HISTORY), KeyboardButton(BTN_SERVICE)],
    ]
    try:
        return ReplyKeyboardMarkup(kb, resize_keyboard=True, is_persistent=True)
    except TypeError:
        return ReplyKeyboardMarkup(kb, resize_keyboard=True)


MENU_TEXT = "🤖 <b>SMSBower Bot</b>\nMenu is ready 👇"
menu_anchor: Dict[int, int] = {}   # chat_id -> permanent keyboard message id


async def send_menu(bot, chat_id):
    """Permanent message that carries the keyboard. It is never auto-deleted."""
    try:
        m = await bot.send_message(chat_id, MENU_TEXT, parse_mode="HTML", reply_markup=bottom_keyboard())
    except Exception:
        return
    old = menu_anchor.get(chat_id)
    menu_anchor[chat_id] = m.message_id
    if old:
        schedule_delete(bot, chat_id, old, 0)


def copy_button(code):
    label = f"📋 Copy OTP: {code}"
    if CopyTextButton is not None:
        return InlineKeyboardButton(label, copy_text=CopyTextButton(text=str(code)))
    return InlineKeyboardButton(label, callback_data=f"copy_{code}")


# ----------------------------- NUMBER MESSAGE -----------------------------
def build_number_text(meta: dict) -> str:
    title = "🟢 <b>New Number Purchased!</b>"
    if meta.get("country"):
        title += f" ({esc(meta['country'])})"
    lines = [
        title,
        "━━━━━━━━━━━━━━━━━━━━",
        f"📞 <b>Number:</b> <code>{esc(meta['number'])}</code>",
        f"💰 <b>Price:</b> <code>{esc(meta['price'])}</code>",
    ]
    for i, code in enumerate(meta["codes"]):
        t = ""
        if i < len(meta["times"]):
            dt = parse_iso(meta["times"][i])
            if dt:
                t = f"  🕒 {fmt_dt(dt)}"
        lines.append(f"🔑 <b>OTP {i + 1}:</b> <code>{esc(code)}</code>{t}")

    state = meta.get("state", "active")
    if state == "cancelled":
        lines.append("❌ <b>Cancelled</b>")
    elif state == "cleared":
        lines.append("🧹 <b>Cleared</b>")
    elif state == "finished":
        lines.append("✅ <b>Finished</b>")
    elif state == "expired":
        lines.append("⌛ <b>Expired</b>")
    elif meta.get("waiting"):
        lines.append("⏳ <b>Waiting for Another OTP...</b>")
    elif not meta["codes"]:
        lines.append("⏳ <b>Waiting for OTP...</b>")
    return "\n".join(lines)


def build_number_kb(meta: dict):
    state = meta.get("state", "active")
    rows = []
    if meta["codes"]:
        rows.append([copy_button(meta["codes"][-1])])
    if state == "active":
        if not meta["codes"]:
            rows.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{meta['id']}")])
        elif meta.get("waiting"):
            rows.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{meta['id']}")])
        else:
            rows.append([
                InlineKeyboardButton("🔄 Another OTP", callback_data=f"another_{meta['id']}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{meta['id']}"),
            ])
    return InlineKeyboardMarkup(rows) if rows else None


async def refresh_msg(app, meta: dict):
    try:
        await app.bot.edit_message_text(
            chat_id=meta["chat_id"], message_id=meta["message_id"],
            text=build_number_text(meta), parse_mode="HTML",
            reply_markup=build_number_kb(meta),
        )
    except Exception:
        pass


# ----------------------------- OTP POLLING -----------------------------
async def poll_code(app, act_id):
    meta = act_meta[act_id]
    loop = asyncio.get_running_loop()
    deadline = loop.time() + POLL_TIMEOUT
    ended_by = "timeout"

    while loop.time() < deadline:
        try:
            res = await api_async({"action": "getStatus", "id": act_id})
            if res.startswith("STATUS_OK"):
                new_code = res.split(":")[-1].strip()
                if not meta["codes"] or meta["codes"][-1] != new_code:
                    ts = now_iso()
                    meta["codes"].append(new_code)
                    meta["times"].append(ts)
                    meta["waiting"] = False
                    update_activation(
                        act_id, status="code_received", codes=list(meta["codes"]),
                        code_times=list(meta["times"]), received_at=ts,
                    )
                    await refresh_msg(app, meta)
            elif "STATUS_CANCEL" in res:
                ended_by = "cancel"
                break
            elif "STATUS_FINISH" in res:
                ended_by = "finish"
                break
        except asyncio.CancelledError:
            return
        except Exception:
            pass
        try:
            await asyncio.sleep(POLL_INTERVAL)
        except asyncio.CancelledError:
            return

    if meta.get("state") == "active":
        if ended_by == "finish":
            meta["state"] = "finished"
            update_activation(act_id, status="finished")
        elif ended_by == "cancel":
            meta["state"] = "finished" if meta["codes"] else "cancelled"
            update_activation(act_id, status="finished" if meta["codes"] else "cancelled")
        else:
            meta["state"] = "finished" if meta["codes"] else "expired"
            update_activation(act_id, status="finished" if meta["codes"] else "expired")
        meta["waiting"] = False
        await refresh_msg(app, meta)

    poll_tasks.pop(act_id, None)
    schedule_delete(app.bot, meta["chat_id"], meta["message_id"], NUMBER_MSG_DELETE_SECONDS)


async def cancel_retry(act_id, attempts=12, delay=10):
    """Wrong-prefix number: retry cancelling if early-cancel is denied"""
    for _ in range(attempts):
        res = await api_async({"action": "setStatus", "id": act_id, "status": 8})
        if not res.startswith("EARLY_CANCEL_DENIED") and not res.startswith("ERROR"):
            update_activation(act_id, status="cancelled")
            return
        await asyncio.sleep(delay)


# ----------------------------- BUYING -----------------------------
async def buy_request(service, country_id, max_price, prefix):
    params = {
        "action": "getNumber",
        "service": service,
        "country": country_id,
        "maxPrice": str(max_price),
    }
    prefixes = clean_prefixes(prefix)
    if prefixes:
        params["prefix"] = ",".join(prefixes)
    return await api_async(params)


async def process_purchase(app, chat_id, res, country_name, max_price, prefix, service, country_id):
    """Handle an ACCESS_NUMBER response. Returns True if the number is kept"""
    parts = res.split(":")
    act_id = parts[1]
    raw_number = parts[2]
    formatted_number = raw_number if raw_number.startswith("+") else f"+{raw_number}"
    actual_price = parts[3] if len(parts) > 3 else f"≤${max_price}"

    prefixes = clean_prefixes(prefix)
    if prefixes:
        plain = raw_number.lstrip("+")
        if not any(plain.startswith(p) for p in prefixes):
            add_activation({
                "id": act_id, "number": formatted_number, "country": country_name,
                "service": service, "price": actual_price, "status": "wrong_prefix",
                "codes": [], "created_at": now_iso(),
            })
            spawn(cancel_retry(act_id))
            return False

    add_activation({
        "id": act_id, "number": formatted_number, "country": country_name,
        "service": service, "price": actual_price, "status": "waiting_code",
        "codes": [], "code_times": [], "created_at": now_iso(),
    })

    meta = {
        "id": act_id, "number": formatted_number, "price": actual_price, "country": country_name,
        "codes": [], "times": [], "waiting": False, "state": "active",
        "chat_id": chat_id, "message_id": None,
    }
    act_meta[act_id] = meta
    try:
        msg = await app.bot.send_message(
            chat_id, build_number_text(meta), parse_mode="HTML", reply_markup=build_number_kb(meta)
        )
        meta["message_id"] = msg.message_id
    except Exception:
        # number is already bought even if the message failed, keep polling
        meta["message_id"] = 0
    poll_tasks[act_id] = spawn(poll_code(app, act_id))
    return True


def is_current(uid, run_id) -> bool:
    run = auto_runs.get(uid)
    return bool(run and run["id"] == run_id)


def is_fatal(res: str) -> bool:
    return any(res.startswith(x) for x in ("NO_BALANCE", "BAD_KEY", "BANNED"))


async def auto_loop(app, user_id, chat_id, run_id):
    while is_current(user_id, run_id):
        try:
            st = get_state(user_id)
            if st.max_price <= 0:
                await notify(app.bot, chat_id, "⚠️ <b>Set a Single Country first!</b>\nExample: <code>Colombia 0.35 57300</code>", delay=20)
                auto_runs.pop(user_id, None)
                break

            res = await buy_request(st.service, st.country, st.max_price, st.prefix)

            if res.startswith("ACCESS_NUMBER"):
                await process_purchase(app, chat_id, res, st.country_name, st.max_price, st.prefix, st.service, st.country)
                await asyncio.sleep(BUY_COOLDOWN)
            elif is_fatal(res):
                if is_current(user_id, run_id):
                    auto_runs.pop(user_id, None)
                await notify(app.bot, chat_id, f"🛑 <b>Auto stopped:</b> <code>{esc(res)}</code>", delay=60)
                break
            else:
                await asyncio.sleep(SEARCH_DELAY)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)


async def multi_auto_loop(app, user_id, chat_id, run_id):
    while is_current(user_id, run_id):
        try:
            st = get_state(user_id)
            if not st.multi_countries:
                await notify(app.bot, chat_id, "⚠️ <b>Multi Country List is empty!</b> Add countries first.", delay=20)
                auto_runs.pop(user_id, None)
                break

            countries = list(st.multi_countries)
            # request all countries in parallel
            results = await asyncio.gather(
                *[buy_request(st.service, c["id"], c["max_price"], c.get("prefix", "")) for c in countries],
                return_exceptions=True,
            )

            bought = False
            fatal = None
            for c, res in zip(countries, results):
                if isinstance(res, Exception) or not isinstance(res, str):
                    continue
                if res.startswith("ACCESS_NUMBER"):
                    ok = await process_purchase(
                        app, chat_id, res, c["name"], c["max_price"], c.get("prefix", ""), st.service, c["id"]
                    )
                    bought = bought or ok
                elif is_fatal(res):
                    fatal = res

            if fatal:
                if is_current(user_id, run_id):
                    auto_runs.pop(user_id, None)
                await notify(app.bot, chat_id, f"🛑 <b>Auto stopped:</b> <code>{esc(fatal)}</code>", delay=60)
                break

            await asyncio.sleep(BUY_COOLDOWN if bought else SEARCH_DELAY)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(1)


def start_auto(app, uid, chat_id, mode):
    global run_counter
    run_counter += 1
    run_id = run_counter
    auto_runs[uid] = {"mode": mode, "id": run_id}   # the old loop stops by itself
    loop_fn = auto_loop if mode == "single" else multi_auto_loop
    spawn(loop_fn(app, uid, chat_id, run_id))


# ----------------------------- HISTORY (today, Dhaka time) -----------------------------
def todays_entries():
    now_local = datetime.now(LOCAL_TZ)
    start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    entries = []
    for rec in DB:
        codes = rec.get("codes") or []
        times = rec.get("code_times") or []
        for i, code in enumerate(codes):
            ts = times[i] if i < len(times) else (rec.get("received_at") or rec.get("created_at"))
            dt = parse_iso(ts) if ts else None
            if dt and start <= dt.astimezone(LOCAL_TZ) < end:
                entries.append((dt, rec, code))
    entries.sort(key=lambda x: x[0], reverse=True)   # newest first
    return entries, start


async def show_history(app, uid, chat_id):
    entries, start = todays_entries()
    day_label = f"{start.strftime('%a')}, {start.day} {start.strftime('%b %Y')}"

    if not entries:
        await send_info(
            app.bot, chat_id, uid, "history",
            f"📊 <b>Today's OTP History</b> ({esc(day_label)})\n━━━━━━━━━━━━━━━━━━━━\n❌ No OTP received today yet.",
        )
        return

    header = f"📊 <b>Today's OTP History</b> ({esc(day_label)})\n🔢 Total: <b>{len(entries)}</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    blocks = []
    for idx, (dt, rec, code) in enumerate(entries, 1):
        blocks.append(
            f"{idx}. 📞 <code>{esc(rec.get('number'))}</code>\n"
            f"    🔑 <code>{esc(code)}</code>  🕒 {fmt_dt(dt)}  💰 {esc(rec.get('price'))}\n"
        )

    # split to stay under Telegram's 4096 limit
    chunks, cur = [], header
    for b in blocks:
        if len(cur) + len(b) > 3800:
            chunks.append(cur)
            cur = ""
        cur += b
    chunks.append(cur)

    old = info_msgs.pop((uid, "history"), None)
    if old:
        schedule_delete(app.bot, chat_id, old, 0)
    for n, chunk in enumerate(chunks):
        try:
            m = await app.bot.send_message(chat_id, chunk, parse_mode="HTML")
            schedule_delete(app.bot, chat_id, m.message_id, INFO_DELETE_SECONDS)
            if n == 0:
                info_msgs[(uid, "history")] = m.message_id
        except Exception:
            pass


# ----------------------------- Home / Dashboard -----------------------------
async def build_dashboard(uid) -> str:
    st = get_state(uid)
    run = auto_runs.get(uid)
    if run and run["mode"] == "single":
        status = "🟢 Single Auto running"
    elif run and run["mode"] == "multi":
        status = "🔵 Multi Auto running"
    else:
        status = "🔴 Stopped"

    bal_res = await api_async({"action": "getBalance"})
    balance = bal_res.split(":")[-1] if "ACCESS_BALANCE" in bal_res else "N/A"

    live = sum(1 for m in act_meta.values() if m.get("state") == "active")
    otps_today = len(todays_entries()[0])

    price_disp = "Not Set" if st.max_price == 0 else f"${st.max_price}"
    prefix_disp = st.prefix if st.prefix else "ALL"

    lines = [
        "🤖 <b>SMSBower Dashboard</b>",
        "━━━━━━━━━━━━━━━━━━━━",
        f"⚙️ <b>Status:</b> {status}",
        f"💳 <b>Balance:</b> <code>${esc(balance)}</code>",
        f"📲 <b>Service:</b> <code>{esc(st.service.upper())}</code>",
        f"📦 <b>Active Numbers:</b> <code>{live}</code>   🔑 <b>OTPs Today:</b> <code>{otps_today}</code>",
        "",
        "🌍 <b>Single Country</b>",
        f"   • {esc(st.country_name)} (ID: <code>{esc(st.country)}</code>)",
        f"   • 💰 <code>{esc(price_disp)}</code>   🔢 <code>{esc(prefix_disp)}</code>",
        "",
        f"🌐 <b>Multi List</b> ({len(st.multi_countries)} countries)",
    ]
    if st.multi_countries:
        for c in st.multi_countries:
            pf = f" | 🔢 <code>{esc(c['prefix'])}</code>" if c.get("prefix") else ""
            lines.append(f"   • {esc(c['name'])}: <code>${esc(c['max_price'])}</code>{pf}")
    else:
        lines.append("   • (empty)")
    return "\n".join(lines)


async def show_home(app, uid, chat_id):
    st = get_state(uid)
    st.awaiting_input = ""
    save_settings(user_settings)
    text = await build_dashboard(uid)
    await send_info(app.bot, chat_id, uid, "home", text)


# ----------------------------- MULTI LIST MANAGEMENT -----------------------------
def build_manage_view(uid):
    st = get_state(uid)
    text = "🌐 <b>Multi-Country List Management</b>\n━━━━━━━━━━━━━━━━━━━━\n"
    kb = []
    if not st.multi_countries:
        text += "❌ List is currently empty!\n"
    else:
        for c in st.multi_countries:
            pf = f" | 🔢 <code>{esc(c['prefix'])}</code>" if c.get("prefix") else ""
            text += f"• <b>{esc(c['name'])}</b>: <code>${esc(c['max_price'])}</code>{pf} (ID: <code>{esc(c['id'])}</code>)\n"
            kb.append([InlineKeyboardButton(f"❌ Remove {c['name']}", callback_data=f"del_multi_{c['id']}")])
    kb.append([InlineKeyboardButton("➕ Add / Update Country", callback_data="prompt_add_multi")])
    text += "\n👇 Use the options below to edit:"
    return text, InlineKeyboardMarkup(kb)


async def show_manage_multi_menu(app, uid, chat_id, query=None):
    text, markup = build_manage_view(uid)
    if query is not None:
        try:
            await query.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            pass
    else:
        await send_info(app.bot, chat_id, uid, "manage", text, markup=markup)


ADD_FORMAT_HELP = (
    "<code>Country Price Prefix(optional)</code>\n\n"
    "Examples:\n"
    "• <code>Argentina 0.35</code>\n"
    "• <code>12 0.35</code> (ID 12 - USA Virtual)\n"
    "• <code>33 0.35 57300</code> (Colombia + Prefix)\n"
    "• <code>Colombia 0.35 57300,57301</code> (multiple prefixes)"
)


# ----------------------------- Clear All -----------------------------
async def clear_all(app, uid, chat_id):
    auto_runs.pop(uid, None)   # also stop auto search

    targets = [r for r in DB if r.get("status") in CLEARABLE]
    sem = asyncio.Semaphore(10)

    async def one(rec):
        status = 6 if rec.get("codes") else 8   # finish if a code arrived, otherwise cancel
        async with sem:
            res = await api_async({"action": "setStatus", "id": rec["id"], "status": status})
        return rec, status, res

    results = await asyncio.gather(*[one(r) for r in targets]) if targets else []

    cancelled = finished = failed = 0
    edits = []
    for rec, status, res in results:
        act_id = rec["id"]
        if res.startswith("EARLY_CANCEL_DENIED") or res.startswith("ERROR"):
            failed += 1
            continue
        t = poll_tasks.pop(act_id, None)
        if t:
            t.cancel()
        if status == 6:
            finished += 1
            update_activation(act_id, status="finished")
        else:
            cancelled += 1
            update_activation(act_id, status="cancelled")
        meta = act_meta.get(act_id)
        if meta and meta.get("message_id"):
            meta["state"] = "cleared"
            meta["waiting"] = False
            edits.append(refresh_msg(app, meta))
            schedule_delete(app.bot, meta["chat_id"], meta["message_id"], 15)

    if edits:
        await asyncio.gather(*edits, return_exceptions=True)

    text = (
        "🧹 <b>Clear complete!</b>\n"
        f"❌ Cancelled: <b>{cancelled}</b>\n"
        f"✅ Finished (had OTP): <b>{finished}</b>"
    )
    if failed:
        text += f"\n⏳ <b>{failed}</b> could not be cancelled yet (too new). Press Clear again in a moment."
    if not targets:
        text = "🧹 No active numbers to clear."
    text += "\n🛑 Auto search stopped."
    await notify(app.bot, chat_id, text, delay=20)


# ----------------------------- INLINE BUTTON HANDLER -----------------------------
async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data or ""
    app = context.application
    uid = query.from_user.id

    if data.startswith("cancel_"):
        act_id = data.split("_", 1)[1]
        res = await api_async({"action": "setStatus", "id": act_id, "status": 8})
        if res.startswith("EARLY_CANCEL_DENIED"):
            await query.answer("⏳ Number is too new, try Cancel again in a moment.", show_alert=True)
            return
        await query.answer("❌ Cancelled")
        update_activation(act_id, status="cancelled")
        t = poll_tasks.pop(act_id, None)
        if t:
            t.cancel()
        meta = act_meta.get(act_id)
        if meta and meta.get("message_id"):
            meta["state"] = "cancelled"
            meta["waiting"] = False
            await refresh_msg(app, meta)
            schedule_delete(app.bot, meta["chat_id"], meta["message_id"], 30)
        else:
            try:
                await query.edit_message_text("❌ <b>Activation cancelled!</b>", parse_mode="HTML")
                if query.message:
                    schedule_delete(app.bot, query.message.chat_id, query.message.message_id, 30)
            except Exception:
                pass

    elif data.startswith("another_"):
        act_id = data.split("_", 1)[1]
        res = await api_async({"action": "setStatus", "id": act_id, "status": 3})
        if res.startswith("ACCESS") or "RETRY" in res:
            await query.answer("🔄 Waiting for another OTP...")
            update_activation(act_id, status="waiting_another_code")
            meta = act_meta.get(act_id)
            if meta:
                meta["waiting"] = True
                await refresh_msg(app, meta)
        else:
            await query.answer(f"⚠️ {res[:150]}", show_alert=True)

    elif data.startswith("copy_"):
        # fallback for older PTB: send the code as a tap-to-copy message
        code = data.split("_", 1)[1]
        await query.answer("Code sent below, tap it to copy ✅")
        if query.message:
            await notify(app.bot, query.message.chat_id, f"🔑 <code>{esc(code)}</code>", delay=60)

    elif data == "prompt_add_multi":
        await query.answer()
        st = get_state(uid)
        st.awaiting_input = "add_multi"
        save_settings(user_settings)
        if query.message:
            await notify(
                app.bot, query.message.chat_id,
                "➕ <b>To ADD / UPDATE a country, send:</b>\n" + ADD_FORMAT_HELP,
                delay=PROMPT_DELETE_SECONDS, markup=None,
            )

    elif data.startswith("del_multi_"):
        await query.answer()
        c_id = data.split("_")[2]
        st = get_state(uid)
        st.multi_countries = [c for c in st.multi_countries if str(c["id"]) != str(c_id)]
        save_settings(user_settings)
        await show_manage_multi_menu(app, uid, query.message.chat_id if query.message else None, query=query)

    else:
        await query.answer()


# ----------------------------- BOTTOM BUTTON / TEXT HANDLER -----------------------------
async def handle_bottom_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    text = (msg.text or "").strip()
    uid = update.effective_user.id
    cid = update.effective_chat.id
    app = context.application
    st = get_state(uid)

    if DELETE_USER_MESSAGES:
        schedule_delete(app.bot, cid, msg.message_id, 0)

    # ---- a button press cancels any pending input mode ----
    if text in ALL_BUTTONS:
        if text not in (BTN_MANAGE, BTN_SINGLE_COUNTRY, BTN_SERVICE):
            st.awaiting_input = ""
            save_settings(user_settings)

    # ---- waiting for typed input ----
    elif st.awaiting_input:
        mode = st.awaiting_input

        if mode == "single_country":
            parsed = parse_country_line(text)
            if parsed:
                cid_code, cname, price, prefix = parsed
                st.country, st.country_name = cid_code, cname
                st.max_price, st.prefix = price, prefix
                st.awaiting_input = ""
                save_settings(user_settings)
                pf = f"<code>{esc(prefix)}</code>" if prefix else "ALL"
                await notify(
                    app.bot, cid,
                    f"✅ <b>Single Country saved</b>\n🌍 <code>{esc(cname)}</code> (ID: <code>{esc(cid_code)}</code>)\n💰 <code>${price}</code>   🔢 {pf}",
                )
            else:
                await notify(
                    app.bot, cid,
                    "❌ <b>Invalid format!</b> Send:\n" + ADD_FORMAT_HELP, delay=30,
                )
            return

        elif mode == "add_multi":
            parsed = parse_country_line(text)
            if parsed:
                cid_code, cname, price, prefix = parsed
                st.multi_countries = [c for c in st.multi_countries if str(c["id"]) != str(cid_code)]
                st.multi_countries.append({"id": cid_code, "name": cname, "max_price": price, "prefix": prefix})
                st.awaiting_input = ""
                save_settings(user_settings)
                pf = f" | Prefix: <code>{esc(prefix)}</code>" if prefix else " | Prefix: All"
                await notify(
                    app.bot, cid,
                    f"✅ <b>Saved:</b> <code>{esc(cname)}</code> (ID: <code>{esc(cid_code)}</code>) - <code>${price}</code>{pf}",
                )
                await show_manage_multi_menu(app, uid, cid)
            else:
                await notify(app.bot, cid, "❌ <b>Invalid format!</b> Send:\n" + ADD_FORMAT_HELP, delay=30)
            return

        elif mode == "service":
            st.service = text.lower()
            st.awaiting_input = ""
            save_settings(user_settings)
            await notify(app.bot, cid, f"✅ <b>Service set to:</b> <code>{esc(st.service.upper())}</code>")
            return

    # ---- button actions ----
    if text in LEGACY_HOME or text == BTN_HOME:
        await show_home(app, uid, cid)

    elif text == BTN_SINGLE_AUTO:
        if st.max_price <= 0:
            await notify(
                app.bot, cid,
                "⚠️ Set <b>🌍 Single Country</b> first (country + price).\nExample: <code>Colombia 0.35 57300</code>",
                delay=20,
            )
        else:
            start_auto(app, uid, cid, "single")
            await notify(app.bot, cid, f"🚀 <b>Single Auto started!</b> 🌍 {esc(st.country_name)}")

    elif text == BTN_MULTI_AUTO:
        if not st.multi_countries:
            await notify(app.bot, cid, "⚠️ <b>Multi List is empty!</b> Add countries in <b>🌐 Manage Multi List</b> first.", delay=20)
        else:
            start_auto(app, uid, cid, "multi")
            await notify(app.bot, cid, f"🚀 <b>Multi Auto started!</b> 🌐 Searching {len(st.multi_countries)} countries in parallel")

    elif text == BTN_STOP:
        auto_runs.pop(uid, None)
        await notify(app.bot, cid, "🛑 <b>Auto search stopped.</b>")

    elif text == BTN_CLEAR:
        await clear_all(app, uid, cid)

    elif text == BTN_MANAGE:
        st.awaiting_input = "add_multi"
        save_settings(user_settings)
        await show_manage_multi_menu(app, uid, cid)

    elif text == BTN_SINGLE_COUNTRY:
        st.awaiting_input = "single_country"
        save_settings(user_settings)
        cur_price = "Not Set" if st.max_price == 0 else f"${st.max_price}"
        cur_pf = st.prefix if st.prefix else "ALL"
        await notify(
            app.bot, cid,
            "🌍 <b>Set Single Country, send:</b>\n" + ADD_FORMAT_HELP +
            f"\n\n📌 <b>Current:</b> {esc(st.country_name)} | {esc(cur_price)} | Prefix: {esc(cur_pf)}",
            delay=PROMPT_DELETE_SECONDS,
        )

    elif text == BTN_SERVICE:
        st.awaiting_input = "service"
        save_settings(user_settings)
        await notify(app.bot, cid, "📲 <b>Send the Service code</b> (e.g. <code>tg</code>, <code>wa</code>):", delay=PROMPT_DELETE_SECONDS)

    elif text == BTN_BALANCE:
        res = await api_async({"action": "getBalance"})
        if "ACCESS_BALANCE" in res:
            bal = res.split(":")[-1]
            await notify(app.bot, cid, f"💳 <b>Your Balance:</b> <code>${esc(bal)}</code>", delay=60)
        else:
            await notify(app.bot, cid, f"⚠️ <code>{esc(res)}</code>", delay=20)

    elif text in LEGACY_HISTORY or text == BTN_HISTORY:
        await show_history(app, uid, cid)

    elif text in LEGACY_REMOVED:
        await notify(
            app.bot, cid,
            "ℹ️ This button was removed. Use <b>🌍 Single Country</b> and send:\n<code>Colombia 0.35 57300</code>",
            delay=20,
        )


# ----------------------------- /start -----------------------------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if DELETE_USER_MESSAGES and update.message:
        schedule_delete(context.application.bot, update.effective_chat.id, update.message.message_id, 0)
    await send_menu(context.application.bot, update.effective_chat.id)
    await show_home(context.application, update.effective_user.id, update.effective_chat.id)


async def access_guard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """🔒 Silently block everyone except OWNER_ID"""
    user = update.effective_user
    if user is None or user.id not in ALLOWED_IDS:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except Exception:
                pass
        raise ApplicationHandlerStop


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, (NetworkError, TimedOut)):
        pass
    else:
        print(f"Update {update} caused error {context.error}")


async def post_init(application):
    # restore the keyboard automatically every time the bot starts
    await send_menu(application.bot, OWNER_ID)


async def shutdown(application):
    global http_session
    if http_session and not http_session.closed:
        await http_session.close()


def main():
    t_request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0, pool_timeout=30.0)
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(t_request)
        .concurrent_updates(True)
        .post_init(post_init)
        .post_shutdown(shutdown)
        .build()
    )

    # 🔒 runs first (group=-1)
    app.add_handler(TypeHandler(Update, access_guard), group=-1)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(handle_inline_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bottom_buttons))
    app.add_error_handler(error_handler)

    print("🤖 Bot is running... (Fast mode, Today History, Clear All, Auto-Delete)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
