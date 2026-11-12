import os
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import TimedOut, NetworkError
from telegram.request import HTTPXRequest

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
SMSBOWER_API_KEY = os.getenv("SMSBOWER_API_KEY", "YOUR_API_KEY_HERE")

API_URL = "https://smsbower.page/stubs/handler_api.php"
DB_FILE = "activations.json"
SETTINGS_FILE = "settings.json"

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

# 📌 Country ID থেকে নাম খোঁজার জন্য রিভার্স ডিকশনারি
COUNTRY_ID_MAP = {id_code: name for id_code, name in COUNTRY_LIST.values()}

DEFAULT_MULTI_COUNTRIES = [
    {"id": "39", "name": "Argentina", "max_price": 0.35, "prefix": ""},
    {"id": "117", "name": "Portugal", "max_price": 0.30, "prefix": ""},
]

@dataclass
class UserState:
    country: str = "1003"
    country_name: str = "Bermuda"
    service: str = "tg"
    max_price: float = 0.0
    prefix: str = ""
    awaiting_input: str = ""
    multi_countries: List[dict] = field(default_factory=lambda: list(DEFAULT_MULTI_COUNTRIES))

auto_tasks = {}
poll_tasks = {}
http_session: aiohttp.ClientSession = None
session_lock = asyncio.Lock()

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

def find_country(input_text: str):
    """নাম অথবা Country ID দুটো দিয়েই দেশ খুঁজে বের করার লজিক"""
    query = input_text.strip().lower()
    
    # ১. যদি ইউজার সরাসরি ID টাইপ করে (যেমন: 12 বা 33)
    if query in COUNTRY_ID_MAP:
        return query, COUNTRY_ID_MAP[query]
    
    # ২. যদি ইউজার দেশের নাম টাইপ করে (যেমন: USA বা Colombia)
    if query in COUNTRY_LIST:
        return COUNTRY_LIST[query]
    
    return None, None

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def add_activation(record):
    data = load_db()
    data.append(record)
    save_db(data)

def update_activation(act_id, **kwargs):
    data = load_db()
    for item in data:
        if item.get("id") == act_id:
            item.update(kwargs)
            break
    save_db(data)

async def api_async(params):
    global http_session
    async with session_lock:
        if http_session is None or http_session.closed:
            http_session = aiohttp.ClientSession()
            
    params["api_key"] = SMSBOWER_API_KEY
    try:
        async with http_session.get(API_URL, params=params, timeout=10) as resp:
            return (await resp.text()).strip()
    except Exception as e:
        return f"ERROR: {e}"

