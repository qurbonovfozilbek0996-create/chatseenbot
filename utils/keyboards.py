from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from database.db import (
    get_categories, get_subcategories,
    get_services_by_subcategory, get_services_by_category,
    get_payment_methods, get_setting
)

def main_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🛒 Xizmatlarga buyurtma berish")],
        [KeyboardButton(text="💰 Hisob to'ldirish"), KeyboardButton(text="👤 Mening hisobim")],
        [KeyboardButton(text="📋 Buyurtmalarim"), KeyboardButton(text="🎁 Promokod")],
        [KeyboardButton(text="👥 Referal tizimi"), KeyboardButton(text="📞 Murojaat")],
    ], resize_keyboard=True)

def admin_menu_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⚙️ Asosiy sozlamalar")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🎟 Promokod")],
        [KeyboardButton(text="📢 Kanallar"), KeyboardButton(text="🛍 Xizmatlar")],
        [KeyboardButton(text="🔍 Foydalanuvchini boshqarish")],
        [KeyboardButton(text="🔘 Tugmalar"), KeyboardButton(text="📨 Xabarnoma")],
        [KeyboardButton(text="🔄 Botni o'chir/yoq"), KeyboardButton(text="◀️ Orqaga")],
    ], resize_keyboard=True)

async def categories_kb():
    cats = await get_categories()
    per_row = int(await get_setting('categories_per_row') or 2)
    buttons = []
    row = []
    for cat in cats:
        row.append(InlineKeyboardButton(
            text=f"{cat['emoji']} {cat['name']}",
            callback_data=f"cat:{cat['id']}"
        ))
        if len(row) == per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def subcategories_kb(cat_id):
    subs = await get_subcategories(cat_id)
    buttons = []
    for sub in subs:
        buttons.append([InlineKeyboardButton(
            text=f"{sub['emoji']} {sub['name']}",
            callback_data=f"sub:{sub['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back:cats")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def services_kb(parent_id, parent_type):
    if parent_type == 'sub':
        services = await get_services_by_subcategory(parent_id)
    else:
        services = await get_services_by_category(parent_id)
    per_row = int(await get_setting('services_per_row') or 5)
    buttons = []
    row = []
    for i, srv in enumerate(services):
        row.append(InlineKeyboardButton(
            text=str(i + 1),
            callback_data=f"srv:{srv['id']}"
        ))
        if len(row) == per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    back = f"back:cat:{parent_id}" if parent_type == 'sub' else "back:cats"
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data=back)])
    return InlineKeyboardMarkup(inline_keyboard=buttons), services

async def payment_methods_kb():
    methods = await get_payment_methods()
    per_row = int(await get_setting('payment_per_row') or 2)
    buttons = []
    row = []
    for m in methods:
        row.append(InlineKeyboardButton(
            text=f"{m['emoji']} {m['name']}",
            callback_data=f"pay_method:{m['id']}"
        ))
        if len(row) == per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="back:main")])
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_confirm_kb(pay_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"pay_ok:{pay_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"pay_no:{pay_id}"),
    ]])

def admin_settings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✳️ Birlamchi sozlamalar", callback_data="adm:base_settings")],
        [InlineKeyboardButton(text="🗂 Adminlar", callback_data="adm:admins"),
         InlineKeyboardButton(text="💳 Hamyonlar", callback_data="adm:wallets")],
        [InlineKeyboardButton(text="🔑 API sozlash", callback_data="adm:api"),
         InlineKeyboardButton(text="⭐️ Bot dizayni", callback_data="adm:design")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:back")],
    ])

def base_settings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💱 Valyuta", callback_data="adm:currency")],
        [InlineKeyboardButton(text="💎 VIP narxi", callback_data="adm:vip_price")],
        [InlineKeyboardButton(text="🤝 Taklif foizi", callback_data="adm:referral_bonus")],
        [InlineKeyboardButton(text="🔄 O'tkazma narxi", callback_data="adm:transfer_fee")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:settings")],
    ])

def admins_manage_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yangi admin qo'shish", callback_data="adm:add_admin")],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="adm:admin_list"),
         InlineKeyboardButton(text="❌ O'chirish", callback_data="adm:del_admin")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:settings")],
    ])

def wallets_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ To'lov tizimi qo'shish", callback_data="adm:add_wallet")],
        [InlineKeyboardButton(text="📋 Ro'yxat", callback_data="adm:wallet_list")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:settings")],
    ])

def api_settings_kb(has_api):
    btns = []
    if has_api:
        btns.append([InlineKeyboardButton(text="🔄 APIni yangilash", callback_data="adm:set_api")])
        btns.append([InlineKeyboardButton(text="🗑 APIni o'chirish", callback_data="adm:del_api")])
    else:
        btns.append([InlineKeyboardButton(text="🆕 APIni kiritish", callback_data="adm:set_api")])
    btns.append([InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:settings")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def design_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="adm:des:cat:1"),
         InlineKeyboardButton(text="2", callback_data="adm:des:cat:2"),
         InlineKeyboardButton(text="3", callback_data="adm:des:cat:3"),
         InlineKeyboardButton(text="4", callback_data="adm:des:cat:4")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm:settings")],
    ])

def admin_category_actions_kb(cat_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 Ichki bo'limlar", callback_data=f"adm_srv:subs:{cat_id}")],
        [InlineKeyboardButton(text="➕ Xizmat qo'shish", callback_data=f"adm_srv:add_srv:cat:{cat_id}")],
        [InlineKeyboardButton(text="🔄 On/Off", callback_data=f"adm_srv:toggle_cat:{cat_id}"),
         InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_srv:del_cat:{cat_id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data="adm_srv:categories")],
    ])

def admin_subcategory_actions_kb(sub_id, cat_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Xizmat qo'shish", callback_data=f"adm_srv:add_srv:sub:{sub_id}")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm_srv:del_sub:{sub_id}:{cat_id}")],
        [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"adm_srv:subs:{cat_id}")],
    ])

def user_manage_kb(target_id, is_banned, is_vip):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Unban" if is_banned else "🚫 Ban",
            callback_data=f"usr:{'unban' if is_banned else 'ban'}:{target_id}"
         ),
         InlineKeyboardButton(
            text="⭐️ VIP olish" if is_vip else "⭐️ VIP berish",
            callback_data=f"usr:{'unvip' if is_vip else 'vip'}:{target_id}"
         )],
        [InlineKeyboardButton(text="💰 Balans qo'shish", callback_data=f"usr:add_bal:{target_id}")],
    ])

async def subscription_check_kb(channels):
    buttons = []
    for ch in channels:
        link = ch['channel_link'] or f"https://t.me/{ch['channel_id'].lstrip('@')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['channel_name']}", url=link)])
    buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
    ])

def confirm_order_kb(service_id):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm_order:{service_id}"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="cancel"),
    ]])