def bottom_keyboard():
    kb = [
        [KeyboardButton("▶️ Start"), KeyboardButton("▶️ Single Auto"), KeyboardButton("🌐 Multi Auto")],
        [KeyboardButton("🛑 Stop"), KeyboardButton("🌐 Manage Multi List"), KeyboardButton("🌍 Single Country")],
        [KeyboardButton("🔢 Single Prefix"), KeyboardButton("💰 Max Price"), KeyboardButton("📲 Service")],
        [KeyboardButton("💳 Balance"), KeyboardButton("📊 History (24h)")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def initial_inline_keyboard(act_id):
    kb = [
        [InlineKeyboardButton("🔄 Another OTP", callback_data=f"another_{act_id}"), InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{act_id}")]
    ]
    return InlineKeyboardMarkup(kb)

def otp_received_keyboard(act_id, latest_code):
    kb = [
        [InlineKeyboardButton(f"📋 Copy OTP ({latest_code})", callback_data=f"copy_{latest_code}")],
        [InlineKeyboardButton("🔄 Another OTP", callback_data=f"another_{act_id}"), InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{act_id}")]
    ]
    return InlineKeyboardMarkup(kb)

async def show_start_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = get_state(update.effective_user.id)
    st.awaiting_input = ""
    save_settings(user_settings)
    
    country_disp = getattr(st, "country_name", st.country)
    price_disp = "Not Set" if st.max_price == 0 else f"${st.max_price}"
    prefix_disp = st.prefix if st.prefix else "ALL (No Filter)"
    
    msg = (
        f"🤖 **SMSBower Bot Dashboard**\n\n"
        f"🌍 **Single Country:** `{country_disp}` (ID: `{st.country}`)\n"
        f"🔢 **Single Prefix:** `{prefix_disp}`\n"
        f"📲 **Service:** `{st.service.upper()}`\n"
        f"💰 **Single Max Price:** `{price_disp}`\n"
        f"🌐 **Multi List Total:** `{len(st.multi_countries)} Countries`\n\n"
        f"Choose an option below:"
    )
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=bottom_keyboard())

async def poll_code(app, act_id, number, price, chat_id, message_id):
    formatted_number = f"+{number}" if not str(number).startswith("+") else number
    codes_list = []
    max_checks = 600
    check_count = 0
    
    while check_count < max_checks:
        check_count += 1
        try:
            res = await api_async({"action": "getStatus", "id": act_id})
            if "STATUS_OK" in res:
                new_code = res.split(":")[-1].strip()
                if not codes_list or codes_list[-1] != new_code:
                    codes_list.append(new_code)
                    update_activation(act_id, status="code_received", codes=codes_list, received_at=datetime.now(timezone.utc).isoformat())
                    otp_text = "\n".join([f"🔑 **OTP {idx+1}:** `{code}`" for idx, code in enumerate(codes_list)])
                    try:
                        await app.bot.edit_message_text(
                            chat_id=chat_id, message_id=message_id,
                            text=(
                                f"📱 **New Number Purchased!**\n\n"
                                f"📞 **Number:** `{formatted_number}`\n"
                                f"💰 **Price:** `{price}`\n\n"
                                f"{otp_text}"
                            ),
                            parse_mode="Markdown", reply_markup=otp_received_keyboard(act_id, new_code)
                        )
                    except Exception:
                        pass
            elif "STATUS_CANCEL" in res or "STATUS_FINISH" in res:
                update_activation(act_id, status="finished")
                break
        except asyncio.CancelledError:
            break
        except (NetworkError, TimedOut, Exception):
            pass
        await asyncio.sleep(2)

async def auto_loop(app, user_id, chat_id):
    while auto_tasks.get(user_id, False):
        try:
            st = get_state(user_id)
            if st.max_price <= 0:
                await app.bot.send_message(chat_id, "⚠️ **Please set Max Price first!**", parse_mode="Markdown")
                auto_tasks[user_id] = False
                break

            params = {
                "action": "getNumber",
                "service": st.service,
                "country": st.country,
                "maxPrice": str(st.max_price)
            }

            if hasattr(st, 'prefix') and st.prefix.strip():
                clean_prefixes = [p.strip() for p in st.prefix.replace(" ", "").split(",") if p.strip()]
                if clean_prefixes:
                    params["prefix"] = ",".join(clean_prefixes)

            res = await api_async(params)

            if res.startswith("ACCESS_NUMBER"):
                parts = res.split(":")
                act_id = parts[1]
                raw_number = parts[2]
                formatted_number = f"+{raw_number}" if not raw_number.startswith("+") else raw_number
                actual_price = parts[3] if len(parts) > 3 else f"≤${st.max_price}"

                if hasattr(st, 'prefix') and st.prefix.strip():
                    prefixes = [p.strip() for p in st.prefix.replace(" ", "").split(",") if p.strip()]
                    matched = any(raw_number.startswith(p) or raw_number.removeprefix("+").startswith(p) for p in prefixes)
                    
                    if not matched:
                        asyncio.create_task(api_async({"action": "setStatus", "id": act_id, "status": 8}))
                        await asyncio.sleep(1)
                        continue

                add_activation({
                    "id": act_id, "number": formatted_number, "country": st.country,
                    "service": st.service, "price": actual_price, "status": "waiting_code",
                    "codes": [], "created_at": datetime.now(timezone.utc).isoformat()
                })

                msg = await app.bot.send_message(
                    chat_id,
                    f"📱 **New Number Purchased!**\n\n📞 **Number:** `{formatted_number}`\n💰 **Price:** `{actual_price}`\n⏳ Waiting for OTP...",
                    parse_mode="Markdown", reply_markup=initial_inline_keyboard(act_id)
                )
                poll_tasks[act_id] = asyncio.create_task(poll_code(app, act_id, formatted_number, actual_price, chat_id, msg.message_id))
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(1.5)
        except (NetworkError, TimedOut, Exception):
            await asyncio.sleep(3)

async def multi_auto_loop(app, user_id, chat_id):
    while auto_tasks.get(user_id, False):
        try:
            st = get_state(user_id)
            if not st.multi_countries:
                await app.bot.send_message(chat_id, "⚠️ **Multi Country List is empty!** Add countries first.", parse_mode="Markdown")
                auto_tasks[user_id] = False
                break

            bought = False
            for c in st.multi_countries:
                if not auto_tasks.get(user_id, False):
                    break

                params = {
                    "action": "getNumber",
                    "service": st.service,
                    "country": c["id"],
                    "maxPrice": str(c["max_price"])
                }
                if c.get("prefix"):
                    params["prefix"] = c["prefix"]

                res = await api_async(params)

                if res.startswith("ACCESS_NUMBER"):
                    parts = res.split(":")
                    act_id = parts[1]
                    raw_number = parts[2]
                    formatted_number = f"+{raw_number}" if not raw_number.startswith("+") else raw_number
                    actual_price = parts[3] if len(parts) > 3 else f"≤${c['max_price']}"

                    if c.get("prefix"):
                        prefixes = [p.strip() for p in c["prefix"].replace(" ", "").split(",") if p.strip()]
                        matched = any(raw_number.startswith(p) or raw_number.removeprefix("+").startswith(p) for p in prefixes)
                        
                        if not matched:
                            asyncio.create_task(api_async({"action": "setStatus", "id": act_id, "status": 8}))
                            await asyncio.sleep(1)
                            continue

                    add_activation({
                        "id": act_id, "number": formatted_number, "country": c["name"],
                        "service": st.service, "price": actual_price, "status": "waiting_code",
                        "codes": [], "created_at": datetime.now(timezone.utc).isoformat()
                    })

                    msg = await app.bot.send_message(
                        chat_id,
                        f"📱 **New Number Purchased! ({c['name']})**\n\n📞 **Number:** `{formatted_number}`\n💰 **Price:** `{actual_price}`\n⏳ Waiting for OTP...",
                        parse_mode="Markdown", reply_markup=initial_inline_keyboard(act_id)
                    )
                    poll_tasks[act_id] = asyncio.create_task(poll_code(app, act_id, formatted_number, actual_price, chat_id, msg.message_id))
                    bought = True
                    await asyncio.sleep(1)
                    break 

            if not bought:
                await asyncio.sleep(1.5)
        except (NetworkError, TimedOut, Exception):
            await asyncio.sleep(3)

async def handle_inline_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("cancel_"):
        await query.answer("Cancelling activation...")
        act_id = data.split("_")[1]
        asyncio.create_task(api_async({"action": "setStatus", "id": act_id, "status": 8}))
        update_activation(act_id, status="cancelled")
        if act_id in poll_tasks:
            poll_tasks[act_id].cancel()
            del poll_tasks[act_id]
        try:
            await query.edit_message_text(f"❌ **Activation cancelled!**", parse_mode="Markdown")
        except Exception:
            pass

    elif data.startswith("another_"):
        await query.answer("Requesting another OTP...")
        act_id = data.split("_")[1]
        asyncio.create_task(api_async({"action": "setStatus", "id": act_id, "status": 3}))
        update_activation(act_id, status="waiting_another_code")

    elif data.startswith("copy_"):
        code = data.split("_")[1]
        await query.answer(f"Copied Code: {code}", show_alert=True)

    elif data == "prompt_add_multi":
        await query.answer()
        st = get_state(query.from_user.id)
        st.awaiting_input = "add_multi"
        save_settings(user_settings)
        if query.message:
            await query.message.reply_text(
                "➕ **To ADD or UPDATE a country, reply in this format:**\n"
                "`CountryNameOrID MaxPrice Prefix(Optional)`\n\n"
                "Examples:\n"
                "• `12 0.35` (ID 12 - USA Virtual)\n"
                "• `Argentina 0.35` (Name - Argentina)\n"
                "• `33 0.35 57300` (ID 33 - Colombia with Prefix)",
                parse_mode="Markdown"
            )

    elif data.startswith("del_multi_"):
        await query.answer()
        c_id = data.split("_")[2]
        st = get_state(query.from_user.id)
        st.multi_countries = [c for c in st.multi_countries if str(c["id"]) != str(c_id)]
        save_settings(user_settings)
        await show_manage_multi_menu(query, context, edit=True)

async def show_manage_multi_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE, edit=False):
    user_id = update_or_query.from_user.id if hasattr(update_or_query, "from_user") else update_or_query.effective_user.id
    st = get_state(user_id)
    
    msg_text = "🌐 **Multi-Country List Management**\n━━━━━━━━━━━━━━━━━━━━\n"
    inline_kb = []

    if not st.multi_countries:
        msg_text += "❌ List is currently empty!\n"
    else:
        for c in st.multi_countries:
            pf_str = f" | Prefix: `{c['prefix']}`" if c.get("prefix") else ""
            msg_text += f"• **{c['name']}**: `${c['max_price']}`{pf_str} (ID: `{c['id']}`)\n"
            inline_kb.append([InlineKeyboardButton(f"❌ Remove {c['name']}", callback_data=f"del_multi_{c['id']}")])

    inline_kb.append([InlineKeyboardButton("➕ Add / Update Country", callback_data="prompt_add_multi")])
    msg_text += "\n👇 Click options below to edit:"
    reply_markup = InlineKeyboardMarkup(inline_kb)

    if edit and hasattr(update_or_query, "edit_message_text"):
        await update_or_query.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(msg_text, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_bottom_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id
    cid = update.effective_chat.id
    st = get_state(uid)

    main_buttons = [
        "▶️ Start", "▶️ Single Auto", "🌐 Multi Auto", "🛑 Stop", 
        "🌐 Manage Multi List", "🌍 Single Country", "🔢 Single Prefix",
        "💰 Max Price", "📲 Service", "💳 Balance", "📊 History (24h)", "/start"
    ]

    if text in main_buttons:
        if text not in ["🌐 Manage Multi List", "💰 Max Price", "🌍 Single Country", "🔢 Single Prefix", "📲 Service"]:
            st.awaiting_input = ""
            save_settings(user_settings)

    elif st.awaiting_input:
        if st.awaiting_input == "price":
            try:
                st.max_price = float(text)
                st.awaiting_input = ""
                save_settings(user_settings)
                await update.message.reply_text(f"✅ **Single Max Price set to:** `${st.max_price}`", parse_mode="Markdown", reply_markup=bottom_keyboard())
            except ValueError:
                await update.message.reply_text("❌ Invalid price number!")
            return

        elif st.awaiting_input == "prefix":
            if text.lower() in ["off", "remove", "all", "none", "0"]:
                st.prefix = ""
                msg_out = "✅ **Single Prefix Removed!** Now buying ALL prefixes."
            else:
                cleaned_prefix = text.replace(" ", "")
                st.prefix = cleaned_prefix
                msg_out = f"✅ **Single Prefix Set To:** `{cleaned_prefix}`"
            
            st.awaiting_input = ""
            save_settings(user_settings)
            await update.message.reply_text(msg_out, parse_mode="Markdown", reply_markup=bottom_keyboard())
            return

        elif st.awaiting_input == "country":
            cid_code, cname = find_country(text)
            if cid_code and cname:
                st.country = cid_code
                st.country_name = cname
                st.awaiting_input = ""
                save_settings(user_settings)
                await update.message.reply_text(f"✅ **Country set to:** `{cname}` (ID: `{cid_code}`)", parse_mode="Markdown", reply_markup=bottom_keyboard())
            else:
                await update.message.reply_text("❌ Country Name or ID not found!")
            return

        elif st.awaiting_input == "add_multi":
            try:
                parts = text.split()
                if len(parts) == 2:
                    c_input, mprice_str = parts[0], parts[1]
                    prefix_input = ""
                elif len(parts) >= 3:
                    c_input, mprice_str = parts[0], parts[1]
                    prefix_input = parts[2].strip()
                else:
                    raise ValueError("Invalid format")

                mprice = float(mprice_str)
                cid_code, cname = find_country(c_input)

                if cid_code and cname:
                    st.multi_countries = [c for c in st.multi_countries if str(c["id"]) != str(cid_code)]
                    st.multi_countries.append({"id": cid_code, "name": cname, "max_price": mprice, "prefix": prefix_input})
                    st.awaiting_input = ""
                    save_settings(user_settings)
                    pf_msg = f" | Prefix: `{prefix_input}`" if prefix_input else " | Prefix: All"
                    await update.message.reply_text(f"✅ **Successfully saved:** `{cname}` (ID: `{cid_code}`) - `${mprice}`{pf_msg}", parse_mode="Markdown", reply_markup=bottom_keyboard())
                else:
                    await update.message.reply_text("❌ Country Name or ID not found!")
            except Exception:
                await update.message.reply_text(
                    "❌ **Invalid format!** Write like this:\n"
                    "• `12 0.35` (ID 12 - USA Virtual)\n"
                    "• `Argentina 0.35` (Country Name)\n"
                    "• `33 0.35 57300` (ID 33 - Colombia with Prefix)",
                    parse_mode="Markdown"
                )
            return

        elif st.awaiting_input == "service":
            st.service = text.lower()
            st.awaiting_input = ""
            save_settings(user_settings)
            await update.message.reply_text(f"✅ **Service set to:** `{st.service.upper()}`", parse_mode="Markdown", reply_markup=bottom_keyboard())
            return

    if text in ["▶️ Start", "/start"]:
        await show_start_menu(update, context)

    elif text == "▶️ Single Auto":
        auto_tasks[uid] = False
        await asyncio.sleep(0.3)
        auto_tasks[uid] = True
        await update.message.reply_text("🚀 **Single Country Auto Search Started!**", parse_mode="Markdown", reply_markup=bottom_keyboard())
        asyncio.create_task(auto_loop(context.application, uid, cid))

    elif text == "🌐 Multi Auto":
        auto_tasks[uid] = False
        await asyncio.sleep(0.3)
        auto_tasks[uid] = True
        await update.message.reply_text("🚀 **Multi-Country Auto Search Started!**", parse_mode="Markdown", reply_markup=bottom_keyboard())
        asyncio.create_task(multi_auto_loop(context.application, uid, cid))

    elif text == "🛑 Stop":
        auto_tasks[uid] = False
        await update.message.reply_text("🛑 **Auto search stopped.**", parse_mode="Markdown", reply_markup=bottom_keyboard())

    elif text == "🌐 Manage Multi List":
        st.awaiting_input = "add_multi"
        save_settings(user_settings)
        await show_manage_multi_menu(update, context)

    elif text == "🔢 Single Prefix":
        st.awaiting_input = "prefix"
        save_settings(user_settings)
        await update.message.reply_text(
            "💬 **Reply with Number Prefix(es):**\n\n"
            "• Single Prefix: `58424`\n"
            "• Multiple Prefixes: `58424,58414`\n"
            "• Remove Prefix (All): Type `off` or `all`",
            parse_mode="Markdown"
        )

    elif text == "💰 Max Price":
        st.awaiting_input = "price"
        save_settings(user_settings)
        await update.message.reply_text("💬 **Reply with Single Country Max Price** (e.g., `0.30`):", parse_mode="Markdown")

    elif text == "🌍 Single Country":
        st.awaiting_input = "country"
        save_settings(user_settings)
        await update.message.reply_text("💬 **Reply with Country Name or ID** (e.g., `12`, `33`, `Colombia`):", parse_mode="Markdown")

    elif text == "📲 Service":
        st.awaiting_input = "service"
        save_settings(user_settings)
        await update.message.reply_text("💬 **Enter Service Code** (e.g. `tg`, `wa`):", parse_mode="Markdown")

    elif text == "💳 Balance":
        res = await api_async({"action": "getBalance"})
        if "ACCESS_BALANCE" in res:
            bal = res.split(":")[-1]
            await update.message.reply_text(f"💳 **Your Balance:** `${bal}`", parse_mode="Markdown", reply_markup=bottom_keyboard())

    elif text == "📊 History (24h)":
        db = load_db()
        now = datetime.now(timezone.utc)
        twenty_four_hours_ago = now - timedelta(hours=24)
        
        recent_otps = []
        for rec in db:
            if rec.get("codes"):
                time_str = rec.get("received_at", rec.get("created_at"))
                dt = datetime.fromisoformat(time_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt >= twenty_four_hours_ago:
                    recent_otps.append(rec)

        if not recent_otps:
            await update.message.reply_text("📊 **No OTPs in last 24h.**", parse_mode="Markdown", reply_markup=bottom_keyboard())
            return

        report_text = f"📊 **Last 24 Hours OTP Report ({len(recent_otps)})**\n━━━━━━━━━━━━━━━━━━━━\n"
        for idx, item in enumerate(recent_otps[-20:], 1):
            codes_str = ", ".join(item.get('codes', []))
            report_text += f"{idx}. 📞 `{item.get('number')}` | 🔑 `{codes_str}` | 💰 `{item.get('price')}`\n"
        await update.message.reply_text(report_text, parse_mode="Markdown", reply_markup=bottom_keyboard())

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, (NetworkError, TimedOut)):
        pass
    else:
        print(f"Update {update} caused error {context.error}")

async def shutdown(application):
    global http_session
    if http_session and not http_session.closed:
        await http_session.close()

def main():
    t_request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0, pool_timeout=30.0)
    app = Application.builder().token(BOT_TOKEN).request(t_request).post_shutdown(shutdown).build()
    
    app.add_handler(CommandHandler("start", show_start_menu))
    app.add_handler(CallbackQueryHandler(handle_inline_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bottom_buttons))
    app.add_error_handler(error_handler)
    
    print("🤖 Bot with Country ID & Prefix support is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
